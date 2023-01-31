import flock
import fcntl
import time
import getopt
import sys
import logging
import threading

from pyapi.clixon import rpc_subscription_create
from pyapi.client import create_socket, readloop, send
from pyapi.modules import load_modules
from pyapi.log import get_logger

logger = get_logger()
lockfd = None


def usage(err=""):
    name = sys.argv[0]

    if err != "":
        print(f"{name}: {err}")
        print("")
    print(f"{name} -f<module1,module2> -s<path> -d -p<pidfile>")
    print("  -f       Comma separate list of modules to exclude")
    print("  -d       Enable verbose debug logging")
    print("  -s       Clixon socket path")
    print("  -p       Pidfile for Python server")
    print("  -h       This!")

    sys.exit(0)


def main(sockpath, modulefilter):
    logger.debug(f"Socket path: {sockpath}")

    modules = load_modules(modulefilter)

    if modules == []:
        logger.error("No loadable modules found.")
        sys.exit(0)

    sock = create_socket(sockpath)
    enable_notify = rpc_subscription_create()
    send(sock, enable_notify.dumps())

    threads = []

    threads.append(threading.Thread(target=readloop, args=(sock, modules)))

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()


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
        elif opt == "-s":
            sockpath = arg
        elif opt == "-f":
            modulefilter = arg
        elif opt == "-p":
            pidfile = arg
        else:
            print(opt)
            usage()

    try:
        main(sockpath, modulefilter)
    except KeyboardInterrupt:
        fcntl.lockf(lockfd, fcntl.LOCK_UN)

        logger.info("Goodbye!")
        sys.exit(0)

    while True:
        time.sleep(1)
