import keyword
from xml.sax import handler
from xml.sax.expatreader import ExpatParser

from pyapi.element import Element

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO


class Handler(handler.ContentHandler):
    def __init__(self):
        self.root = Element(None, None)
        self.root.is_root = True
        self.elements = []

    def startElement(self, name, attributes):
        name = name.replace("-", "_")
        name = name.replace(".", "_")
        name = name.replace(":", "_")

        if keyword.iskeyword(name):
            name += "_"

        attrs = dict()
        for k, v in attributes.items():
            attrs[k] = v

        element = Element(name, attrs)

        if len(self.elements) > 0:
            self.elements[-1].add_child(element)
        else:
            self.root.add_child(element)
        self.elements.append(element)

    def endElement(self, name):
        self.elements.pop()

    def characters(self, cdata):
        self.elements[-1].add_cdata(cdata)


def parse_string(xmlstr):
    parser = ExpatParser()
    sax_handler = Handler()
    parser.setContentHandler(sax_handler)
    parser.parse(StringIO(xmlstr))

    return sax_handler.root
