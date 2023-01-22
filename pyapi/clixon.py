import socket
import struct
import select

from enum import Enum
from pyapi.parser import Element, parse_string


class RPCTypes(Enum):
    GET_CONFIG = 0
    EDIT_CONFIG = 1
    COMMIT = 2


class Clixon():
    def __init__(self, sockpath, notification=False):
        self.__hdrlen = 8
        self.__sockpath = sockpath
        self.__connect()

        if notification:
            pass

    def __enter__(self):
        self.root = self.rpc_config_get()

        return self.root

    def __exit__(self, *args):
        self.rpc_config_set(self.root)
        self.rpc_commit()

    def __connect(self):
        self.__socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.__socket.connect(self.__sockpath)

    def __send(self, data):
        """
        Send data over socket. Will pack the data to fit Clixons
        dataframe which is used to communicate over the UNIX socket.

        struct clicon_msg {
            uint32_t    op_len;     /* length of message. network byte order.*/
            uint32_t    op_id;      /* session-id. network byte order. */
            char        op_body[0]; /* rest of message, actual data */
        };

        op_len is the length of the NETCONF message + the size of the header
        (8 bytes) defined as HDRLEN above.

        """
        datalen = len(data)
        opid = 42

        if type(data) != bytes:
            data = str.encode(data)

        frame = struct.pack("!II", datalen + self.__hdrlen + 1, opid)

        self.__socket.sendall(frame + data + b"\0")

    def __read(self):
        """
        Read from the socket. Will pick up the header first and figure out
        the number of bytes of NETCONF message to read from the socket.
        """
        data = ""

        readable, writable, exceptional = select.select(
            [self.__socket], [], [])

        for read in readable:
            recv = read.recv(self.__hdrlen)
            datalen, _ = struct.unpack("!II", recv)

            recv = read.recv(datalen)
            data += recv.decode()[:-1]

        return data

    def __get_rpc_header(self, rpc_type, user):
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

    def rpc_config_get(self, user="root"):
        attributes = {
            "nc:type": "xpath",
            "nc:select": "/"
        }

        root = self.__get_rpc_header(RPCTypes.GET_CONFIG, user)
        root.rpc.get_config.add_element("source")
        root.rpc.get_config.source.add_element("candidate")
        root.rpc.get_config.add_element(
            "nc_filter", origname="nc:filter", attributes=attributes)
        self.__send(root.dumps())
        data = self.__read()

        root = parse_string(data)

        return root.rpc_reply.data

    def rpc_config_set(self, config, user="root"):
        root = self.__get_rpc_header(RPCTypes.EDIT_CONFIG, user)
        root.rpc.edit_config.add_element("target")
        root.rpc.edit_config.target.add_element("candidate")
        root.rpc.edit_config.add_element(
            "default_operation", origname="default-operation")
        root.rpc.edit_config.default_operation.set_cdata("replace")
        root.rpc.edit_config.add_element("config")

        for node in config.get_elements():
            root.rpc.edit_config.config.add_child(node)

        self.__send(root.dumps())
        self.rpc_commit()

    def rpc_commit(self, user="root"):
        root = self.__get_rpc_header(RPCTypes.COMMIT, user)

        self.__send(root.dumps())
        data = self.__read()

        root = parse_string(data)
        return root.rpc_reply

    def rpc_subscription_create(self):
        attributes = {
            "xmlns": "urn:ietf:params:xml:ns:netmod:notification"
        }

        root = self.__get_rpc_header("", "root")
        root.add_element("create_subscription",
                         origname="create-subscripton", attributes=attributes)
        root.create_subscription.add_element("stream")
        root.create_subscription.stream.set_cdata("controller")
        root.create_subscription.add_element("filter", attributes={
            "type": "xpath",
            "select": ""
        })

        return root


def rpc(sockpath):
    """
    The whole idea with this decorator is to do something like this:

    @rpc(sockpath)
    def test(root):
        print(root.dumps())

    root is the whole configuration three and is written back to
    Clixon when one exits the function.

    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            with Clixon(sockpath) as root:
                return func(root)
        return wrapper
    return decorator


def notification(sockpath):
    def decorator(func):
        def wrapper(*args, **kwargs):
            with Clixon(sockpath, notification=True) as root:
                return func(root)
        return wrapper
    return decorator
