"""
Client module for the Clixon API.

This module is responsible for connecting to the Clixon API and listen for
notifications. It also contains the main read loop for the client.
"""

import re
import struct
import sys
import time
import traceback

from socket import socket
from typing import Optional

from clixon.args import get_logger
from clixon.event import RPCEventHandler
from clixon.modules import run_hooks
from clixon.modules import run_modules
from clixon.netconf import RPCTypes
from clixon.netconf import rpc_header_get
from clixon.netconf import rpc_subscription_create
from clixon.netconf import rpc_transactions_get
from clixon.parser import parse_string
from clixon.sock import SocketClosedError
from clixon.sock import create_socket
from clixon.sock import read
from clixon.sock import send

logger = get_logger()
events = RPCEventHandler()
transactions = {}


def __get_username(sock: socket, tid: int, pp: bool) -> str:
    """
    Get the username from the transaction ID.
    """

    rpc = rpc_transactions_get(tid=tid)

    send(sock, rpc, pp)
    data = read(sock, pp)
    root = parse_string(data)

    username = root.rpc_reply.data.transactions.transaction.username.get_data()

    return username


@events.register("*<controller-transaction*>*</controller-transaction>*")
def controller_transaction_cb(*args, **kwargs) -> None:
    """
    Callback for controller transaction

    :param args: Arguments
    :type args: list
    :param kwargs: Keyword arguments
    :type kwargs: dict
    :return: None
    :rtype: None

    """

    data = kwargs["data"]
    modules = kwargs["modules"]
    sock = kwargs["sock"]
    notification = parse_string(data)
    tid = str(notification.notification.controller_transaction.tid)
    result = str(notification.notification.controller_transaction.result)

    if tid not in transactions:
        return

    for service in transactions[tid]:
        match = re.match(r"(\S+)\[.+='(\S+)'\]", service.cdata)

        if not match:
            raise ValueError(
                f"Invalid command, could not parse service: {service.cdata}"
            )

        service_name = match.group(1)
        instance = match.group(2)

        run_hooks(sock, modules, service_name, instance, False, result)


@events.register("*<services-commit*>*</services-commit>*")
def services_commit_cb(*args, **kwargs) -> None:
    """
    Callback for services commit

    :param args: Arguments
    :type args: list
    :param kwargs: Keyword arguments
    :type kwargs: dict
    :return: None
    :rtype: None

    """

    data = kwargs["data"]
    sock = kwargs["sock"]
    modules = kwargs["modules"]
    pp = kwargs["pp"]
    service_name = ""
    service_diff = False

    logger.debug("Received service notify")

    reply = parse_string(data)
    notification = reply.notification
    tid = str(notification.services_commit.tid.cdata)

    username = __get_username(sock, tid, pp)

    rpc = rpc_header_get(RPCTypes.TRANSACTION_DONE, username)
    rpc.rpc.transaction_actions_done.create("tid", cdata=tid)

    try:
        services = notification.services_commit.service
    except AttributeError:
        services = None

    try:
        if not services:
            logger.debug("No services in commit, running all services")
            run_modules(sock, modules, None, None, user=username)
            send(sock, rpc, pp)

            return

        if "<diff>true</diff>" in data:
            logger.info("Service diff detected")
            service_diff = True
        else:
            logger.info("No service diff detected")
            transactions[tid] = services

        finished_services = []
        for service in services:
            match = re.match(r"(\S+)\[.+='(\S+)'\]", service.cdata)

            if not match:
                raise ValueError(
                    f"Invalid command, could not parse service: {service.cdata}"
                )

            service_name = match.group(1)
            instance = match.group(2)

            run_hooks(
                sock,
                modules,
                service_name,
                instance,
                service_diff,
                "pre-commit",
                user=username,
            )

            run_modules(
                sock, modules, service_name, instance, service_diff, user=username
            )

            if service_name not in finished_services:
                finished_services.append(service_name)
    except Exception as e:
        logger.error("Catched an module exception")
        logger.error(traceback.format_exc())

        if service_name:
            name = f" {service_name} "
        else:
            name = " "

        error = f"\nService module{name}returned an error:\n\n"
        error += str(e)

        rpc = rpc_header_get(RPCTypes.TRANSACTION_ERROR, "root")
        rpc.rpc.transaction_error.create("tid", cdata=tid)
        rpc.rpc.transaction_error.create("origin", cdata="pyapi")
        rpc.rpc.transaction_error.create("reason", cdata=error)
    else:
        logger.debug(f"Service {service_name} done")

        if not service_name:
            service_name = ""

        for service in finished_services:
            rpc.rpc.transaction_actions_done.create("service", cdata=service)

    send(sock, rpc, pp)


def enable_service_notify(sock: socket, pp: bool) -> None:
    """

    Enable service notifications

    :param sock: Socket
    :type sock: socket
    :param pp: Pretty print
    :type pp: bool
    :return: None
    :rtype: None

    """

    rpc = rpc_subscription_create()
    send(sock, rpc, pp)
    data = read(sock, pp)

    return data


def enable_transaction_notify(sock: socket, pp: bool) -> None:
    """

    Enable transaction notifications

    :param sock: Socket
    :type sock: socket
    :param pp: Pretty print
    :type pp: bool
    :return: None
    :rtype: None

    """

    rpc = rpc_subscription_create("controller-transaction")
    send(sock, rpc, pp)
    data = read(sock, pp)

    return data


def readloop(sockpath: str, modules: list, pp: Optional[bool] = False) -> None:
    """
    Read loop for the client.

    :param sockpath: Path to the socket
    :type sockpath: str
    :param modules: List of modules to run
    :type modules: list
    :param pp: Pretty print
    :type pp: bool
    :return: None
    :rtype: None

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
            data = enable_service_notify(sock, pp)

            events.emit(event=data, data=data, sock=sock, pp=pp)

            logger.info("Enable transaction subscriptions")
            data = enable_transaction_notify(sock, pp)

            events.emit(event=data, data=data, sock=sock, pp=pp)
        except Exception as e:
            logger.error(str(e))
            return

        logger.info("Listening for notifications...")

        while True:
            try:
                data = read(sock, pp)
                events.emit(event=data, data=data, sock=sock, modules=modules, pp=pp)
            except struct.error:
                logger.error("Socket closed, backend probably died")
                sys.exit(1)
            except SocketClosedError:
                logger.error("Socket closed, backend probably died")
                sys.exit(1)
            except Exception:
                logger.error("Reader loop got an exception:")
                logger.error(traceback.print_exc())

                time.sleep(3)
