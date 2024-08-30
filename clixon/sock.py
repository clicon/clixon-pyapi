import re
import socket
from clixon.args import get_logger
from typing import Optional
import select
from clixon.element import Element
from clixon.parser import dump_string


logger = get_logger()
hdrlen = 8


class SocketClosedError(Exception):
    """
    Raised when the socket is closed.
    """

    pass


def create_socket(sockpath: str) -> socket.socket:
    """
    Create a socket and connect to the socket path.

    :param sockpath: Path to the socket
    :type sockpath: str
    :return: socket
    :rtype: socket.socket

    """

    logger.debug(f"Connecting to socket: {sockpath}")

    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.setblocking(False)
    sock.connect(sockpath)

    return sock


def read(
    sock: socket.socket, pp: Optional[bool] = False, standalone: Optional[bool] = False
) -> str:
    """
    Read from the socket and return the data.

    :param sock: Socket to read from
    :type sock: socket.socket
    :param pp: Pretty print the data
    :type pp: bool
    :param standalone: If True, raise an exception if the data is an error
    :type standalone: bool
    :return: Data read from the socket
    :rtype: str
    """

    data = b""
    chunk_len = 0

    re_chunk_size = r"\n#(\d+)\n"

    while True:
        readable, _, _ = select.select([sock], [], [])

        if not readable:
            continue

        if not chunk_len:
            chunk_len = re.search(re_chunk_size, data.decode())

            if chunk_len:
                chunk_len = int(chunk_len.group(1))
                logger.debug(f"Found chunk length: {chunk_len}")
                data = b""
            else:
                tmpdata = sock.recv(1)

                if not tmpdata:
                    raise SocketClosedError("Socket closed")

                data += tmpdata
        else:
            if len(data) < int(chunk_len):
                data += sock.recv(chunk_len - len(data) + 3)
            else:
                break

    if data[-3:] == b"\n##":
        data = data[:-3]

    if isinstance(data, bytes):
        data = data.decode()

    logger.debug("Read:")
    logger.debug(f"  len={chunk_len}")
    logger.debug("  data=" + dump_string(data, pp=pp))

    return data


def send(sock: socket.socket, data: str, pp: Optional[bool] = False) -> None:
    """
    Send data to the socket.

    :param sock: Socket to send data to
    :type sock: socket.socket
    :param data: Data to send
    :type data: str
    :param pp: Pretty print the data
    :type pp: bool
    :return: None
    :rtype: None

    """

    if type(data) is Element:
        data = data.dumps()

    if type(data) is not bytes:
        data = str.encode(data)

    datalen = len(data)

    frame_start = b"\n#"
    frame_end = b"\n##\n"

    frame_header = frame_start + str(datalen).encode() + b"\n"
    framelen = len(frame_header) + datalen + len(frame_end)

    frame = frame_header + data + frame_end

    sent = 0
    sent_total = 0

    logger.debug(f"Sending {framelen} bytes of data")

    # Send all the data in data
    while sent_total < framelen:
        _, writable, _ = select.select([], [sock], [])

        if not writable:
            logger.debug("No data available")
            continue

        sent = int(sock.send(frame[sent_total:]))
        sent_total += sent

    logger.debug("Send:")
    logger.debug(f"  len={framelen}")
    logger.debug("  data=" + dump_string(data, pp=pp))
    logger.debug(f"  sent={sent_total}")

    return sent_total
