#!/usr/bin/env python3
import os
import sys

from daemonize import Daemonize

from clixon.args import parse_args
from clixon.client import readloop
from clixon.log import init_root_logger
from clixon.modules import load_modules

(
    sockpath,
    mpath,
    mfilter,
    pidfile,
    foreground,
    pp,
    log,
    debug
) = parse_args(sys.argv[1:])

logger = init_root_logger(log, debug)
lockfd = None


def main() -> None:
    """
    Main function for clixon_server.
    """

    modules = []

    for path in mpath:
        sys.path.append(path)
        modules.extend(load_modules(path, mfilter))

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
