import re
from typing import Optional
from xml.dom import minidom
from xml.sax import handler
from xml.sax.expatreader import ExpatParser

from clixon.element import Element

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO


class Handler(handler.ContentHandler):
    def __init__(self):
        """
        Initialize the handler.
        """

        self.root = Element(None, None)
        self.root.is_root = True
        self.elements = []

    def startElement(self, name: str, attributes: str) -> None:
        """
        Start a new element.
        """

        attrs = dict()
        for k, v in attributes.items():
            attrs[k] = v

        element = Element(name, attrs)

        if len(self.elements) > 0:
            self.elements[-1].add(element)
        else:
            self.root.add(element)
        self.elements.append(element)

    def endElement(self, name: str) -> None:
        """
        End the current element.
        """

        self.elements.pop()

    def characters(self, cdata: str) -> None:
        """
        Add character data to the current element.
        """

        self.elements[-1].cdata = cdata


def parse_file(filename: str) -> Element:
    """
    Parse an XML file and return the root element.
    """

    parser = ExpatParser()
    sax_handler = Handler()
    parser.setContentHandler(sax_handler)
    parser.parse(filename)

    return sax_handler.root


def parse_string(xmlstr: str):
    """
    Parse an XML string and return the root element.
    """

    parser = ExpatParser()
    sax_handler = Handler()
    parser.setContentHandler(sax_handler)
    parser.parse(StringIO(xmlstr))

    return sax_handler.root


def dump_string(xmlstr: str, pp: Optional[bool] = False) -> str:
    """
    Dump an XML string and return the root element.
    """

    if isinstance(xmlstr, bytes):
        outstr = str(xmlstr.decode()).strip()
    else:
        outstr = xmlstr.strip()

    if pp:
        dom = minidom.parseString(outstr)
        outstr = "\n" + dom.toprettyxml()

    return outstr


def parse_template(template: str, **kwargs: dict) -> str:
    """
    Parse a template and return the result.
    """

    vars_re = re.compile(r"{{(\w+)}}", re.MULTILINE)
    vars_list = re.findall(vars_re, template)

    for var in vars_list:
        if var not in kwargs:
            raise ValueError("Missing variable: {}".format(var))
        if kwargs[var] != str:
            kwargs[var] = str(kwargs[var])
        template = template.replace("{{" + var + "}}", kwargs[var])

    return parse_string(template)


def parse_template_file(filename: str, **kwargs: dict) -> str:
    """
    Parse a template file and return the result.
    """

    with open(filename, "r") as fd:
        template = fd.read()

    return parse_template(template, **kwargs)
