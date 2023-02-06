import getopt
import logging
import sys

from clixon.log import get_logger


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
    print("  -h       This!")

    sys.exit(0)


logger = get_logger()


def parse_args():
    sockpath = "/usr/local/var/controller.sock"
    pidfile = "/tmp/clixon_pyserver.pid"
    modulepath = "./modules/"
    modulefilter = ""

    try:
        opts, args = getopt.getopt(sys.argv[1:], "ds:f:p:m:")
    except getopt.GetoptError as e:
        usage(err=e)

    for opt, arg in opts:
        if opt == "-d":
            logger.setLevel(logging.DEBUG)
        elif opt == "-s":
            sockpath = arg
        elif opt == "-f":
            modulefilter = arg
        elif opt == "-p":
            pidfile = arg
        elif opt == "-m":
            modulepath = arg
        else:
            print(opt)
            usage()

    return sockpath, modulepath, modulefilter, pidfile
