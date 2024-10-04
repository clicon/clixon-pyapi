#!/usr/bin/env python3
import os
import sys
import fcntl
from clixon.args import get_logger, parse_args
from clixon.client import readloop
from clixon.modules import load_modules

(sockpath, mpath, mfilter, pidfile, pp, _, _) = parse_args(sys.argv[1:])

logger = get_logger()
lockfd = None


class PIDLock:
    def __init__(self, pidfile):
        self.__pidfile = pidfile
        self.__pidfd = None

    def __enter__(self):
        self.__pidfd = open(self.__pidfile, "a+")
        try:
            fcntl.flock(self.__pidfd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except IOError:
            logger.error(f"Another instance of clixon_server is running.")
            sys.exit(0)

        self.__pidfd.seek(0)
        self.__pidfd.truncate()
        self.__pidfd.write(str(os.getpid()))
        self.__pidfd.flush()
        self.__pidfd.seek(0)

        return self.__pidfd

    def __exit__(self, exc_type=None, exc_value=None, exc_tb=None):
        try:
            self.__pidfd.close()
        except IOError as err:
            if err.errno != 9:
                raise

        os.remove(self.__pidfile)


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
        with PIDLock(pidfile):
            main()
    except Exception as e:
        logger.error(e)
