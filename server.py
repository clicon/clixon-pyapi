import os
import time
import flock
import fcntl
import sys
import threading

from pyapi.client import readloop
from pyapi.modules import load_modules
from pyapi.log import get_logger
from pyapi.args import parse_args

logger = get_logger()
lockfd = None


def main():
    sockpath, modulepath, modulefilter, pidfile = parse_args()
    try:
        lockfd = open(pidfile, "w")
        fcntl.lockf(lockfd, flock.LOCK_EX | flock.LOCK_NB)
    except IOError:
        logger.error("Another server is already running.")
        sys.exit(1)

    modules = load_modules(modulefilter)

    if modules == []:
        logger.error("No loadable modules found.")
        sys.exit(0)

    threads = []
    threads.append(threading.Thread(target=readloop, args=(sockpath, modules)))

    try:
        for thread in threads:
            thread.daemon = True
            thread.start()

        while True:
            time.sleep(5)
    except KeyboardInterrupt:
        fcntl.lockf(lockfd, fcntl.LOCK_UN)
        os.remove(pidfile)

        logger.info("Goodbye!")
        sys.exit(0)
    except IOError as e:
        logger.error(f"IO error: {e}")
    except Exception as e:
        logger.error(e)


if __name__ == "__main__":
    main()
