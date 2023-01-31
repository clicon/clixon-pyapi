import select
import struct
import socket
from pyapi.modules import run_modules
from pyapi.log import get_logger

logger = get_logger()
hdrlen = 8


def create_socket(sockpath):
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

        logger.debug(f"Reading {datalen} bytes from select with ID {opid}")

        recv = read.recv(datalen - hdrlen)
        data += recv.decode()

    datalen = len(data)

    logger.debug(f"Got {datalen} bytes of data: {data}")

    return data[:-1]


def readloop(sock, modules):
    logger.debug("Starting read loop")
    while True:
        data = read(sock)
        if "<notification" in data:
            if "<services-commit" in data:
                logger.debug("Received service notify")
                run_modules(modules)
        else:
            logger.debug(f"Got data: {data}")


def send(sock, data):
    datalen = len(data)
    opid = 42

    if type(data) != bytes:
        data = str.encode(data)

    frame = struct.pack("!II", datalen + hdrlen + 1, opid)
    sock.send(frame + data + b"\0")
    sent = len(frame)

    logger.debug(f"Sent {sent} bytes of data: {str(data)}")
