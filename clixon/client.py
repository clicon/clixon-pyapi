import select
import socket
import struct
import time
from typing import Optional

from clixon.element import Element
from clixon.log import get_logger
from clixon.modules import run_modules
from clixon.netconf import (RPCTypes, rpc_error_get, rpc_header_get,
                            rpc_subscription_create)
from clixon.parser import dump_string, parse_string

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
        logger.debug("  data=" + dump_string(recv, pp=pp))

        data += recv.decode()
        data = data[:-1]

    rpc_error_get(data)

    return data


def readloop(sockpath: str, modules: list, pp: Optional[bool] = False) -> None:
    """
    Read loop for the client.
    """

    logger.debug("Starting read loop")
    while True:
        logger.debug("Creating socket and enables notify")

        try:
            sock = create_socket(sockpath)
        except Exception as e:
            logger.error(f"Could not connect to socket: {e}")
            time.sleep(3)
            continue

        logger.info("Enable service subscriptions")
        enable_service_notify = rpc_subscription_create()
        send(sock, enable_service_notify, pp)
        read(sock, pp)

        logger.info("Enable transaction subscriptions")
        enable_transaction_notify = rpc_subscription_create(
            "controller-transaction")
        send(sock, enable_transaction_notify, pp)
        read(sock, pp)

        logger.info("Listening for notifications...")

        while True:
            try:
                data = read(sock, pp)
            except Exception as e:
                logger.error(f"Reader loop got an exception: {e}")
                time.sleep(3)
                break

            if "<notification" in data:
                if "<services-commit" in data:
                    logger.debug("Received service notify")

                    reply = parse_string(data)
                    notification = reply.notification
                    tid = str(notification.services_commit.tid.cdata)

                    try:
                        run_modules(modules)
                    except Exception as e:
                        logger.error("Catched an module exception")

                        rpc = rpc_header_get(
                            RPCTypes.TRANSACTION_ERROR, "root")
                        rpc.rpc.transaction_error.create(
                            "tid", cdata=tid)
                        rpc.rpc.transaction_error.create(
                            "origin", cdata="pyapi")
                        rpc.rpc.transaction_error.create(
                            "reason", cdata=str(e))

                    else:
                        logger.info("All modules done, finishing transaction")

                        rpc = rpc_header_get(RPCTypes.TRANSACTION_DONE, "root")
                        rpc.rpc.transaction_actions_done.create(
                            "tid", cdata=tid)

                        for child in notification.services_commit.get_elements():
                            if child.get_name() == "service":
                                rpc.rpc.transaction_actions_done.create(
                                    "service", cdata=str(child.cdata))

                    send(sock, rpc, pp)

            else:
                print(data)


def send(sock: socket.socket, data: str, pp: Optional[bool] = False) -> None:
    """
    Send data to the socket.
    """

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
    logger.debug("  data=" + dump_string(data, pp=pp))
