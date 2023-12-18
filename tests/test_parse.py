from clixon.parser import parse_string

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
    Test that html encoding is preserved and CDATA is intact.
    """

    xmlstr0 = """<description>&lt; * &gt;</description>"""
    xmlstr1 = """<description>&lt;test&gt;</description>"""
    xmlstr2 = """<description>&lt;*&gt;</description>"""
    xmlstr3 = """<description>asd &lt;*&gt; asd</description>"""

    root = parse_string(xmlstr0)

    assert root.dumps() == xmlstr0

    root = parse_string(xmlstr1)

    assert root.dumps() == xmlstr1

    root = parse_string(xmlstr2)

    assert root.dumps() == xmlstr2

    root = parse_string(xmlstr3)

    assert root.dumps() == xmlstr3


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
