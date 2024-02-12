import argparse
import os
import signal
import sys
from typing import Optional

import clixon.parser as parser
from clixon.log import get_log_factory


def __kill(pidfile: str) -> None:
    """
    Kill daemon.
    :param pidfile: Pidfile
    :return: None
    """

    try:
        with open(pidfile) as fd:
            pid = int(fd.read())
            print(f"Killing daemon with pid {pid}!")
            os.kill(pid, signal.SIGTERM)
    except FileNotFoundError:
        print(f"Pidfile {pidfile} not found")


def __parse_config_file(configfile: str) -> tuple:
    """
    Parse configuration variables
        sockpath, modulepaths, modulefilter, pidfile
    from file.
    :param configfile: Configuration file
    :return: Tuple with parsed configuration
    """

    # Jupyter sucks
    if "jupyter" in configfile:
        print("Looks like you are running this from Jupyter.")
        print("I'll fall back to the default configuration file",
              "since Jupyter messes with sys.argv.")
        configfile = "/usr/local/etc/clixon/controller.xml"

    config = parser.parse_file(configfile)

    try:
        config = config.clixon_config

        sockpath = config.CLICON_SOCK.cdata
        modulepath = config.CONTROLLER_PYAPI_MODULE_PATH.cdata
        modulefilter = config.CONTROLLER_PYAPI_MODULE_FILTER.cdata
        pidfile = config.CONTROLLER_PYAPI_PIDFILE.cdata
    except AttributeError as e:
        print(f"Could not parse confiuguration file: {e}")

        sys.exit(1)

    return sockpath, [modulepath], modulefilter, pidfile


global_args = {}


def parse_args(cli_args: Optional = None) -> tuple:
    """
    Parse command line arguments.

    :param cli_args: List of command line arguments
    :return: Tuple with configuration
    """
    global global_args

    default_mpath = "/usr/local/share/clixon/controller/modules/"
    default_sockpath = "/usr/local/var/run/controller.sock"
    default_pidfile = "/tmp/clixon_server.pid"
    default_log = "s"

    parser = argparse.ArgumentParser(description="clixon PyAPI")
    parser.add_argument("-f", "--configfile",
                        help="Clixon controller configuration file")
    parser.add_argument("-m", "--modulepaths", action="append",
                        default=[default_mpath], help="Modules path")
    parser.add_argument("-e", "--modulefilter", default="",
                        help="Comma separated list of modules to exclude")
    parser.add_argument("-d", "--debug", action="store_true",
                        help="Enable verbose debug logging")
    parser.add_argument("-s", "--sockpath",
                        default=default_sockpath,
                        help="Clixon socket path")
    parser.add_argument("-p", "--pidfile", default=default_pidfile,
                        help="Pidfile for Python server")
    parser.add_argument("-F", "--foreground", action="store_true",
                        help="Run in foreground")
    parser.add_argument("-P", "--pp", action="store_true",
                        help="Prettyprint XML")
    parser.add_argument("-l", "--log", choices=["s", "o"], default=default_log,
                        help="Log on (s)yslog, std(o)ut")
    parser.add_argument("-z", "--kill-daemon", action="store_true",
                        help="Kill daemon")
    args = parser.parse_args(cli_args)

    if args.kill_daemon:
        __kill(args.pidfile)
        sys.exit(0)

    args.modulepaths = list(set(args.modulepaths))
    if not all(map(os.path.exists, args.modulepaths)):
        print(f"Module path {args.modulepaths} contains non-existing paths")
        sys.exit(0)

    if args.configfile is not None and not os.path.exists(args.configfile):
        print(f"Configuration file {args.configfile} does not exist")
        sys.exit(0)

    # Load
    #   sockpath, conf_mpath, modulefilter, pidfile
    # from config file
    if args.configfile:
        sockpath, conf_mpath, modulefilter, pidfile = __parse_config_file(
            args.configfile)
        args.sockpath = sockpath
        args.modulepaths.extend(conf_mpath)
        args.modulefilter = modulefilter
        args.pidfile = pidfile

    # Save args in global scope for get_args function
    global_args = vars(args)

    return (args.sockpath,
            args.modulepaths,
            args.modulefilter,
            args.pidfile,
            args.foreground,
            args.pp,
            args.log,
            args.debug)


def get_logger():
    """
    Get logger.
    :return: Logger
    """

    log = get_arg("log")
    debug = get_arg("debug")

    logger = get_log_factory(log, debug)

    return logger


def get_arg(opt: str):
    """
    Get CLI argument.

    :param opt: Key of option to get.
    :return: Value of key
    """
    if opt in global_args.keys():
        return global_args.get(opt)

    return None
