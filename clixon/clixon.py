import os
from typing import Optional

from clixon.args import get_arg, get_logger
from clixon.sock import read, send, create_socket
from clixon.parser import parse_string
from clixon.netconf import (
    rpc_commit,
    rpc_config_get,
    rpc_config_set,
    rpc_push,
    rpc_pull,
    rpc_subscription_create,
    rpc_error_get
)
from clixon.helpers import get_tree_diffs

sockpath = get_arg("sockpath")
pp = get_arg("pp")
logger = get_logger()
default_sockpath = "/usr/local/var/run/controller.sock"


class Clixon():
    def __init__(self, sockpath: Optional[str] = "",
                 commit: Optional[bool] = False,
                 push: Optional[bool] = False,
                 pull: Optional[bool] = False,
                 source: Optional[str] = "actions",
                 target: Optional[str] = "actions",
                 cron: Optional[bool] = False,
                 user: Optional[str] = "root") -> None:
        """
        Create a Clixon object.
        :param sockpath: Path to the socket
        :param commit: Commit the configuration
        :param push: Push the configuration
        :param pull: Pull the configuration
        :param source: Source of the configuration
        :param target: Target of the configuration
        :param cron: Run in cron mode
        :param user: User to run as
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
        self.__standalone = False

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
        """

        if self.__pull:
            self.pull()

        return self

    def __exit__(self, *args: object) -> None:
        """
        Send the final config and commit.
        :param args: Arguments
        :return: None
        """

        diff = get_tree_diffs(self.__old_root, self.__root)

        if not diff:
            logger.info("No changes detected")
            return

        try:
            if self.__root is None:
                self.__root = self.get_root()

            for device in self.__root.devices.get_elements():
                if device.get_name() != "device":
                    continue

                logger.debug(
                    f"Configure {device.name} with target {self.__target}")

                config = rpc_config_set(
                    device, device=True,
                    target=self.__target
                )

                send(self.__socket, config, pp)
                data = read(self.__socket, pp, standalone=self.__standalone)

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
        """
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
        """
        logger.debug("Updating root object")

        config = rpc_config_get(
            user=self.__user,
            source=self.__source
        )

        send(self.__socket, config, pp)
        data = read(self.__socket, pp)

        self.__handle_errors(data)
        self.__root = parse_string(data).rpc_reply.data
        self.__old_root = parse_string(data).rpc_reply.data

        return self.__root

    def __wait_for_pull_push_notification(self) -> None:
        """
        Wait for the pull/push notification.
        :return: None
        """

        data = read(self.__socket, pp, standalone=self.__standalone)

        rpc_error_get(data, standalone=self.__standalone)

        idx = 0
        while True:
            if "notification" in data and "SUCCESS" in data:
                break

            idx += 1

            if idx > 5:
                raise ValueError("Push timeout")

            data = read(self.__socket, pp, standalone=self.__standalone)

            self.__handle_errors(data)

    def __handle_errors(self, data: str) -> None:
        """
        Handle errors.
        :param data: Data
        :return: None
        """

        rpc_error_get(data, standalone=self.__standalone)

    def pull(self) -> None:
        """
        Send a pull request.
        :return: None
        """

        logger.info("Pulling config")

        enable_transaction_notify = rpc_subscription_create(
            "controller-transaction")
        send(self.__socket, enable_transaction_notify, pp)
        data = read(self.__socket, pp, standalone=self.__standalone)

        self.__handle_errors(data)

        pull = rpc_pull()
        send(self.__socket, pull, pp)

        self.__wait_for_pull_push_notification()

    def push(self) -> None:
        """
        Send a push request.
        :return: None
        """

        logger.info("Pushing config")

        enable_transaction_notify = rpc_subscription_create(
            "controller-transaction")
        send(self.__socket, enable_transaction_notify, pp)
        data = read(self.__socket, pp, standalone=self.__standalone)

        self.__handle_errors(data)

        logger.debug("Pushing commit")
        push = rpc_push()

        send(self.__socket, push, pp)

        self.__wait_for_pull_push_notification()

    def set_root(self, root: object) -> None:
        """
        Set the root object.
        :param root: Root object
        :return: None
        """

        send(self.__socket, root, pp)
        data = read(self.__socket, pp)
        self.__handle_errors(data)

        if self.__commit:
            self.commit()

    def get_logger(self) -> object:
        """
        Return the logger object.
        """
        return self.__logger


def rpc(sockpath: Optional[str] = sockpath,
        commit: Optional[bool] = False) -> object:
    """
    Decorator to create a Clixon object.
    :param sockpath: Path to the socket
    :param commit: Commit the configuration
    :return: Clixon object
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            with Clixon(sockpath, commit=commit) as root:
                return func(root, logger, **kwargs)
        return wrapper
    return decorator
