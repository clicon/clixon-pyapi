import pytest
from clixon.element import Element
from clixon.helpers import set_creator_attributes, get_value, get_path
from clixon.parser import parse_string


def test_set_creator_attributes():
    """
    Test that set_creator_attributes works as expected.
    """

    root = Element("root")
    root.create("test")
    root.test.create("bar")

    set_creator_attributes(root.test, "test", instance_name="keff")

    xmlstr = """<test cl:creator="test[service-name='keff']" nc:operation="create" xmlns:cl="http://clicon.org/lib"><bar/></test>"""

    assert root.dumps() == xmlstr

    set_creator_attributes(root.test, "test", "keff", "create")

    xmlstr = """<test cl:creator="test[service-name='keff']" nc:operation="create" xmlns:cl="http://clicon.org/lib"><bar/></test>"""

    assert root.dumps() == xmlstr


def test_set_creator_attributes_update():
    """
    Test that set_creator_attributes works and existing attributes are kept.
    """

    root = Element("root")
    root.create("test", attributes={"test": "foo"})
    root.test.create("bar")

    set_creator_attributes(root.test, "test", "keff", "create")

    xmlstr = """<test cl:creator="test[service-name='keff']" nc:operation="create" xmlns:cl="http://clicon.org/lib" test="foo"><bar/></test>"""

    assert root.dumps() == xmlstr


def test_get_value():
    """
    Test that get_value works as expected.
    """

    xmlstr_1 = """<rpc-reply xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"><data><table xmlns="urn:example:clixon"><parameter><name>name1</name><value>value1</value></parameter><parameter><name>name2</name><value>value2</value></parameter><parameter><name>name3</name><value>value3</value></parameter></table></data></rpc-reply>"""

    root = parse_string(xmlstr_1)

    value1_path = get_path(
        root, "/rpc-reply/data/table/parameter[name='name1']")

    value1 = get_value(value1_path, "value")

    assert value1 == "value1"

    value1 = get_value(value1_path, "valueX", default="value1")

    assert value1 == "value1"

    with pytest.raises(Exception):
        get_value(value1_path, "valueX", required=True)
