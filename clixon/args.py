import getopt
import os
import signal
import sys
from typing import Optional

import clixon.parser as parser
from clixon.log import get_log_factory


def get_logger():
    """
    Get logger.
    :return: Logger
    """

    log = parse_args("log")
    debug = parse_args("debug")

    logger = get_log_factory(log, debug)

    return logger


def get_sockpath():
    """
    Get socket path.
    :return: Socket path
    """

    return parse_args("sockpath")


def get_prettyprint():
    """
    Get prettyprint flag.
    :return: Prettyprint flag
    """

    return parse_args("pp")


def usage(err: Optional[str] = "") -> None:
    """
    Print usage and exit.
    :param err: Error message
    :return: None
    """

    name = sys.argv[0]

    if err != "":
        print(f"{name}: {err}")
        print("")
    print(f"{name} -f<module1,module2> -s<path> -d -p<pidfile>")
    print("  -f       Clixon controller configuration file")
    print("  -m       Modules path")
    print("  -e       Comma separate list of modules to exclude")
    print("  -d       Enable verbose debug logging")
    print("  -s       Clixon socket path")
    print("  -p       Pidfile for Python server")
    print("  -F       Run in foreground")
    print("  -P       Prettyprint XML")
    print("  -l       <s|o> Log on (s)yslog, std(o)ut")
    print("  -h       This!")

    sys.exit(0)


def kill(pidfile: str) -> None:
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

    sys.exit(0)


def parse_config(configfile: str, argname: Optional[bool] = "") -> tuple:
    """
    Parse configuration file.
    :param configfile: Configuration file
    :param argname: Argument name
    :return: Tuple with configuration
    """

    # Jupyter sucks
    if "jupyter" in configfile:
        if argname == "sockpath":
            print("Looks like you are running this from Jupyter.")
            print(
                "I'll fall back to the default configuration file since Jupyter messes with sys.argv.")
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


def parse_args(argname: str = None) -> tuple:
    """
    Parse command line arguments.
    :param argname: Argument name
    :return: Tuple with configuration
    """
    global logger

    sockpath = "/usr/local/var/controller.sock"
    pidfile = "/tmp/clixon_server.pid"
    modulepaths = ["/usr/local/share/clixon/controller/modules"]
    modulefilter = ""
    foreground = False
    pp = False
    configfile = None
    log = "s"
    debug = False
    kill_daemon = False

    try:
        opts, args = getopt.getopt(sys.argv[1:], "ds:e:p:m:FzPf:l:")
    except getopt.GetoptError as e:
        usage(err=e)

    for opt, arg in opts:
        if opt == "-f":
            if not os.path.exists(arg):
                usage(err=f"Configuration file {arg} does not exist")
            configfile = arg
        elif opt == "-d":
            debug = True
        elif opt == "-s":
            sockpath = arg
        elif opt == "-e":
            if opt == "" or opt == "-f":
                usage(err="No module filter specified")
            modulefilter = arg
        elif opt == "-p":
            pidfile = arg
        elif opt == "-m":
            if not os.path.exists(arg):
                usage(err=f"Module path {arg} does not exist")
            modulepaths.append(arg)
        elif opt == "-F":
            foreground = True
        elif opt == "-z":
            kill_daemon = True
        elif opt == "-P":
            pp = True
        elif opt == "-l":
            if arg not in ["s", "e", "o"]:
                usage(err=f"Invalid logging option {arg}")
            log = arg
        else:
            usage()

    if kill_daemon:
        kill(pidfile)

    if configfile:
        sockpath, conf_mpath, modulefilter, pidfile = parse_config(
            configfile, argname)
        modulepaths.extend(conf_mpath)

    if argname:
        return locals()[argname]

    return (sockpath, modulepaths, modulefilter, pidfile, foreground, pp,
            log, debug)
