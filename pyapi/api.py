import sys
import xml.etree.ElementTree as ET

from pyapi.client import connect, read, send
from pyapi.parser import XMLNS, clicon_sock, ping, show_configuration


class ClixonApi():
    def __init__(self, sockpath=None, configfile=None):
        """
        Class for talking with Clixon using NETCONF.
        """

        # Establish socket connection, there are no reason for us to continue
        # if this step fails.
        if configfile:
            sockpath = clicon_sock(configfile)

        if not sockpath:
            print("Fatal! No path to the Clixon socket.")
            sys.exit(-1)

        self.__sock = connect(sockpath)

        # Issue a ping over NETCONF once the socket is created.
        if not self.__ping():
            print("Fatal! Failed to send ping message.")
            sys.exit(-1)

    def __ping(self):
        """
        NETCONF ping message to verify we have a working connection.
        """
        send(self.__sock, ping())
        res = read(self.__sock)

        root = ET.fromstring(res)
        if root.findall(f"{XMLNS}ok"):
            return True

        return False

    def show_configuration(self, as_dict=False, source="candidate"):
        send(self.__sock, show_configuration())
        res = read(self.__sock)

        return res

    def set(self, xpath, value):
        pass
