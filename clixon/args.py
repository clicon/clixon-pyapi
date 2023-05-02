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
    print("  -m       Modules path")
    print("  -f       Comma separate list of modules to exclude")
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
    except Exception as e:
        logger.error("Failed to kill daemon")


def parse_args():
    sockpath = "/usr/local/var/controller.sock"
    pidfile = "/tmp/clixon_pyserver.pid"
    modulepath = "./modules/"
    modulefilter = ""
    foreground = False
    pp = False

    try:
        opts, args = getopt.getopt(sys.argv[1:], "ds:f:p:m:FzP")
    except getopt.GetoptError as e:
        usage(err=e)

    for opt, arg in opts:
        if opt == "-d":
            logger.setLevel(logging.DEBUG)
        elif opt == "-s":
            sockpath = arg
        elif opt == "-f":
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

    return sockpath, modulepath, modulefilter, pidfile, foreground, pp
