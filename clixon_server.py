#!/usr/bin/env python3
import sys

from pidfile import AlreadyRunningError, PIDFile

from clixon.args import get_logger, parse_args
from clixon.client import readloop
from clixon.modules import load_modules

(sockpath, mpath, mfilter, pidfile, pp, _, _) = parse_args(sys.argv[1:])

logger = get_logger()
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
    try:
        with PIDFile(pidfile):
            main()
    except AlreadyRunningError:
        logger.error("Server already running.")
