from logging import getLogger
import select
import socket
import struct
from typing import Optional

from clixon.element import Element
from clixon.parser import dump_string


logger = getLogger(__name__)
hdrlen = 8


def create_socket(sockpath: str) -> socket.socket:
    """
    Create a socket and connect to the socket path.
    :param sockpath: Path to the socket
    :return: socket
    """

    logger.debug(f"Connecting to socket: {sockpath}")

    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.setblocking(False)
    sock.connect(sockpath)

    return sock


def read(sock: socket.socket, pp: Optional[bool] = False,
         standalone: Optional[bool] = False) -> str:
    """
    Read from the socket and return the data.
    :param sock: Socket to read from
    :param pp: Pretty print the data
    :param standalone: If True, raise an exception if the data is an error
    :return: Data read from the socket
    """

    data = ""
    datalen = 0
    opid = 0

    logger.debug("Waiting for select")

    while datalen == 0 or len(data) < datalen - hdrlen:
        readable, _, _ = select.select([sock], [], [])

        for readable_sock in readable:
            if readable_sock != sock:
                logger.debug("This is not the socket we want")
                continue

            if datalen == 0:
                recv = sock.recv(hdrlen)
                datalen, opid = struct.unpack("!II", recv)

                logger.debug("Read header:")
                logger.debug(f"  len={datalen}")
                logger.debug(f"  opid={opid}")

                break
            else:
                recv = sock.recv(datalen - hdrlen)
                data += recv.decode()

    data = data[:-1]

    logger.debug("Read:")
    logger.debug(f"  len={datalen}")
    logger.debug(f"  opid={opid}")
    logger.debug("  data=" + dump_string(data, pp=pp))

    return data


def send(sock: socket.socket, data: str, pp: Optional[bool] = False) -> None:
    """
    Send data to the socket.
    :param sock: Socket to send data to
    :param data: Data to send
    :param pp: Pretty print the data
    :return: None
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
    frame = frame + data

    sent = 0
    sent_total = 0

    # Send all the data in data
    while sent_total < framelen:
        _, writable, _ = select.select([], [sock], [])

        if not writable:
            continue

        sent = int(sock.send(frame[sent_total:]))
        sent_total += sent

    logger.debug("Send:")
    logger.debug(f"  len={framelen}")
    logger.debug(f"  opid={opid}")
    logger.debug("  data=" + dump_string(data, pp=pp))
    logger.debug(f"  sent={sent_total}")
