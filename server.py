import flock
import fcntl
import time
import asyncio
import importlib
import getopt
import sys
import os
import logging

from pyapi.clixon import rpc_subscription_create
from pyapi.client import create_socket, readloop, send

from log import get_logger

logger = get_logger()
lockfd = None


def usage(err=""):
    name = sys.argv[0]

    if err != "":
        print(f"{name}: {err}")
        print("")
    print(f"{name} -f<module1,module2> -s<path> -d -p<pidfile>")
    print("  -f       Module filter, comma separate list of modules")
    print("  -d       Debug")
    print("  -s       Clixon socket path")
    print("  -p       Pidfile for Python server")

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


def load_modules(modulefilter):
    loaded_modules = []
    filtered = modulefilter.split(",")
    for modulefile in find_modules():
        if modulefile in filtered:
            logger.debug(f"Skipping module: {modulefile}")
            continue

        logger.debug(f"Importing module modules.{modulefile}")
        module = importlib.import_module("modules." + modulefile)
        loaded_modules.append(module)

    return loaded_modules


async def main(sockpath, modulefilter):
    logger.debug(f"Socket path: {sockpath}")

    modules = load_modules(modulefilter)

    if modules == []:
        logger.error("No loadable modules found.")
        sys.exit(0)

    sock = create_socket(sockpath)
    enable_notify = rpc_subscription_create()
    loop = asyncio.get_event_loop()
    send(sock, enable_notify.dumps())

    tasks = asyncio.gather(readloop(loop, sock, modules))
    await asyncio.wait_for(tasks, timeout=None)

if __name__ == "__main__":
    sockpath = "/usr/local/var/controller.sock"
    pidfile = "/tmp/clixon_pyserver.pid"
    modulefilter = ""

    try:
        lockfd = open(pidfile, "w")
        fcntl.lockf(lockfd, flock.LOCK_EX | flock.LOCK_NB)
    except IOError:
        logger.error("Failed to create lock file, quitting!")
        sys.exit(0)

    try:
        opts, args = getopt.getopt(sys.argv[1:], "ds:f:p:")
    except getopt.GetoptError as e:
        usage(err=e)

    for opt, arg in opts:
        if opt == "-d":
            logger.setLevel(logging.DEBUG)
        if opt == "-s":
            sockpath = arg
        if opt == "-f":
            modulefilter = arg
        if opt == "-p":
            pidfile = arg

    try:
        asyncio.run(main(sockpath, modulefilter))
    except KeyboardInterrupt:
        fcntl.lockf(lockfd, fcntl.LOCK_UN)

        logger.info("Goodbye!")
        sys.exit(0)

    while True:
        time.sleep(1)
