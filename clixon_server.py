#!/usr/bin/env python3

import fcntl
import os
import sys
import threading
import time

import flock

from clixon.args import parse_args
from clixon.client import readloop
from clixon.log import get_logger
from clixon.modules import load_modules

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
