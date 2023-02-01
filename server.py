import os
import time
import flock
import fcntl
import sys
import threading

from pyapi.clixon import rpc_subscription_create
from pyapi.client import create_socket, readloop, send
from pyapi.modules import load_modules
from pyapi.log import get_logger
from pyapi.args import parse_args

logger = get_logger()
lockfd = None


def main():
    try:
        sockpath, modulepath, modulefilter, pidfile = parse_args()
        lockfd = open(pidfile, "w")
        fcntl.lockf(lockfd, flock.LOCK_EX | flock.LOCK_NB)
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
            thread.daemon = True
            thread.start()

        while True:
            time.sleep(5)
    except IOError:
        logger.error("Another instance of the server is already running!")
        sys.exit(0)
    except KeyboardInterrupt:
        fcntl.lockf(lockfd, fcntl.LOCK_UN)
        os.remove(pidfile)

        logger.info("Goodbye!")
        sys.exit(0)
    except Exception as e:
        logger.error(e)


if __name__ == "__main__":
    main()
