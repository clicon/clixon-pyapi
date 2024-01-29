#!/usr/bin/env python3
import os
import sys

from daemonize import Daemonize

from clixon.args import parse_args, get_logger
from clixon.client import readloop
from clixon.modules import load_modules

(sockpath, mpath, mfilter, pidfile, foreground, pp, _, _) = parse_args()

logger = get_logger()
lockfd = None


def main() -> None:
    """
    Main function for clixon_server.
    """

    modules = []

    for path in mpath:
        sys.path.append(path)
        modules.append(load_modules(path, mfilter))

    if modules == []:
        logger.error("No loadable modules found.")
        sys.exit(0)

    try:
        readloop(sockpath, modules, pp)
    except IOError as e:
        logger.error(f"IO error: {e}")
    except Exception as e:
        logger.error(e)
    except KeyboardInterrupt:
        logger.info("\nGoodbye.")


if __name__ == "__main__":
    if foreground:
        main()
    else:
        daemon = Daemonize(app="clixon_server", pid=pidfile, action=main,
                           logger=logger,
                           foreground=foreground,
                           verbose=True,
                           chdir=os.getcwd())
        daemon.start()
