from pyapi.parser import parse_string

xmlstr_1 = """<rpc-reply xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"><data><table xmlns="urn:example:clixon"><parameter><name>name1</name><value>value1</value></parameter><parameter><name>name2</name><value>value2</value></parameter><parameter><name>name3</name><value>value3</value></parameter></table></data></rpc-reply>"""

xmlstr_2 = """<rpc-reply xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"><data><table xmlns="urn:example:clixon"><parameter><name>name1</name><value>value1</value></parameter><parameter><name>name2</name><value>value2</value></parameter><parameter><name>name3</name><value>value3</value></parameter></table></data><foo-bar xmlns="foo:bar:test:1">test data</foo-bar></rpc-reply>"""


def test_to_obj_and_back():
    root = parse_string(xmlstr_1)

    assert root.dumps() == xmlstr_1


def test_add_node():
    root = parse_string(xmlstr_1)
    root.rpc_reply.create(
        "foo-bar", {"xmlns": "foo:bar:test:1"}, cdata="test data")


def test_del_node():
    root = parse_string(xmlstr_2)
    root.rpc_reply.delete("foo-bar")

    assert root.dumps() == xmlstr_1


def test_repr_0():
    root = parse_string(xmlstr_1)

    assert root.rpc_reply.data.table.parameter[0].name.cdata == "name1"


def test_repr_1():
    root = parse_string(xmlstr_1)

    assert root.rpc_reply.data.table.parameter[1].name.cdata == "name2"


def test_repr_2():
    root = parse_string(xmlstr_1)

    assert root.rpc_reply.data.table.parameter[2].name.cdata == "name3"
