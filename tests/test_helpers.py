from clixon.element import Element
from clixon.helpers import set_creator_attributes


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
