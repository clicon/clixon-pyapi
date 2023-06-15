#!/usr/bin/env python3
import os
import sys
import threading
import time

from daemonize import Daemonize

from clixon.args import parse_args, get_logger
from clixon.client import readloop
from clixon.modules import load_modules

sockpath, modulespath, modulefilter, pidfile, foreground, pp, _, _ = parse_args()
logger = get_logger()
lockfd = None


def main() -> None:
    """
    Main function for clixon_server.
    """

    modules = load_modules(modulespath, modulefilter)

    if modules == []:
        logger.error("No loadable modules found.")
        sys.exit(0)

    threads = []
    threads.append(threading.Thread(
        target=readloop, args=(sockpath, modules, pp)))

    try:
        logger.debug("Starting threads.")
        for thread in threads:
            thread.daemon = True
            thread.start()

        while True:
            time.sleep(5)
    except IOError as e:
        logger.error(f"IO error: {e}")
    except Exception as e:
        logger.error(e)
    except KeyboardInterrupt:
        logger.info("\nGoodbye.")


if __name__ == "__main__":
    daemon = Daemonize(app="clixon_server", pid=pidfile, action=main,
                       logger=logger,
                       foreground=foreground,
                       verbose=True,
                       chdir=os.getcwd())
    daemon.start()
