from clixon.element import Element
import string
import random
from clixon.parser import parse_string, dump_string

xmlstr_1 = """<rpc-reply xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"><data><table xmlns="urn:example:clixon"><parameter><name>name1</name><value>value1</value></parameter><parameter><name>name2</name><value>value2</value></parameter><parameter><name>name3</name><value>value3</value></parameter></table></data></rpc-reply>"""

xmlstr_2 = """<rpc-reply xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"><data><table xmlns="urn:example:clixon"><parameter><name>name1</name><value>value1</value></parameter><parameter><name>name2</name><value>value2</value></parameter><parameter><name>name3</name><value>value3</value></parameter></table></data><foo-bar xmlns="foo:bar:test:1">test data</foo-bar></rpc-reply>"""


def test_to_obj_and_back():
    """
    Test that an XML string can be parsed and dumped back to XML.
    """

    root = parse_string(xmlstr_1)

    assert root.dumps() == xmlstr_1


def test_add_node():
    """
    Test that a node can be added.
    """

    root = parse_string(xmlstr_1)
    root.rpc_reply.create(
        "foo-bar", {"xmlns": "foo:bar:test:1"}, cdata="test data")


def test_del_node():
    """
    Test that a node can be deleted.
    """

    root = parse_string(xmlstr_2)
    root.rpc_reply.delete("foo-bar")

    assert root.dumps() == xmlstr_1


def test_repr_0():
    """
    Test that the first element is returned from object representation.
    """

    root = parse_string(xmlstr_1)

    assert root.rpc_reply.data.table.parameter[0].name.cdata == "name1"


def test_repr_1():
    """
    Test that the second element is returned from object representation.
    """

    root = parse_string(xmlstr_1)

    assert root.rpc_reply.data.table.parameter[1].name.cdata == "name2"


def test_repr_2():
    """
    Test that the last element is returned from object representation.
    """

    root = parse_string(xmlstr_1)

    assert root.rpc_reply.data.table.parameter[2].name.cdata == "name3"


def test_html_encoding():
    """
    Test that HTML encoding is preserved and CDATA is intact.
    """

    xmlstr0 = """<description>&lt; * &gt;</description>"""
    xmlstr1 = """<description>&lt;test&gt;</description>"""
    xmlstr2 = """<description>&lt;*&gt;</description>"""
    xmlstr3 = """<description>asd &lt;*&gt; asd</description>"""
    xmlstr4 = """<description>&lt;*&gt; asd &amp; test&amp;asd</description>"""
    xmlstr5 = """<description>"'&lt;*&gt;&amp;'"</description>"""
    xmlstr6 = """<description>&lt;*&gt; asd &amp; test&amp;asd</description>"""

    root = parse_string(xmlstr0)

    assert root.dumps() == xmlstr0

    root = parse_string(xmlstr1)

    assert root.dumps() == xmlstr1

    root = parse_string(xmlstr2)

    assert root.dumps() == xmlstr2

    root = parse_string(xmlstr3)

    assert root.dumps() == xmlstr3

    root = parse_string(xmlstr4)

    assert root.dumps() == xmlstr4

    root = parse_string(xmlstr5)

    assert root.dumps() == xmlstr5


def test_decode_all_characters():
    """
    Test that all characters are decoded correctly.
    """

    xmlstr6 = """<str>0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!";#$%&amp;';()*+,-./:;&lt;=;&gt;?@[\\]^_`{|}~</str>"""

    root = parse_string(xmlstr6)

    assert root.dumps() == xmlstr6


def test_strip():
    """
    Test that leading and trailing whitespace is stripped from cdata
    """

    xmlstr0 = """<description>  test  </description>"""
    xmlstr1 = """<description>test</description>"""
    xmlstr2 = """      <description>   test   </description>   """
    xmlstr2_res = """<description>   test   </description>"""
    xmlstr3 = """<description>  test   test   test</description>"""

    root = parse_string(xmlstr0)

    assert root.dumps() == xmlstr0

    root = parse_string(xmlstr1)

    assert root.dumps() == xmlstr1

    root = parse_string(xmlstr2)

    assert root.dumps() == xmlstr2_res

    root = parse_string(xmlstr3)

    assert root.dumps() == xmlstr3


def test_prettyprint():
    """
    Test that prettyprint works.
    """

    xmlstr_1 = """<rpc-reply xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"><data><table xmlns="urn:example:clixon"><parameter><name>name1</name><value>value1</value></parameter><parameter><name>name2</name><value>value2</value></parameter><parameter><name>name3</name><value>value3</value></parameter></table></data></rpc-reply>"""

    xmlstr1_pp = """\n<?xml version="1.0" ?>\n<rpc-reply xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">\n\t<data>\n\t\t<table xmlns="urn:example:clixon">\n\t\t\t<parameter>\n\t\t\t\t<name>name1</name>\n\t\t\t\t<value>value1</value>\n\t\t\t</parameter>\n\t\t\t<parameter>\n\t\t\t\t<name>name2</name>\n\t\t\t\t<value>value2</value>\n\t\t\t</parameter>\n\t\t\t<parameter>\n\t\t\t\t<name>name3</name>\n\t\t\t\t<value>value3</value>\n\t\t\t</parameter>\n\t\t</table>\n\t</data>\n</rpc-reply>\n"""

    assert dump_string(xmlstr_1) == xmlstr_1

    assert dump_string(xmlstr_1, pp=True) == xmlstr1_pp
