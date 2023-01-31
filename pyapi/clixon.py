import os
from enum import Enum
from pyapi.parser import Element, parse_string
from pyapi.client import read, send, create_socket
from pyapi.log import get_logger

logger = get_logger()


class RPCTypes(Enum):
    GET_CONFIG = 0
    EDIT_CONFIG = 1
    COMMIT = 2


def rpc_config_get(socket, user="root"):
    attributes = {
        "nc:type": "xpath",
        "nc:select": "/"
    }

    root = get_rpc_header(RPCTypes.GET_CONFIG, user)
    root.rpc.get_config.add_element("source")
    root.rpc.get_config.source.add_element("candidate")
    root.rpc.get_config.add_element(
        "nc_filter", origname="nc:filter", attributes=attributes)

    send(socket, root.dumps())
    data = read(socket)
    root = parse_string(data.rstrip())

    return root.rpc_reply.data


def rpc_config_set(config, socket, user="root"):
    root = get_rpc_header(RPCTypes.EDIT_CONFIG, user)
    root.rpc.edit_config.add_element("target")
    root.rpc.edit_config.target.add_element("candidate")
    root.rpc.edit_config.add_element(
        "default_operation", origname="default-operation")
    root.rpc.edit_config.default_operation.set_cdata("replace")
    root.rpc.edit_config.add_element("config")

    for node in config.get_elements():
        root.rpc.edit_config.config.add_child(node)

    return root


def rpc_commit(socket, user="root"):
    root = get_rpc_header(RPCTypes.COMMIT, user)

    send(socket, root.dumps())
    data = read(socket)
    root = parse_string(data)

    return root.rpc_reply


def get_rpc_header(rpc_type, user, attributes=None):
    if attributes is None:
        attributes = {
            "xmlns": "urn:ietf:params:xml:ns:netconf:base:1.0",
            "username": user,
            "xmlns:nc": "urn:ietf:params:xml:ns:netconf:base:1.0",
            "message-id": 42
        }

    root = Element("root", {})
    root.add_element("rpc", attributes=attributes)

    if rpc_type == RPCTypes.GET_CONFIG:
        root.rpc.add_element("get_config", origname="get-config")
    elif rpc_type == RPCTypes.EDIT_CONFIG:
        root.rpc.add_element("edit_config", origname="edit-config")
    elif rpc_type == RPCTypes.COMMIT:
        root.rpc.add_element("commit")

    return root


def rpc_subscription_create():
    attributes = {
        "xmlns": "urn:ietf:params:xml:ns:netmod:notification"
    }

    rpcattrs = {
        "xmlns": "urn:ietf:params:xml:ns:netconf:base:1.0",
        "message-id": "42"
    }

    root = get_rpc_header("", "root", rpcattrs)
    root.rpc.add_element("create_subscription",
                         origname="create-subscription", attributes=attributes)
    root.rpc.create_subscription.add_element("stream")
    root.rpc.create_subscription.stream.set_cdata("controller")
    root.rpc.create_subscription.add_element(
        "filter", {"type": "xpath", "select": ""})

    return root


class Clixon():
    def __init__(self, sockpath="/usr/local/var/controller.sock"):
        if sockpath == "" or not os.path.exists(sockpath):
            raise ValueError(f"Invalid socket: {sockpath}")

        self.__socket = create_socket(sockpath)
        self.__root = rpc_config_get(self.__socket)

    def __enter__(self):
        return self.__root

    def __exit__(self, *args):
        config = rpc_config_set(self.__root, self.__socket)
        send(self.__socket, config.dumps())
        rpc_commit(self.__socket)

    def get_root(self):
        return self.__root

    def set_root(self, root):
        send(self.__socket, root.dumps())
        rpc_commit(self.__socket)


def rpc(sockpath="/usr/local/var/controller.sock"):
    def decorator(func):
        def wrapper(*args, **kwargs):
            with Clixon(sockpath) as root:
                return func(root, logger)
        return wrapper
    return decorator
