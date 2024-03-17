import argparse
import logging
import os
import signal
import sys
from typing import Optional

from clixon.log import get_log_factory
import clixon.parser as parser
from clixon.version import __version__


def __update_from_configfile(opt: Optional[str] = None):
    """
    Update global arguments from configuration file.

    :param opt: Option
    :type opt: str
    :return: None
    :rtype: None

    """
    if not global_args.get("configfile"):
        return

    sockpath, modulepaths, modulefilter, pidfile = __parse_config(
        global_args.get("configfile"), opt)
    global_args["sockpath"] = sockpath
    global_args["modulepaths"] = modulepaths
    global_args["modulefilter"] = modulefilter
    global_args["pidfile"] = pidfile


def __kill(pidfile: str) -> None:
    """
    Kill daemon.

    :param pidfile: Pidfile
    :type pidfile: str
    :return: None
    :rtype: None

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
    :type configfile: str
    :param argname: Argument name
    :type argname: str
    :return: Tuple with configuration
    :rtype: tuple
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


def parse_args(cli_args: Optional[list] = None) -> tuple:
    """
    Parse command line arguments.

    :param cli_args: List of command line arguments
    :type cli_args: list
    :return: Tuple with configuration
    :rtype: tuple

    """
    global global_args

    default_mpath = "/usr/local/share/clixon/controller/modules"
    default_sockpath = "/usr/local/var/run/controller.sock"
    default_pidfile = "/tmp/clixon_server.pid"
    default_log = "s"

    parser = argparse.ArgumentParser(description="clixon PyAPI")
    parser.add_argument("-f", "--configfile",
                        help="Clixon controller configuration file")
    parser.add_argument("-m", "--modulepaths", action="append", default=[],
                        help="Modules path")
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
    parser.add_argument("-V", "--version", action="store_true",
                        help="Print version")
    args = parser.parse_args(cli_args)

    if args.kill_daemon:
        __kill(args.pidfile)

    if args.version:
        print(__version__)
        sys.exit(0)

    if args.modulepaths is None:
        args.modulepaths = [default_mpath]

    if not all(map(os.path.exists, args.modulepaths)):
        print(f"Module path {args.modulepaths} does not exist")
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

        for path in conf_mpath:
            if os.path.normpath(path) in args.modulepaths:
                continue
            args.modulepaths.extend(conf_mpath)

        args.modulefilter = modulefilter
        args.pidfile = pidfile

    if len(args.modulepaths) == 0:
        args.modulepaths = [default_mpath]
    args.modulepaths = list(set(args.modulepaths))

    if not all(map(os.path.exists, args.modulepaths)):
        print(f"Module path {args.modulepaths} contains non-existing paths")
        sys.exit(0)

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


def get_sockpath() -> str:
    """
    Get socket path.

    :return: Socket path
    :rtype: str

    """

    return get_arg("sockpath")


def get_prettyprint() -> bool:
    """
    Get prettyprint flag.

    :return: Prettyprint flag
    :rtype: bool

    """

    return get_arg("pp")


def get_arg(opt: str):
    """
    Get CLI argument.

    :param opt: Key of option to get.
    :type opt: str
    :return: Value of key
    :rtype: str

    """

    if "sphinx-build" in sys.argv[0]:
        return

    if opt in ["sockpath", "modulepaths", "modulefilter", "pidfile"]:
        __update_from_configfile(opt)

    if opt in global_args.keys():
        return global_args.get(opt)

    return None
