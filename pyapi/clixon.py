import os
from pyapi.client import send, create_socket
from pyapi.log import get_logger
from pyapi.args import parse_args
from pyapi.netconf import rpc_config_get, rpc_config_set, rpc_commit

logger = get_logger()
sockpath, _, _, _ = parse_args()


class Clixon():
    def __init__(self, sockpath="/usr/local/var/controller.sock"):
        if sockpath == "" or not os.path.exists(sockpath):
            raise ValueError(f"Invalid socket: {sockpath}")

        self.__socket = create_socket(sockpath)
        self.__root = rpc_config_get()

    def __enter__(self):
        return self.__root

    def __exit__(self, *args):
        config = rpc_config_set(self.__root)
        send(self.__socket, config.dumps())
        commit = rpc_commit()
        send(self.__socket, commit)

    def get_root(self):
        return self.__root

    def set_root(self, root):
        send(self.__socket, root.dumps())
        commit = rpc_commit()
        send(self.__socket, commit)


def rpc():
    def decorator(func):
        def wrapper(*args, **kwargs):
            with Clixon(sockpath) as root:
                return func(root, logger)
        return wrapper
    return decorator
