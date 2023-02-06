import select
import socket
import struct
import time

from clixon.element import Element
from clixon.log import get_logger
from clixon.modules import run_modules
from clixon.netconf import rpc_error_get, rpc_subscription_create

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

        logger.debug("Read:")
        logger.debug(f"  len={datalen}")
        logger.debug(f"  opid={opid}")
        logger.debug(f"  data={recv}")

        data += recv.decode()
        data = data[:-1]

    rpc_error_get(data)

    return data


def readloop(sockpath, modules):
    logger.debug("Starting read loop")
    while True:
        logger.debug("Creating socket and enables notify")

        try:
            sock = create_socket(sockpath)
        except FileNotFoundError as e:
            logger.error(f"Could not connect to socket: {e}")
            time.sleep(3)
            continue

        enable_notify = rpc_subscription_create()
        send(sock, enable_notify)

        while True:
            try:
                data = read(sock)
            except struct.error as e:
                logger.error(f"Reader loop got an exception: {e}")
                break

            if "<notification" in data:
                if "<services-commit" in data:
                    logger.debug("Received service notify")
                    run_modules(modules)


def send(sock, data):
    opid = 42

    if type(data) == Element:
        data = data.dumps()

    if not data.endswith("\0"):
        data += "\0"

    if type(data) != bytes:
        data = str.encode(data)

    framelen = hdrlen + len(data)
    frame = struct.pack("!II", framelen, opid)

    sock.send(frame + data)

    logger.debug("Send:")
    logger.debug(f"  len={framelen}")
    logger.debug(f"  opid={opid}")
    logger.debug(f"  data={data}")
