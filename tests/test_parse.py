from pyapi.parser import parse_string

xmlstr_1 = """<rpc-reply xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"><data><table xmlns="urn:example:clixon"><parameter><name>name1</name><value>value1</value></parameter><parameter><name>name2</name><value>value2</value></parameter><parameter><name>name3</name><value>value3</value></parameter></table></data></rpc-reply>"""

xmlstr_2 = """<rpc-reply xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"><data><table xmlns="urn:example:clixon"><parameter><name>name1</name><value>value1</value></parameter><parameter><name>name2</name><value>value2</value></parameter><parameter><name>name3</name><value>value3</value></parameter></table></data><foo-bar xmlns="foo:bar:test:1">test data</foo-bar></rpc-reply>"""


def test_to_obj_and_back():
    # Convert XML to Python objects and back to XML again. In the end we should
    # have an XML string identical to the one we used from the beginning.
    root = parse_string(xmlstr_1)

    assert root.dumps() == xmlstr_1


def test_add_node():
    root = parse_string(xmlstr_1)
    root.rpc_reply.create(
        "foo_bar", {"xmlns": "foo:bar:test:1"}, cname="test data")


def test_del_node():
    root = parse_string(xmlstr_2)
    root.rpc_reply.delete("foo_bar")

    assert root.dumps() == xmlstr_1


def test_repr():
    root = parse_string(xmlstr_1)

    assert root.rpc_reply.data.table.parameter[0].name.get_cdata() == "name1"
    assert root.rpc_reply.data.table.parameter[1].name.get_cdata() == "name2"
    assert root.rpc_reply.data.table.parameter[2].name.get_cdata() == "name3"
