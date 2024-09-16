import os
from typing import Optional

from clixon.args import get_arg, get_logger
from clixon.netconf import (
    rpc_commit,
    rpc_config_get,
    rpc_config_set,
    rpc_error_get,
    rpc_pull,
    rpc_push,
    rpc_subscription_create,
    rpc_apply_service,
    rpc_datastore_diff,
    rpc_lock,
    rpc_unlock,
)
from clixon.parser import parse_string
from clixon.sock import create_socket, read, send
from clixon.helpers import timeout


sockpath = get_arg("sockpath")
pp = get_arg("pp")
logger = get_logger()
default_sockpath = "/usr/local/var/run/controller.sock"


class Clixon:
    def __init__(
        self,
        sockpath: Optional[str] = "",
        commit: Optional[bool] = False,
        push: Optional[bool] = False,
        pull: Optional[bool] = False,
        source: Optional[str] = "actions",
        target: Optional[str] = "actions",
        cron: Optional[bool] = False,
        read_only: Optional[bool] = False,
        user: Optional[str] = "root",
        standalone: Optional[bool] = False,
    ) -> None:
        """
        Create a Clixon object.

        :param sockpath: Path to the socket
        :type sockpath: str
        :param commit: Commit the configuration
        :type commit: bool
        :param push: Push the configuration
        :type push: bool
        :param pull: Pull the configuration
        :type pull: bool
        :param source: Source of the configuration
        :type source: str
        :param target: Target of the configuration
        :type target: str
        :param cron: Run in cron mode
        :type cron: bool
        :param user: User to run as
        :type user: str
        :return: None
        :rtype: None
        """

        if sockpath == "":
            sockpath = default_sockpath

        if not os.path.exists(sockpath):
            raise ValueError(f"Invalid socket: {sockpath}")

        self.__commit = commit
        self.__logger = logger
        self.__pull = pull
        self.__push = push
        self.__root = None
        self.__socket = create_socket(sockpath)
        self.__source = source
        self.__target = target
        self.__user = user
        self.__read_only = read_only
        self.__transaction_notify = False
        self.__standalone = standalone

        if cron:
            self.__commit = True
            self.__pull = True
            self.__push = True
            self.__source = "running"
            self.__standalone = True
            self.__target = "candidate"

    def __enter__(self) -> object:
        """
        Return the root object.

        :return: Root object
        :rtype: object

        """

        if self.__pull:
            self.pull()

        return self

    def __exit__(self, *args: object) -> None:
        """
        Send the final config and commit.

        :param args: Arguments
        :type args: object
        :return: None
        :rtype: None

        """
        if self.__read_only:
            logger.info("Read only mode enabled")
            return

        try:
            if self.__root is None:
                self.__root = self.get_root()

            for child in self.__root:
                config = rpc_config_set(child, target=self.__target)
                send(self.__socket, config, pp)
                data = read(self.__socket, pp)

                self.__handle_errors(data)

            if self.__commit:
                self.commit()

        except Exception as e:
            logger.error(f"Got exception from Clixon.__exit__: {e}")
            raise Exception(f"{e}")

    def commit(self) -> None:
        """
        Commit the configuration.

        :return: None
        :rtype: None

        """

        if self.__read_only:
            logger.info("Read only mode enabled")
            return

        commit = rpc_commit()

        send(self.__socket, commit, pp)
        data = read(self.__socket, pp)

        self.__handle_errors(data)

        if self.__push:
            self.push()

    def get_root(self) -> object:
        """
        Return the root object.

        :return: Root object
        :rtype: object

        """
        logger.debug("Updating root object")

        config = rpc_config_get(user=self.__user, source=self.__source)

        send(self.__socket, config, pp)
        data = read(self.__socket, pp)

        self.__handle_errors(data)
        self.__root = parse_string(data).rpc_reply.data

        return self.__root

    @timeout(30)
    def __wait_for_notification(self) -> None:
        """
        Wait for the pull/push notification.

        :return: None
        :rtype: None

        """

        data = read(self.__socket, pp, standalone=self.__standalone)

        self.__handle_errors(data)

        idx = 0
        while True:
            logger.debug(f"Waiting for notification {idx} of 5")

            if "notification" in data and "SUCCESS" in data:
                break

            idx += 1

            if idx > 5:
                raise ValueError("Read too many messages without notification success")

            data = read(self.__socket, pp, standalone=self.__standalone)

            self.__handle_errors(data)

    def __handle_errors(self, data: str) -> None:
        """
        Handle errors.

        :param data: Data
        :type data: str
        :return: None
        :rtype: None

        """

        rpc_error_get(data, standalone=self.__standalone)

    def __strip_rpc_reply(self, data: str) -> str:
        """
        Strip the rpc-reply tags and make the output readable.

        :param data: Data
        :type data: str
        :return: Stripped data
        :rtype: str
        """

        # Remove the rpc-reply tag and make the output more readable
        data = data.replace("&lt;", "<").replace("&gt;", ">")
        data = data.replace('<diff xmlns="http://clicon.org/controller">', "")
        data = data.replace("</diff>", "")
        data = data.replace(
            """<rpc-reply xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">""", ""
        )
        data = data.replace("</rpc-reply>", "")

        return data

    def __enable_transaction_notify(self) -> None:
        """
        Enable transaction notifications.

        :return: None
        :rtype: None
        """

        enable_transaction_notify = rpc_subscription_create("controller-transaction")

        send(self.__socket, enable_transaction_notify, pp)
        data = read(self.__socket, pp, standalone=self.__standalone)

        self.__handle_errors(data)
        self.__transaction_notify = True

    def pull(
        self, device: Optional[bool] = "*", transient: Optional[bool] = False
    ) -> None:
        """
        Send a pull request.

        :return: None
        :rtype: None

        """

        logger.info(f"Pulling config for device {device}")

        if not self.__transaction_notify:
            self.__enable_transaction_notify()

        pull = rpc_pull(transient=transient, device=device)
        send(self.__socket, pull, pp)

        self.__wait_for_notification()

    def push(self) -> None:
        """
        Send a push request.

        :return: None
        :rtype: None

        """

        logger.info("Pushing config")

        if self.__read_only:
            logger.info("Read only mode enabled")
            return

        if not self.__transaction_notify:
            self.__enable_transaction_notify()

        logger.debug("Pushing commit")
        push = rpc_push()

        send(self.__socket, push, pp)

        self.__wait_for_notification()

    def set_root(self, root: object) -> None:
        """
        Set the root object.

        :param root: Root object
        :type root: object
        :return: None
        :rtype: None

        """

        if self.__read_only:
            logger.info("Read only mode enabled")
            return

        config = rpc_config_set(root, device=False, target=self.__target)

        send(self.__socket, config, pp)
        data = read(self.__socket, pp)
        self.__handle_errors(data)

        if self.__commit:
            self.commit()

    def get_logger(self) -> object:
        """
        Return the logger object.

        :return: Logger object
        :rtype: object

        """
        return self.__logger

    def apply_service(
        self, service: str, instance: str, diff: Optional[bool] = True
    ) -> str:
        """
        Apply a service.

        :param service: Service name
        :type service: str
        :param instance: Instance name
        :type instance: str
        :param diff: Diff
        :type diff: bool
        :return: None
        :rtype: None

        """

        if self.__read_only and not diff:
            raise ValueError("Apply: Read only mode enabled, can only apply diff")

        if not self.__transaction_notify:
            self.__enable_transaction_notify()

        rpc_apply = rpc_apply_service(service, instance, diff)
        send(self.__socket, rpc_apply, pp)

        self.__wait_for_notification()

        rpc_diff = rpc_datastore_diff()
        send(self.__socket, rpc_diff, pp)
        data = read(self.__socket, pp, standalone=self.__standalone)

        self.__handle_errors(data)

        data = self.__strip_rpc_reply(data)

        return data

    def show_compare(self, set_root: Optional[bool] = False) -> str:
        """
        Show the compare.

        :return: Compare
        :rtype: str

        """

        if set_root:
            self.set_root(self.__root)

        rpc_show_compare = rpc_datastore_diff(compare=True)
        send(self.__socket, rpc_show_compare, pp)
        data = read(self.__socket, pp, standalone=self.__standalone)

        self.__handle_errors(data)
        data = self.__strip_rpc_reply(data)

        return data

    def show_devices_diff(self, dict_format: Optional[bool] = False) -> str:
        """
        Show the devices diff.

        :return: Devices diff
        :rtype: str

        """

        self.pull(transient=True)

        rpc_show_devices_diff = rpc_datastore_diff(transient=True)

        send(self.__socket, rpc_show_devices_diff, pp)
        data = read(self.__socket, pp, standalone=self.__standalone)

        self.__handle_errors(data)

        data = self.__strip_rpc_reply(data)

        if not data:
            if dict_format:
                return dict()
            return None

        if dict_format:
            # Create a dict structure where crpd1 and crpd2 are the keys
            # and the diff is the value
            # crpd1:
            #       <system xmlns="http://yang.juniper.net/junos/conf/root">
            # -       <host-name>foobar</host-name>
            # +       <host-name>TW6A3ZM3</host-name>
            #       </system>
            # crpd2:
            #       <system xmlns="http://yang.juniper.net/junos/conf/root">
            # -       <host-name>kalas</host-name>
            # +       <host-name>crpd2</host-name>
            #       </system>
            diff = dict()

            for line in data.split("\n"):
                if line.endswith(":") and "<" not in line and ">" not in line:
                    key = line[:-1]
                else:
                    if key not in diff:
                        diff[key] = ""
                    diff[key] += line + "\n"

            return diff

        return data

    def lock(self, target: Optional[str] = "candidate") -> None:
        """
        Lock the configuration.

        :param target: Target
        :type target: str
        :return: None
        :rtype: None

        """

        logger.info(f"Locking configuration for target {target}")

        rpc = rpc_lock(target)
        send(self.__socket, rpc, pp)
        data = read(self.__socket, pp)

        self.__handle_errors(data)

    def unlock(self, target: Optional[str] = "candidate") -> None:
        """
        Unlock the configuration.

        :param target: Target
        :type target: str
        :return: None
        :rtype: None

        """

        logger.info(f"Unlocking configuration for target {target}")

        rpc = rpc_unlock(target)
        send(self.__socket, rpc, pp)
        data = read(self.__socket, pp)

        self.__handle_errors(data)


def rpc(sockpath: Optional[str] = sockpath, commit: Optional[bool] = False) -> object:
    """
    Decorator to create a Clixon object.

    :param sockpath: Path to the socket
    :type sockpath: str
    :param commit: Commit the configuration
    :type commit: bool
    :return: Clixon object
    :rtype: object

    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            with Clixon(sockpath, commit=commit) as root:
                return func(root, logger, **kwargs)

        return wrapper

    return decorator
