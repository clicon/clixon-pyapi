from pyapi.client import connect, read, send
from pyapi.parser import Element, parse_string


class Clixon():
    def __init__(self, sockpath):
        self.__sockpath = sockpath
        self.__socket = connect(self.__sockpath)

    def __enter__(self):
        self.root = self.rpc_config_get()

        return self.root

    def __exit__(self, *args):
        self.rpc_config_set(self.root)

    def __get_rpc_header(self, rpc_type, user):
        root = Element("root", {})
        root.add_element("rpc", attributes={"xmlns": "urn:ietf:params:xml:ns:netconf:base:1.0",
                                            "username": user, "xmlns:nc": "urn:ietf:params:xml:ns:netconf:base:1.0", "message-id": 42})

        if rpc_type == "get_config":
            root.rpc.add_element("get_config", origname="get-config")
        elif rpc_type == "edit_config":
            root.rpc.add_element("edit_config", origname="edit-config")
        else:
            raise ValueError("Unknown rpc_type")

        return root

    def rpc_config_get(self, user="root"):
        root = self.__get_rpc_header("get_config", user)
        root.rpc.get_config.add_element("source")
        root.rpc.get_config.source.add_element("candidate")
        root.rpc.get_config.add_element("nc_filter", origname="nc:filter",
                                        attributes={
                                            "nc:type": "xpath", "nc:select": "/"})
        send(self.__socket, root.dumps())
        data = read(self.__socket)

        root = parse_string(data)
        return root.rpc_reply.data

    def rpc_config_set(self, config, user="root"):
        root = self.__get_rpc_header("edit_config", user)
        root.rpc.edit_config.add_element("target")
        root.rpc.edit_config.target.add_element("candidate")
        root.rpc.edit_config.add_element(
            "default_operation", origname="default-operation")
        root.rpc.edit_config.default_operation.set_cdata("none")
        root.rpc.edit_config.add_element("config")

        for node in config.get_elements():
            root.rpc.edit_config.config.add_child(node)

        send(self.__socket, root.dumps())


def rpc(sockpath):
    def decorator(func):
        def wrapper(*args, **kwargs):
            with Clixon(sockpath) as root:
                return func(root)
        return wrapper
    return decorator
