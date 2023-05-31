import clixon.parser as parser
import getopt
import logging
import sys
import os
import signal

from clixon.log import get_logger

logger = get_logger()


def usage(err=""):
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
    print("  -h       This!")

    sys.exit(0)


def kill(pidfile):
    try:
        with open(pidfile) as fd:
            pid = int(fd.read())
            logger.info(f"Killing daemon with pid {pid}")
            os.kill(pid, signal.SIGTERM)
    except Exception:
        logger.error("Failed to kill daemon")


def parse_config(configfile):
    config = parser.parse_file(configfile)

    try:
        pyconfig = config.clixon_config.PYAPI
        clixon_config = config.clixon_config

        sockpath = clixon_config.CLICON_SOCK.cdata
        modulepath = pyconfig.PYAPI_MODULES.cdata
        modulefilter = pyconfig.PYAPI_MODULE_FILTER.cdata
        pidfile = pyconfig.PYAPI_PIDFILE.cdata
    except AttributeError as e:
        print(f"Could not parse confiuguration file: {e}")

        sys.exit(1)

    return sockpath, modulepath, modulefilter, pidfile


def parse_args():
    sockpath = "/usr/local/var/controller.sock"
    pidfile = "/tmp/clixon_pyserver.pid"
    modulepath = "./modules/"
    modulefilter = ""
    foreground = False
    pp = False
    configfile = None

    try:
        opts, args = getopt.getopt(sys.argv[1:], "ds:e:p:m:FzPf:")
    except getopt.GetoptError as e:
        usage(err=e)

    for opt, arg in opts:
        if opt == "-f":
            if not os.path.exists(arg):
                usage(err=f"Configuration file {arg} does not exist")
            configfile = arg
        elif opt == "-d":
            logger.setLevel(logging.DEBUG)
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
            modulepath = arg
        elif opt == "-F":
            foreground = True
        elif opt == "-z":
            kill(pidfile)
        elif opt == "-P":
            pp = True
        else:
            print(opt)
            usage()

    if configfile:
        sockpath, modulepath, modulefilter, pidfile = parse_config(configfile)

    return sockpath, modulepath, modulefilter, pidfile, foreground, pp
