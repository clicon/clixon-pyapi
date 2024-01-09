import os
from typing import Optional

from clixon.args import parse_args
from clixon.netconf import (rpc_commit, rpc_config_get, rpc_config_set,
                            rpc_push,
                            rpc_pull,
                            rpc_subscription_create)
from clixon.parser import parse_string
from clixon.args import get_logger
from clixon.sock import read, send, create_socket


sockpath = parse_args("sockpath")
pp = parse_args("pp")
logger = get_logger()
default_sockpath = "/usr/local/var/run/controller.sock"


class Clixon():
    def __init__(self, sockpath: Optional[str] = "",
                 commit: Optional[bool] = False,
                 push: Optional[bool] = False,
                 pull: Optional[bool] = False,
                 source: Optional[str] = "actions",
                 target: Optional[str] = "actions",
                 user: Optional[str] = "root") -> None:
        """
        Create a Clixon object.
        """

        if sockpath == "":
            sockpath = default_sockpath

        if not os.path.exists(sockpath):
            raise ValueError(f"Invalid socket: {sockpath}")

        self.__socket = create_socket(sockpath)
        self.__commit = commit
        self.__push = push
        self.__pull = pull
        self.__logger = logger
        self.__target = target
        self.__source = source
        self.__user = user
        self.__root = None

    def __enter__(self) -> object:
        """
        Return the root object.
        """

        if self.__pull:
            logger.info("Pulling config")

            enable_transaction_notify = rpc_subscription_create(
                "controller-transaction")
            send(self.__socket, enable_transaction_notify, pp)
            read(self.__socket, pp)

            pull = rpc_pull()

            send(self.__socket, pull, pp)
            data = read(self.__socket, pp)

            idx = 0
            while True:
                if "notification" not in data and "SUCCESS" not in data:
                    break

                idx += 1

                if idx > 5:
                    raise ValueError("Push timeout")

                data = read(self.__socket, pp)
                print(data)

        return self

    def __exit__(self, *args: object) -> None:
        """
        Send the final config and commit.
        """
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
                read(self.__socket, pp)

                if self.__commit:
                    self.commit()
        except Exception as e:
            logger.error(f"Got exception from Clixon.__exit__: {e}")
            raise Exception(f"{e}")

    def commit(self) -> None:
        """
        Commit the configuration.
        """
        commit = rpc_commit()

        send(self.__socket, commit, pp)
        read(self.__socket, pp)

        if self.__push:
            logger.info("Pushing config")

            enable_transaction_notify = rpc_subscription_create(
                "controller-transaction")
            send(self.__socket, enable_transaction_notify, pp)
            read(self.__socket, pp)

            logger.debug("Pushing commit")
            push = rpc_push()

            send(self.__socket, push, pp)

            data = read(self.__socket, pp)

            idx = 0
            while True:
                if "notification" not in data and "SUCCESS" not in data:
                    break

                idx += 1

                if idx > 5:
                    raise ValueError("Push timeout")

                data = read(self.__socket, pp)

    def get_root(self) -> object:
        """
        Return the root object.
        """
        logger.debug("Updating root object")

        send(self.__socket, rpc_config_get(
            user=self.__user, source=self.__source), pp)
        data = read(self.__socket, pp)

        self.__root = parse_string(data).rpc_reply.data

        return self.__root

    def set_root(self, root: object) -> None:
        """
        Set the root object.
        """
        send(self.__socket, root, pp)
        read(self.__socket, pp)

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
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            with Clixon(sockpath, commit=commit) as root:
                return func(root, logger, **kwargs)
        return wrapper
    return decorator
