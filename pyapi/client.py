import asyncio
import struct
import socket
import queue
from log import get_logger

logger = get_logger()
dataq = queue.Queue()
hdrlen = 8


async def run_modules(modules):
    logger.debug(f"Modules: {modules}")
    for module in modules:
        module.setup()


def create_socket(sockpath):
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.setblocking(False)
    sock.connect(sockpath)

    return sock


async def read(loop, sock, modules):
    while True:
        recvdata = await loop.sock_recv(sock, hdrlen)
        datalen, _ = struct.unpack("!II", recvdata)

        recvdata = await loop.sock_recv(sock, datalen)
        data = recvdata.strip()

        recvlen = len(data)

        logger.debug(f"Recevied {recvlen} pieces of data")
        logger.debug(data)

        if b"<notification" in data:
            if b"<services-commit" in data:
                logger.debug("Received service notify")
                await run_modules(modules)
        else:
            logger.debug("Data put in queue")
            dataq.put(data)


async def send(loop, sock, data):
    datalen = len(data)
    opid = 42

    if type(data) != bytes:
        data = str.encode(data)

    frame = struct.pack("!II", datalen + hdrlen + 1, opid)

    await loop.sock_sendall(sock, frame + data + b"\0")

    sent = len(frame)

    logger.debug(f"Sent {sent} pieces of data")
