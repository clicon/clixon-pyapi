import re
from typing import Optional
from xml.dom import minidom
from xml.sax import handler
from xml.sax.expatreader import ExpatParser

from clixon.element import Element
from clixon.helpers import get_path

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO


class Handler(handler.ContentHandler):
    def __init__(self):
        """
        Initialize the handler.

        :return: None
        :rtype: None
        """

        self.root = Element(None, None)
        self.root.is_root = True
        self.elements = []
        self.last_cdata = ""

    def startElement(self, name: str, attributes: str) -> None:
        """
        Start a new element.

        :param name: Name of the element.
        :type name: str
        :param attributes: Attributes of the element.
        :type attributes: str
        :return: None
        :rtype: None

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

        :param name: Name of the element.
        :type name: str
        :return: None
        :rtype: None

        """

        self.elements.pop()
        self.last_cdata = ""

    def characters(self, cdata: str) -> None:
        """
        Add character data to the current element.

        :param cdata: Character data.
        :type cdata: str
        :return: None
        :rtype: None

        """

        if cdata.startswith("\n"):
            cdata = cdata[1:]

        if cdata.endswith("\n"):
            cdata = cdata[:-1]

        if cdata.isspace() and self.last_cdata == "":
            return

        # Escape special characters
        cdata = cdata.replace("&", "&amp;").replace(
            ">", "&gt;").replace("<", "&lt;")

        self.elements[-1].cdata += cdata
        self.last_cdata = cdata


def parse_file(filename: str) -> Element:
    """
    Parse an XML file and return the root element.

    :param filename: Name of the file.
    :type filename: str
    :return: Root element.
    :rtype: Element

    """

    parser = ExpatParser()
    sax_handler = Handler()
    parser.setContentHandler(sax_handler)
    parser.parse(filename)

    return sax_handler.root


def parse_string(xmlstr: str):
    """
    Parse an XML string and return the root element.

    :param xmlstr: XML string.
    :type xmlstr: str
    :return: Root element.
    :rtype: Element

    """

    # If outstr endwith 0x00 (null char), remove it
    if xmlstr.endswith("\x00"):
        xmlstr = xmlstr[:-1]

    parser = ExpatParser()
    sax_handler = Handler()
    parser.setContentHandler(sax_handler)
    parser.parse(StringIO(xmlstr))

    return sax_handler.root


def dump_string(xmlstr: str, pp: Optional[bool] = False) -> str:
    """
    Dump an XML string and return the root element.

    :param xmlstr: XML string.
    :type xmlstr: str
    :param pp: Pretty print.
    :type pp: bool
    :return: Root element.
    :rtype: Element

    """

    if isinstance(xmlstr, bytes):
        outstr = str(xmlstr.decode()).strip()
    else:
        outstr = xmlstr.strip()

    # If outstr endwith 0x00 (null char), remove it
    if outstr.endswith("\x00"):
        outstr = outstr[:-1]

    if pp:
        dom = minidom.parseString(outstr)
        outstr = "\n" + dom.toprettyxml()

    return outstr


def parse_template(template: str, **kwargs: dict) -> str:
    """
    Parse a template and return the result.

    :param template: Template string.
    :type template: str
    :param kwargs: Variables.
    :type kwargs: dict
    :return: Result.
    :rtype: str

    """

    vars_re = re.compile(
        r"\${([a-zA-Z0-9_\-]+)}|\{\{([a-zA-Z0-9_\-]+)\}\}", re.MULTILINE)
    matches = re.findall(vars_re, template)
    vars_list = [match[0] if match[0] else match[1] for match in matches]

    for var in vars_list:
        var_orig = var
        var = var.replace("-", "_")

        if var not in kwargs:
            raise ValueError(f"Missing variable: {var}")

        if kwargs[var] != str:
            kwargs[var] = str(kwargs[var])

        template = template.replace("{{" + var_orig + "}}", kwargs[var])
        template = template.replace("${" + var_orig + "}", kwargs[var])

    return parse_string(template)


def parse_template_file(filename: str, **kwargs: dict) -> str:
    """
    Parse a template file and return the result.

    :param filename: Template file.
    :type filename: str
    :param kwargs: Variables.
    :type kwargs: dict
    :return: Result.
    :type: str

    """

    try:
        with open(filename, "r") as fd:
            template = fd.read()
    except IOError:
        raise IOError(f"Could not open template file: {filename}")

    return parse_template(template, **kwargs)


def parse_template_config(root: Element, name: str, **kwargs) -> str:
    """
    Parse a template from configuratino tree and return the result.

    :param root: Root of the configuration tree.
    :type root: Element
    :param name: Name of the template.
    :type name: str
    :param kwargs: Variables.
    :type kwargs: dict
    :return: Result.
    :rtype: str

    """

    template_root = get_path(root, f"/devices/template[name='{name}']")

    if not template_root:
        raise ValueError(f"Template {name} not found")

    template_str = template_root.config.configuration.dumps()

    return parse_template(template_str, **kwargs)
