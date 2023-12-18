"""
This module contains functions to read and write to a socket.
"""

import select
import socket
import struct

from typing import Optional
from clixon.args import get_logger
from clixon.element import Element
from clixon.netconf import rpc_error_get
from clixon.parser import dump_string


logger = get_logger()
HEADERLEN = 8


def create_socket(sockpath: str) -> socket.socket:
    """
    Create a socket and connect to the socket path.
    """

    logger.debug("Connecting to socket: %s", sockpath)

    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.setblocking(False)
    sock.connect(sockpath)

    return sock


def read(sock: socket.socket, pprint: Optional[bool] = False) -> str:
    """
    Read from the socket and return the data.
    """

    data = ""
    datalen = 0
    opid = 0

    logger.debug("Waiting for select")

    while datalen == 0 or len(data) < datalen - HEADERLEN:
        readable, _, _ = select.select([sock], [], [])

        for readable_sock in readable:
            if readable_sock != sock:
                logger.debug("This is not the socket we want")
                continue

            if datalen == 0:
                recv = sock.recv(HEADERLEN)
                datalen, opid = struct.unpack("!II", recv)

                logger.debug("Read header:")
                logger.debug("  len=%s", datalen)
                logger.debug("  opid=%s", opid)

                break

            recv = sock.recv(datalen - HEADERLEN)
            data += recv.decode()

    data = data[:-1]

    logger.debug("Read:")
    logger.debug("  len=%s", datalen)
    logger.debug("  opid=%s", opid)
    logger.debug("  data=%s",  dump_string(data, pprint=pprint))

    rpc_error_get(data)

    return data


def send(sock: socket.socket, data: str, pprint: Optional[bool] = False) -> None:
    """
    Send data to the socket.
    """

    opid = 42

    if isinstance(data, Element):
        data = data.dumps()

    if not data.endswith("\0"):
        data += "\0"

    if not isinstance(data, bytes):
        data = str.encode(data)

    framelen = HEADERLEN + len(data)
    frame = struct.pack("!II", framelen, opid)
    frame = frame + data

    sent = 0
    sent_total = 0

    # Send all the data in data

    while sent_total < framelen:
        _, writable, _ = select.select([], [sock], [])

        if not writable:
            continue

        sent = sock.send(frame[sent_total:])
        sent_total += sent

    logger.debug("Send:")
    logger.debug("  len=%s", framelen)
    logger.debug("  opid=%s", opid)
    logger.debug("  data=%s", dump_string(data, pprint=pprint))
    logger.debug("  sent=%s", sent_total)
