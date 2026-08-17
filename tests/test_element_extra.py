import json

import pytest
import yaml

from clixon.element import Element
from clixon.parser import parse_string

XML = (
    "<config><devices><device><name>r1</name><enabled>true</enabled></device>"
    "<device><name>r2</name></device></devices></config>"
)


def config():
    """
    Return a parsed configuration.
    """

    return parse_string(XML)


def test_origname():
    """
    Test that the original name of an element is kept.
    """

    element = Element("service-name")

    assert element.origname() == "service-name"
    assert element.get_name() == "service_name"


def test_origname_without_name():
    """
    Test that an element without an original name falls back to its name.
    """

    element = Element("foo")
    element._origname = ""

    assert element.origname() == "foo"


def test_is_root():
    """
    Test that an element can be marked as root.
    """

    element = Element("config")
    element.is_root(True)

    assert element._is_root is True
    assert bool(element) is True


def test_create_with_element():
    """
    Test that an already created element can be added.
    """

    root = Element("config")
    child = Element("device")
    root.create("ignored", element=child)

    assert root.get_elements() == [child]


def test_rename():
    """
    Test that an element can be renamed.
    """

    element = Element("device")
    element.rename("interface", "interface")

    assert element.get_name() == "interface"
    assert element.origname() == "interface"


def test_replace():
    """
    Test that an element of a given name is replaced by another one.
    """

    root = config()
    replacement = Element("device")
    replacement.create("name", data="r3")

    root.config.devices.replace("device", replacement)

    assert [str(d.name) for d in root.config.devices.device] == ["r2", "r3"]


def test_delete_by_element():
    """
    Test that an element can be deleted by identity.
    """

    root = config()
    first = root.config.devices.get_elements("device")[0]

    root.config.devices.delete(element=first)

    assert [str(d.name) for d in root.config.devices.device] == ["r2"]


def test_delete_itself():
    """
    Test that an element deletes itself from its parent.
    """

    root = config()
    root.config.devices.get_elements("device")[0].delete()

    assert [str(d.name) for d in root.config.devices.device] == ["r2"]


def test_delete_all():
    """
    Test that all the children of an element can be deleted.
    """

    root = config()
    root.config.devices.delete("*")

    assert root.config.devices.get_elements() == []


def test_attributes():
    """
    Test that the attributes of an element are read and updated.
    """

    element = Element("device", attributes={"a": "1"})

    assert element.get_attributes("a") == "1"
    assert element["a"] == "1"
    assert element.get_attributes_str() == ' a="1"'

    element.update_attributes({"b": "2"})

    assert element.get_attributes() == {"a": "1", "b": "2"}

    element.set_attributes({"c": "3"})

    assert element.get_attributes() == {"c": "3"}


def test_get_elements_by_data():
    """
    Test that elements can be filtered on their data.
    """

    root = config()
    found = root.get_elements(name="name", data="r2", recursive=True)

    assert len(found) == 1
    assert str(found[0]) == "r2"


def test_get_data_typecast():
    """
    Test that the data of an element can be cast.
    """

    element = Element("port", data="830")

    assert element.get_data() == "830"
    assert element.get_data(typecast=int) == 830


def test_set_data():
    """
    Test that the data of an element is set and marks it as modified.
    """

    element = Element("name")
    element.set_data("r1", modified=True)

    assert str(element) == "r1"
    assert element.get_modified() is True


def test_set_modified():
    """
    Test that an element can be marked as modified.
    """

    element = Element("name")

    assert element.set_modified(True) is True
    assert element.get_modified() is True


def test_find_and_findall():
    """
    Test that elements are found by name.
    """

    root = config()

    assert root.config.devices.find("device") is not None
    assert root.find("nosuch") is None
    assert len(root.findall("device")) == 2


def test_find_modified():
    """
    Test that the modified elements are found.
    """

    root = config()

    assert root.find_modified() != []


def test_parent_and_parents():
    """
    Test that the parents of an element are walked.
    """

    root = config()
    name = root.config.devices.device[0].name

    assert name.parent().get_name() == "device"
    assert [p.get_name() for p in name.parents()][:3] == [
        "device",
        "devices",
        "config",
    ]


def test_dumps_pp():
    """
    Test that an element is prettyprinted.
    """

    output = config().dumps_pp()

    assert "<config>" in output
    assert "\n" in output


def test_dumpj():
    """
    Test that an element is dumped as JSON.
    """

    data = json.loads(config().dumpj())

    assert data[0]["config"]["devices"]["device"][0]["name"] == "r1"


def test_dumpy():
    """
    Test that an element is dumped as YAML.
    """

    data = yaml.safe_load(config().dumpy())

    assert data[0]["config"]["devices"]["device"][1]["name"] == "r2"


def test_getattr_single_and_many():
    """
    Test that one element is returned as itself and several as a list.
    """

    root = config()

    assert root.config.devices.device[0].name == "r1"
    assert len(root.config.devices.device) == 2
    assert root.config.devices.get_elements("device")[1].name == "r2"


def test_getattr_missing():
    """
    Test that an element which is not there is an attribute error.
    """

    with pytest.raises(AttributeError):
        config().config.nosuch


def test_dunder_helpers():
    """
    Test the helpers an element has for being used as an object.
    """

    root = config()
    devices = root.config.devices

    assert len(devices) == 2
    assert "device" in devices
    assert dir(devices) == ["device", "device"]
    assert repr(root.config.devices.device[0].name) == "r1"
    assert repr(devices) == "devices"
    assert list(iter(devices)) == [devices]
    assert devices.__hasattribute__("device") is True
    assert devices.__hasattribute__("nosuch") is False
