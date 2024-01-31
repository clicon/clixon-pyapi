import re
import sys
import time
import traceback
from typing import Optional
import struct
from clixon.args import get_logger
from clixon.modules import run_modules
from clixon.netconf import RPCTypes, rpc_header_get, rpc_subscription_create
from clixon.parser import parse_string
from clixon.sock import read, send, create_socket

logger = get_logger()


def readloop(sockpath: str, modules: list, pp: Optional[bool] = False) -> None:
    """
    Read loop for the client.
    :param sockpath: Path to the socket
    :param modules: List of modules to run
    :param pp: Pretty print
    :return: None
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

        try:
            logger.info("Enable service subscriptions")
            enable_service_notify = rpc_subscription_create()
            send(sock, enable_service_notify, pp)
            read(sock, pp)

            logger.info("Enable transaction subscriptions")
            enable_transaction_notify = rpc_subscription_create(
                "controller-transaction")
            send(sock, enable_transaction_notify, pp)
            read(sock, pp)
        except Exception as e:
            logger.error(str(e))
            return

        logger.info("Listening for notifications...")

        while True:
            try:
                data = read(sock, pp)
            except struct.error:
                logger.error("Socket closed, backend probably died")
                sys.exit(1)
            except Exception:
                logger.error("Reader loop got an exception:")
                logger.error(traceback.print_exc())

                time.sleep(3)
                break

            if "<notification" not in data:
                continue

            if "<services-commit" not in data:
                continue

            logger.debug("Received service notify")

            reply = parse_string(data)
            notification = reply.notification
            tid = str(notification.services_commit.tid.cdata)

            rpc = rpc_header_get(
                RPCTypes.TRANSACTION_DONE, "root")
            rpc.rpc.transaction_actions_done.create(
                "tid", cdata=tid)

            try:
                services = notification.services_commit.service
            except AttributeError:
                services = None

            if services:
                for service in services:
                    match = re.match(r"(\S+)\[.+='(\S+)'\]", service.cdata)

                    try:
                        service_name = match.group(1)
                        instance = match.group(2)

                        run_modules(modules, service_name, instance)
                    except Exception as e:
                        logger.error("Catched an module exception")

                        traceback.print_exc()

                        rpc = rpc_header_get(
                            RPCTypes.TRANSACTION_ERROR, "root")
                        rpc.rpc.transaction_error.create(
                            "tid", cdata=tid)
                        rpc.rpc.transaction_error.create(
                            "origin", cdata="pyapi")
                        rpc.rpc.transaction_error.create(
                            "reason", cdata=str(e))

                        break

                    else:
                        logger.debug(f"Service {service_name} done")
                        rpc.rpc.transaction_actions_done.create(
                            "service", cdata=service_name)

            else:
                logger.debug(
                    "No services in commit, running all services")
                run_modules(modules, None, None)

            send(sock, rpc, pp)
