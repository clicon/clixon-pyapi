#!/usr/bin/env python3

"""
This module provides the clixon_server program.
"""

import cProfile
import fcntl
import os
import signal
import sys

from clixon.args import get_arg, get_logger, parse_args
from clixon.client import readloop
from clixon.modules import load_modules

(sockpath, mpath, mfilter, pidfile, pp, _, _) = parse_args(sys.argv[1:])

logger = get_logger()
LOCKFD = None


class PIDLock:
    """
    Class for locking the PID file.
    """

    def __init__(self, pid_file):
        self.__pidfile = pid_file
        self.__pidfd = None

    def __enter__(self):
        self.__pidfd = open(self.__pidfile, "a+", encoding="utf-8")
        try:
            fcntl.flock(self.__pidfd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except IOError:
            logger.error("Another instance of clixon_server is running.")
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
            os.remove(pidfile)
        except IOError as err:
            if err.errno != 9:
                raise


def main() -> None:
    """
    Main function for clixon_server.
    """

    modules = []

    for path in mpath:
        sys.path.append(path)
        modules.extend(load_modules(path, mfilter))

    if not modules:
        logger.error("No loadable modules found.")
        sys.exit(0)

    try:
        readloop(sockpath, modules, pp)
    except IOError as e:
        logger.error("IO error: %s", e)
    except KeyboardInterrupt:
        logger.info("\nGoodbye.")


def run_profiled(outfile: str) -> None:
    """
    Run main() under cProfile and write the stats to outfile on exit.
    SIGTERM is turned into a clean exit so the stats are always written.
    """

    def _on_sigterm(signum, frame):
        raise SystemExit(0)

    signal.signal(signal.SIGTERM, _on_sigterm)
    profiler = cProfile.Profile()
    logger.info(f"Profiling enabled, stats will be written to {outfile}")

    try:
        profiler.runcall(main)
    finally:
        profiler.dump_stats(outfile)
        logger.info(f"Profile written to {outfile}")


if __name__ == "__main__":
    try:
        logger.info(f"Creating PID file {pidfile}")
        with PIDLock(pidfile):
            profile_file = get_arg("profile")
            if profile_file:
                run_profiled(profile_file)
            else:
                main()
    except Exception:
        process_name = os.path.basename(sys.argv[0])
        logger.error(
            f"Either another instance of {process_name} is running or "
            f"the PID file {pidfile} can not be created."
        )
