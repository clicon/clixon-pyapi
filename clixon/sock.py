import socket
from clixon.args import get_logger
from typing import Optional
import select
import struct
from clixon.element import Element
from clixon.netconf import rpc_error_get
from clixon.parser import dump_string


logger = get_logger()
hdrlen = 8


def create_socket(sockpath: str) -> socket.socket:
    """
    Create a socket and connect to the socket path.
    """

    logger.debug(f"Connecting to socket: {sockpath}")

    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.setblocking(False)
    sock.connect(sockpath)

    return sock


def read(sock: socket.socket, pp: Optional[bool] = False) -> str:
    """
    Read from the socket and return the data.
    """

    data = ""
    datalen = 0

    logger.debug("Waiting for select")

    readable, writable, exceptional = select.select(
        [sock], [], [])

    for read in readable:
        recv = read.recv(hdrlen)
        datalen, opid = struct.unpack("!II", recv)
        recv = read.recv(datalen - hdrlen)

        logger.debug("Read:")
        logger.debug(f"  len={datalen}")
        logger.debug(f"  opid={opid}")
        logger.debug("  data=" + dump_string(recv, pp=pp))

        data += recv.decode()
        data = data[:-1]

    rpc_error_get(data)

    return data


def send(sock: socket.socket, data: str, pp: Optional[bool] = False) -> None:
    """
    Send data to the socket.
    """

    opid = 42

    if type(data) is Element:
        data = data.dumps()

    if not data.endswith("\0"):
        data += "\0"

    if type(data) is not bytes:
        data = str.encode(data)

    framelen = hdrlen + len(data)
    frame = struct.pack("!II", framelen, opid)

    sock.send(frame + data)

    logger.debug("Send:")
    logger.debug(f"  len={framelen}")
    logger.debug(f"  opid={opid}")
    logger.debug("  data=" + dump_string(data, pp=pp))
