import getpass
import os
import re
import socket
from time import monotonic
from typing import Optional
from xml.sax.saxutils import unescape

from clixon.args import get_arg, get_logger
from clixon.exceptions import TransactionError
from clixon.helpers import get_path
from clixon.netconf import (
    rpc_apply_template,
    rpc_apply_service,
    rpc_close_session,
    rpc_commit,
    rpc_config_get,
    rpc_config_set,
    rpc_connection_open,
    rpc_controller_commit,
    rpc_datastore_diff,
    rpc_error_get,
    rpc_lock,
    rpc_pull,
    rpc_push,
    rpc_subscription_create,
    rpc_unlock,
    rpc_transactions_get,
    rpc_devices_get,
    rpc_schema_get,
    rpc_schemas_get,
    rpc_device_rpc_result,
    rpc_discard_changes,
)
from clixon.parser import parse_string
from clixon.sock import create_socket, read, send

sockpath = get_arg("sockpath")
pp = get_arg("pp")
logger = get_logger()
default_sockpath = "/usr/local/var/run/controller/controller.sock"


class Clixon:
    def __init__(
        self,
        sockpath: Optional[str] = "",
        socket: Optional[socket.socket] = None,
        commit: Optional[bool] = False,
        push: Optional[bool] = False,
        pull: Optional[bool] = False,
        source: Optional[str] = "actions",
        target: Optional[str] = "actions",
        cron: Optional[bool] = False,
        read_only: Optional[bool] = False,
        user: Optional[str] = None,
        standalone: Optional[bool] = False,
        timeout: Optional[int] = 30,
        from_server: Optional[bool] = False,
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

        if not user:
            user = getpass.getuser()

        if sockpath == "" and socket is None:
            sockpath = default_sockpath

            if not os.path.exists(sockpath):
                raise ValueError(f"Invalid socket: {sockpath}")

        self.__commit = commit
        self.__logger = logger
        self.__pull = pull
        self.__push = push
        self.__root = None

        if not socket:
            self.__socket = create_socket(sockpath)
            self.__server_socket = False
        else:
            self.__socket = socket
            self.__server_socket = True

        self.__source = source
        self.__target = target
        self.__user = user
        self.__read_only = read_only
        self.__transaction_notify = False
        self.__standalone = standalone
        self.__timeout = timeout

        if cron:
            self.__commit = True
            self.__pull = True
            self.__push = True
            self.__source = "running"
            self.__standalone = True
            self.__target = "candidate"

        self.__from_server = from_server

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
            logger.info("Read only mode enabled, skipping config set")
        else:
            try:
                if self.__root is None:
                    self.__root = self.get_root()

                for child in self.__root:
                    config = rpc_config_set(
                        child, user=self.__user, target=self.__target
                    )
                    send(self.__socket, config, pp)
                    data = read(self.__socket, pp)

                    self.__handle_errors(data)

                if self.__commit:
                    self.commit()

            except Exception as e:
                logger.error(f"Got exception from Clixon.__exit__: {e}")
                raise Exception(f"{e}")

        if not self.__from_server:
            try:
                self.close_session()
            except Exception:
                pass

    def commit(self) -> None:
        """
        Commit the configuration.

        :return: None
        :rtype: None

        """

        if self.__read_only:
            logger.info("Read only mode enabled")
            return

        commit = rpc_commit(user=self.__user)

        send(self.__socket, commit, pp)
        data = read(self.__socket, pp)

        self.__handle_errors(data)

        if self.__push:
            self.push()

    def commit_services(
        self, push: Optional[bool] = None, device: Optional[str] = "*"
    ) -> None:
        """
        Commit the candidate datastore the way the controller does it: run the
        services which have changed, commit and push the result to the
        devices, all in one transaction.

        Clixon.commit is a plain NETCONF commit, which the controller commits
        locally without running any service, and a push after such a commit
        has nothing to send, the devices never got any configuration.

        Note that the services are only run in a transaction which may push:
        with push disabled the controller reports what the services would
        change without committing anything, which is the commit diff of the
        controller CLI.

        :param push: Push to the devices, the push of the object if not given
        :type push: bool
        :param device: Device name, or * for all of them
        :type device: str
        :return: None
        :rtype: None

        """

        if self.__read_only:
            logger.info("Read only mode enabled")
            return

        if push is None:
            push = self.__push

        if not self.__transaction_notify:
            self.__enable_transaction_notify()

        rpc = rpc_controller_commit(
            device=device,
            source="candidate",
            actions="CHANGE",
            push="COMMIT" if push else "NONE",
            user=self.__user,
        )

        send(self.__socket, rpc, pp)

        self.__wait_for_notification()

    def close_session(self) -> None:
        """
        Send a close-session RPC to gracefully terminate the NETCONF session.

        :return: None
        :rtype: None

        """

        close = rpc_close_session(user=self.__user)
        send(self.__socket, close, pp)

        # After sending close-session, the server should close the connection.
        # We attempt to read to confirm this, expecting an error or no data.
        data = read(self.__socket, pp)

        if "<ok/>" not in data:
            raise ValueError("Unexpected response after close-session")

    def get_root(
        self,
        path: Optional[str] = None,
        xpath: Optional[str] = "/",
        namespaces: Optional[dict] = None,
    ) -> object:
        """
        Return the root object or a specific element, with optional server-side filtering.

        Examples:
            root = clixon.get_root()  # Returns entire root
            device = clixon.get_root(path="devices/device[0]")  # Returns first device (client-side navigation)
            config = clixon.get_root(path="devices/device[name='r1']/config")  # Returns config for device 'r1'
            services = clixon.get_root(xpath="/services")  # Returns only services subtree (server-side filter)
            l2c = clixon.get_root(xpath="/services/l2c:l2c", namespaces={"l2c": "http://example.com/l2c"})  # Filtered with namespace

        :param path: Optional path to a specific element (e.g., "devices/device[0]"). Applied client-side after retrieval.
        :type path: Optional[str]
        :param xpath: XPath expression to filter the config server-side (default '/')
        :type xpath: Optional[str]
        :param namespaces: Dict of namespace prefixes to URIs for xpath (optional)
        :type namespaces: Optional[dict]
        :return: Root object (if path is None) or element at path (if path is provided). Returns None if path is invalid.
        :rtype: object

        """
        logger.debug("Updating root object")

        config = rpc_config_get(
            user=self.__user, source=self.__source, xpath=xpath, namespaces=namespaces
        )

        send(self.__socket, config, pp)
        data = read(self.__socket, pp)

        self.__handle_errors(data)
        self.__root = parse_string(data).rpc_reply.data

        if path:
            return get_path(self.__root, path)

        return self.__root

    def __wait_for_notification(self, return_data: Optional[bool] = False) -> None:
        """
        Wait for the pull/push notification.

        :return: None
        :rtype: None

        """

        # The deadline is watched by the socket rather than by an alarm
        # signal, signals only work in the main thread and the Clixon object
        # is also used from threaded servers.
        deadline = monotonic() + self.__timeout

        def __wait_or_timeout() -> str:
            data = read(
                self.__socket,
                pp,
                standalone=self.__standalone,
                timeout=deadline - monotonic(),
            )

            self.__handle_errors(data)

            idx = 0
            while True:
                logger.debug(f"Waiting for notification {idx} of 5")

                self.__handle_errors(data)

                if "notification" in data and "SUCCESS" in data:
                    self.__handle_errors(data)

                    return data
                elif "notification" in data and "FAILED" in data:
                    raise TransactionError("Transaction failed")

                idx += 1

                if idx > 5:
                    raise ValueError(
                        "Read too many messages without notification success"
                    )

                data = read(
                    self.__socket,
                    pp,
                    standalone=self.__standalone,
                    timeout=deadline - monotonic(),
                )

        data = __wait_or_timeout()

        if return_data:
            return data

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

        enable_transaction_notify = rpc_subscription_create(
            "controller-transaction", user=self.__user
        )

        send(self.__socket, enable_transaction_notify, pp)
        data = read(self.__socket, pp, standalone=self.__standalone)

        self.__handle_errors(data)
        self.__transaction_notify = True

    def __set_timeout(self, timeout: int) -> None:
        """
        Set the timeout.
        """

        self.__timeout = timeout

    def pull(
        self, device: Optional[bool] = "*", transient: Optional[bool] = False
    ) -> None:
        """
        Send a pull request.

        :return: None
        :rtype: None

        """

        logger.debug(f"Pulling config for device {device}")

        if not self.__transaction_notify:
            self.__enable_transaction_notify()

        pull = rpc_pull(transient=transient, device=device, user=self.__user)
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
        push = rpc_push(user=self.__user)

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

        config = rpc_config_set(
            root, user=self.__user, device=False, target=self.__target
        )

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

    def device_rpc(
        self,
        devname: Optional[str] = None,
        template: Optional[str] = "",
        variables: Optional[dict] = {},
        inline: Optional[bool] = False,
        groupname: Optional[str] = None,
    ) -> list | object:
        """
        Apply a RPC template to a device or device-group.

        :param devname: Device name (mutually exclusive with groupname)
        :type devname: str
        :param template: Template name or inline template string
        :type template: str
        :param variables: Template variables
        :type variables: dict
        :param inline: Use inline template
        :type inline: bool
        :param groupname: Device-group name (mutually exclusive with devname)
        :type groupname: str
        :return: devices element
        :rtype: object
        """

        if devname is None and groupname is None:
            raise ValueError("Either devname or groupname must be provided")
        if devname is not None and groupname is not None:
            raise ValueError("devname and groupname are mutually exclusive")

        rpc = rpc_apply_template(
            devname,
            template,
            variables,
            user=self.__user,
            inline=inline,
            groupname=groupname,
        )

        if not self.__transaction_notify:
            self.__enable_transaction_notify()

        send(self.__socket, rpc, pp)

        data = self.__wait_for_notification(return_data=True)

        transaction = parse_string(data)

        try:
            if transaction.notification.controller_transaction.result != "SUCCESS":
                raise ValueError("Device RPC failed")

            tid = transaction.notification.controller_transaction.tid.get_data()
            rpc = rpc_device_rpc_result(tid=tid, user=self.__user)
            send(self.__socket, rpc, pp)
            data = read(self.__socket, pp)

            return parse_string(data).rpc_reply.devices

        except AttributeError:
            raise ValueError("Device RPC failed")

    def apply_template(
        self,
        devname: Optional[str] = None,
        template: Optional[str] = "",
        variables: Optional[dict] = {},
        inline: Optional[bool] = False,
        groupname: Optional[str] = None,
    ) -> None:
        """
        Apply a template.

        :param devname: Device name (mutually exclusive with groupname)
        :type devname: str
        :param template: Template name or inline template string
        :type template: str
        :param variables: Template variables
        :type variables: dict
        :param inline: Use inline template
        :type inline: bool
        :param groupname: Device-group name (mutually exclusive with devname)
        :type groupname: str
        :return: None
        :rtype: None
        """

        if devname is None and groupname is None:
            raise ValueError("Either devname or groupname must be provided")
        if devname is not None and groupname is not None:
            raise ValueError("devname and groupname are mutually exclusive")

        if self.__read_only:
            logger.info("Read only mode enabled")
            return

        rpc = rpc_apply_template(
            devname,
            template,
            variables,
            template_type="CONFIG",
            user=self.__user,
            inline=inline,
            groupname=groupname,
        )

        if not self.__transaction_notify:
            self.__enable_transaction_notify()

        send(self.__socket, rpc, pp)

        data = read(self.__socket, pp, standalone=self.__standalone)

        if "<ok/>" not in data:
            raise ValueError("Apply template failed")

        return True

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

        rpc_apply = rpc_apply_service(service, instance, diff, user=self.__user)
        send(self.__socket, rpc_apply, pp)

        self.__wait_for_notification()

        rpc_diff = rpc_datastore_diff(user=self.__user)
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

        rpc_show_compare = rpc_datastore_diff(compare=True, user=self.__user)
        send(self.__socket, rpc_show_compare, pp)
        data = read(self.__socket, pp, standalone=self.__standalone)

        self.__handle_errors(data)
        data = self.__strip_rpc_reply(data)

        return data

    def show_devices_diff(
        self, device: Optional[str] = "*", dict_format: Optional[bool] = False
    ) -> str:
        """
        Show the devices diff.

        :return: Devices diff
        :rtype: str

        """

        self.pull(device=device, transient=True)

        rpc_show_devices_diff = rpc_datastore_diff(
            device=device, transient=True, user=self.__user
        )

        send(self.__socket, rpc_show_devices_diff, pp)
        data = read(self.__socket, pp, standalone=self.__standalone)

        # If we get a tid, we need to read again to skip it. Since messages are sent asyncronously
        # the notification status message might arrive before the transaction ID message.
        if re.search(r'<tid xmlns="http://clicon.org/controller">(\d+)</tid>', data):
            data = read(self.__socket, pp, standalone=self.__standalone)

        self.__handle_errors(data)

        data = self.__strip_rpc_reply(data)

        if not data:
            if dict_format:
                return {}
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
            diff = {}
            key = None

            for line in data.split("\n"):
                if line.endswith(":") and "<" not in line and ">" not in line:
                    key = line[:-1]
                else:
                    if not key:
                        continue
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

        rpc = rpc_lock(target, user=self.__user)
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

        rpc = rpc_unlock(target, user=self.__user)
        send(self.__socket, rpc, pp)
        data = read(self.__socket, pp)

        self.__handle_errors(data)

    def connection_open(self, devname: Optional[str] = "*") -> None:
        """
        Open a connection.

        :param devname: Device name
        :type devname: str
        :return: None
        :rtype: None

        """

        if not self.__transaction_notify:
            self.__enable_transaction_notify()

        rpc = rpc_connection_open(devname)
        send(self.__socket, rpc, pp)

        try:
            self.__wait_for_notification()

            # The reply of the connection change follows the notification, but
            # only if there is anything to connect to, so it is waited for with
            # a timeout rather than forever.
            data = read(
                self.__socket,
                pp,
                standalone=self.__standalone,
                timeout=self.__timeout,
            )
        except Exception as e:
            logger.error(f"Failed to open connection to {devname}: {e}")
            return None

        self.__handle_errors(data)
        data = self.__strip_rpc_reply(data)

        return data

    def rollback(self) -> None:
        """
        Rollback / discard candidate.

        :param target: Target
        :type target: str
        :return: None
        :rtype: None

        """

        logger.info("Rollback, discard_changes")

        rpc = rpc_discard_changes(user=self.__user)
        send(self.__socket, rpc, pp)
        data = read(self.__socket, pp)

        self.__handle_errors(data)

    def get_service_yang(
        self,
        service: str,
        revision: Optional[str] = None,
        format: Optional[str] = "yang",
    ) -> str:
        """
        Fetch the YANG definition of a service module from the backend.

        The service YANG modules are the modules augmenting /ctrl:services,
        they are fetched using the NETCONF get-schema RPC (RFC 6022).

        Example:
            yang = clixon.get_service_yang("myservice")

        :param service: Name of the service YANG module
        :type service: str
        :param revision: Revision of the YANG module, latest if not given
        :type revision: str
        :param format: Schema format, yang or yin
        :type format: str
        :return: YANG definition of the service module
        :rtype: str

        """

        logger.debug(f"Fetching YANG for service {service}")

        rpc = rpc_schema_get(service, version=revision, format=format, user=self.__user)

        send(self.__socket, rpc, pp)
        data = read(self.__socket, pp, standalone=self.__standalone)

        # The error handling matches on the text of the reply, and a YANG
        # module may very well contain words such as error-message, so the
        # reply is only checked when it is an actual error.
        if "<rpc-error" in data:
            self.__handle_errors(data)

        # The YANG definition is returned as text inside the data element. The
        # XML parser mangles both the escaping and the indentation, hence the
        # raw string is used here.
        match = re.search(r"<data[^>]*>(.*)</data>", data, re.DOTALL)

        if not match:
            raise ValueError(f"No YANG returned for service {service}")

        yang = match.group(1)

        # The backend wraps the YANG in CDATA if
        # CLICON_NETCONF_MONITORING_GETSCHEMA_CDATA is enabled.
        cdata = re.match(r"\s*<!\[CDATA\[(.*)\]\]>\s*$", yang, re.DOTALL)

        if cdata:
            return cdata.group(1)

        return unescape(yang, {"&quot;": '"', "&apos;": "'"})

    def get_schemas(self) -> list:
        """
        Return the YANG schemas the backend serves, RFC 6022
        netconf-state/schemas.

        Example:
            schemas = clixon.get_schemas()
            [{"identifier": "ssh-users", "version": "2023-05-22",
              "format": "yang", "namespace": "http://clicon.org/ssh-users",
              "location": "NETCONF"}, ...]

        :return: List of dicts describing the schemas
        :rtype: list

        """

        rpc = rpc_schemas_get(user=self.__user)

        send(self.__socket, rpc, pp)
        data = read(self.__socket, pp, standalone=self.__standalone)

        self.__handle_errors(data)

        schemas = []

        for schema in parse_string(data).get_elements("schema", recursive=True):
            entry = {}

            for child in schema.get_elements():
                entry[child.origname()] = child.get_data()

            schemas.append(entry)

        return schemas

    def show_transactions(self, tid: Optional[int] = None) -> str:
        rpc = rpc_transactions_get(tid=tid, user=self.__user)

        send(self.__socket, rpc, pp)

        data = read(self.__socket, pp)

        return data

    def show_devices(self) -> str:
        """
        Get device names, connection states, timestamps, and log messages.
        """
        rpc = rpc_devices_get(user=self.__user)
        send(self.__socket, rpc, pp)
        data = read(self.__socket, pp)
        return data


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
