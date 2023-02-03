import select
import socket
import struct

from pyapi.log import get_logger
from pyapi.modules import run_modules

logger = get_logger()
hdrlen = 8


def create_socket(sockpath):
    logger.debug(f"Connecting to socket: {sockpath}")

    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.setblocking(False)
    sock.connect(sockpath)

    return sock


def read(sock):
    data = ""
    hdrlen = 8
    datalen = 0
    logger.debug("Waiting for select")

    readable, writable, exceptional = select.select(
        [sock], [], [])

    for read in readable:
        recv = read.recv(hdrlen)
        datalen, opid = struct.unpack("!II", recv)

        recv = read.recv(datalen - hdrlen)
        data += recv.decode()

        logger.debug(f"Read: {datalen} bytes of data, opid={opid}: " + data)

    return data[:-1]


def readloop(sock, modules):
    logger.debug("Starting read loop")
    while True:
        try:
            data = read(sock)
        except struct.error as e:
            logger.error(f"Reader loop got an exception: {e}")
            return

        if "<notification" in data:
            if "<services-commit" in data:
                logger.debug("Received service notify")
                run_modules(modules)


def send(sock, data):
    opid = 42

    if not data.endswith("\0"):
        data += "\0"

    if type(data) != bytes:
        data = str.encode(data)

    framelen = hdrlen + len(data)
    frame = struct.pack("!II", framelen, opid)

    sock.send(frame + data)

    logger.debug(f"Send: {framelen} bytes of data: " + data.decode())
