import time
import asyncio
import importlib
import getopt
import sys
import os
import logging

from pyapi.clixon import rpc_subscription_create
from pyapi.client import create_socket, read, send

from log import get_logger

logger = get_logger()


def usage(err=""):
    name = sys.argv[0]

    if err != "":
        print(f"{name}: {err}")
        print("")
    print(f"{name} -F -Dn -P<path>")
    print("  -F       Run in foreground")
    print("  -D       Debug")

    sys.exit(0)


def find_modules():
    modules = []
    for root, dirs, files in os.walk("./modules/"):
        for module in files:
            if not module.endswith(".py"):
                logger.debug(f"Skipping file: {module}")
                continue
            logger.debug(f"Added module {module}")
            modules.append(module[:-3])

    return modules


def load_modules():
    loaded_modules = []
    for modulefile in find_modules():
        logger.debug(f"Importing module modules.{modulefile}")
        module = importlib.import_module("modules." + modulefile)
        loaded_modules.append(module)

    return loaded_modules


async def main():
    foreground = False

    try:
        opts, args = getopt.getopt(sys.argv[1:], "fds:")
    except getopt.GetoptError as e:
        usage(err=e)

    for opt, arg in opts:
        if opt == "-f":
            foreground = True
        if opt == "-d":
            logger.setLevel(logging.DEBUG)
        if opt == "-s":
            sockpath = arg

    modules = load_modules()

    if modules == []:
        print("No loadable modules found.")
        sys.exit(0)

    sock = create_socket(sockpath)
    enable_notify = rpc_subscription_create()
    loop = asyncio.get_event_loop()
    tasks = asyncio.gather(read(loop, sock, modules),
                           send(loop, sock, enable_notify.dumps()))

    await asyncio.wait_for(tasks, timeout=None)


if __name__ == "__main__":
    asyncio.run(main())

    while True:
        time.sleep(1)
