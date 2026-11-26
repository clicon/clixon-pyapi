from unittest.mock import MagicMock

import pytest

import clixon.clixon as clixon_module
from clixon import netconf
from clixon.clixon import Clixon
from clixon.element import Element
from clixon.helpers import get_path, set_creator_attributes
from clixon.parser import parse_string, parse_template

REPLY = (
    '<rpc-reply xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"><data>'
    '<services xmlns="http://clicon.org/controller">'
    "<test><service-name>a</service-name></test>"
    "</services>"
    '<devices xmlns="http://clicon.org/controller">'
    "<device><name>r0</name><enabled>true</enabled><config><configuration>"
    "<interfaces>"
    "<interface><name>ge-0/0/0</name><description>d0</description>"
    "<unit><name>0</name></unit></interface>"
    "<interface><name>ge-0/0/1</name><description>d1</description>"
    "<unit><name>0</name></unit></interface>"
    "</interfaces>"
    "<system><host-name>r0</host-name></system>"
    "</configuration></config></device>"
    "<device><name>r1</name><enabled>true</enabled><config><configuration>"
    "<system><host-name>r1</host-name></system>"
    "</configuration></config></device>"
    "</devices>"
    "</data></rpc-reply>"
)

DEVICES_START = '<devices xmlns="http://clicon.org/controller">'
R0_START = "<device><name>r0</name><enabled>true</enabled><config><configuration>"
R0_END = "</configuration></config></device>"


def get_root():
    return parse_string(REPLY).rpc_reply.data


def configuration(root, name="r0"):
    return get_path(root, f"/devices/device[name='{name}']/config/configuration")


def modified_devices(root):
    return [d.name.get_data() for d in root.devices.device if d.find_modified()]


def pruned_config(root):
    rpc = netconf.rpc_config_set(root, prune=True)

    return rpc.rpc.edit_config.config.dumps()


# Modification tracking


def test_parsed_tree_is_not_modified():
    """
    A tree from a get-config reply has no modifications.
    """

    assert modified_devices(get_root()) == []


def test_set_data_is_tracked():
    root = get_root()
    configuration(root).system.host_name.set_data("x")

    assert modified_devices(root) == ["r0"]


def test_cdata_assignment_is_tracked():
    root = get_root()
    configuration(root).system.host_name.cdata = "x"

    assert modified_devices(root) == ["r0"]
    assert configuration(root).system.host_name._modified is True


def test_create_marks_new_element_not_parent():
    root = get_root()
    system = configuration(root).system
    new = system.create("domain-name", data="example.com")

    assert new._modified is True
    assert system._modified is False
    assert modified_devices(root) == ["r0"]


def test_create_unmodified():
    root = get_root()
    new = configuration(root).system.create("domain-name", modified=False)

    assert new._modified is False
    assert modified_devices(root) == []


def test_create_new_element_cdata_is_set():
    element = Element("root")
    child = element.create("a", data="x")
    other = element.create("b", cdata="y")

    assert child.get_data() == "x"
    assert other.get_data() == "y"


def test_add_marks_element():
    root = get_root()
    configuration(root).add(Element("snmp", data="public"))

    assert modified_devices(root) == ["r0"]


def test_add_unmodified_leaves_status():
    element = Element("a")
    element._modified = True
    Element("root").add(element, modified=False)

    assert element._modified is True

    element = Element("b")
    Element("root").add(element, modified=False)

    assert element._modified is False


def test_add_inner_template_element_is_tracked():
    """
    Adding an element from inside a parsed template is detected, only the
    template's top element is marked by the parser.
    """

    root = get_root()
    template = parse_template(
        "<policy-options><ps><name>${NAME}</name></ps></policy-options>", NAME="p1"
    )
    configuration(root).add(template.policy_options.ps)

    assert modified_devices(root) == ["r0"]


def test_update_attributes_is_tracked():
    root = get_root()
    configuration(root).system.update_attributes({"nc:operation": "replace"})

    assert modified_devices(root) == ["r0"]


def test_set_creator_attributes_is_tracked():
    root = get_root()
    set_creator_attributes(configuration(root).system, "test", "a")

    assert modified_devices(root) == ["r0"]


def test_replace_is_tracked():
    root = get_root()
    configuration(root).replace("system", Element("system"))

    assert modified_devices(root) == ["r0"]


def test_set_data_unmodified():
    root = get_root()
    configuration(root).system.host_name.set_data("x", modified=False)

    assert modified_devices(root) == []


# Element.prune()


def test_prune_unmodified_returns_none():
    assert get_root().prune() is None


def test_prune_modified_element_is_returned_whole():
    root = get_root()
    system = configuration(root).system
    system.set_attributes({"a": "1"})

    assert system.prune() is system


def test_prune_keeps_path_and_list_keys():
    root = get_root()
    configuration(root).interfaces.interface[1].description.set_data("new")

    assert pruned_config(root) == (
        DEVICES_START
        + R0_START
        + "<interfaces><interface><name>ge-0/0/1</name>"
        + "<description>new</description></interface></interfaces>"
        + R0_END
        + "</devices>"
    )


def test_prune_created_element_is_sent_whole():
    root = get_root()
    snmp = configuration(root).create("snmp")
    snmp.create("community").create("name", data="public")

    assert pruned_config(root) == (
        DEVICES_START
        + R0_START
        + "<snmp><community><name>public</name></community></snmp>"
        + R0_END
        + "</devices>"
    )


def test_prune_keeps_document_order():
    root = get_root()
    configuration(root).system.host_name.set_data("x")
    configuration(root).interfaces.interface[0].description.set_data("y")

    assert pruned_config(root) == (
        DEVICES_START
        + R0_START
        + "<interfaces><interface><name>ge-0/0/0</name>"
        + "<description>y</description></interface></interfaces>"
        + "<system><host-name>x</host-name></system>"
        + R0_END
        + "</devices>"
    )


def test_prune_multiple_devices_and_services():
    root = get_root()
    configuration(root, "r1").system.host_name.set_data("x")
    root.services.test.create("description", data="svc")

    assert pruned_config(root) == (
        '<services xmlns="http://clicon.org/controller">'
        + "<test><service-name>a</service-name><description>svc</description>"
        + "</test></services>"
        + DEVICES_START
        + "<device><name>r1</name><enabled>true</enabled><config><configuration>"
        + "<system><host-name>x</host-name></system>"
        + R0_END
        + "</devices>"
    )


def test_prune_does_not_change_original_tree():
    root = get_root()
    before = root.dumps()
    configuration(root).system.host_name.set_data("x")
    parents = [(e, e._parent) for e in configuration(root).get_elements()]
    netconf.rpc_config_set(root, prune=True)

    assert root.dumps() == before.replace(
        "<host-name>r0</host-name>", "<host-name>x</host-name>"
    )
    assert all(e._parent is p for e, p in parents)
    assert root.devices._parent is not None


def test_prune_nothing_modified_gives_empty_config():
    rpc = netconf.rpc_config_set(get_root(), prune=True)

    assert rpc.rpc.edit_config.config.get_elements() == []


def test_prune_adds_devices_namespace():
    config = Element("config")
    config.create("devices").create("device").create("name", data="foo")
    rpc = netconf.rpc_config_set(config, prune=True)

    assert rpc.rpc.edit_config.config.dumps() == (
        DEVICES_START + "<device><name>foo</name></device></devices>"
    )
    assert config.devices.attributes == {}


def test_prune_set_root_with_parsed_tree_sends_all():
    """
    A tree parsed from a string is marked as modified at the top, so it is
    sent whole.
    """

    config = parse_string("<services><a><b>1</b></a></services>")
    rpc = netconf.rpc_config_set(config, prune=True)

    assert rpc.rpc.edit_config.config.dumps() == "<services><a><b>1</b></a></services>"


def test_no_prune_sends_whole_device():
    root = get_root()
    configuration(root).system.host_name.set_data("x")
    config = netconf.rpc_config_set(root).rpc.edit_config.config.dumps()

    assert "<description>d0</description>" in config
    assert "<host-name>r1</host-name>" not in config


# Clixon


@pytest.fixture
def backend(monkeypatch):
    """
    Replace the socket calls in clixon.clixon, record what is sent and answer
    get-config with REPLY and everything else with ok.
    """

    sent = []

    def send(sock, data, pp=False):
        if isinstance(data, Element):
            data = data.dumps()
        sent.append(data)

    def read(sock, pp=False, standalone=False):
        if "<get-config" in sent[-1]:
            return REPLY
        return '<rpc-reply xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"><ok/></rpc-reply>'

    monkeypatch.setattr(clixon_module, "send", send)
    monkeypatch.setattr(clixon_module, "read", read)

    return sent


def edit_configs(sent):
    return [s for s in sent if "<edit-config>" in s]


def test_clixon_prune_sends_only_change(backend):
    with Clixon(socket=MagicMock(), from_server=True, prune=True) as cd:
        root = cd.get_root()
        configuration(root).system.host_name.set_data("x")

    (edit,) = edit_configs(backend)

    assert "<host-name>x</host-name>" in edit
    assert "ge-0/0/0" not in edit
    assert "r1" not in edit
    assert "<services" not in edit


def test_clixon_prune_skips_unchanged(backend):
    with Clixon(socket=MagicMock(), from_server=True, prune=True) as cd:
        cd.get_root()

    assert edit_configs(backend) == []


def test_clixon_prune_skips_get_config_without_root(backend):
    with Clixon(socket=MagicMock(), from_server=True, prune=True):
        pass

    assert backend == []


def test_clixon_without_prune_sends_config(backend):
    with Clixon(socket=MagicMock(), from_server=True, prune=False) as cd:
        cd.get_root()

    (edit,) = edit_configs(backend)

    assert "<services" in edit


def test_clixon_set_root_prune(backend):
    cd = Clixon(socket=MagicMock(), from_server=True, prune=True)
    root = cd.get_root()
    cd.set_root(root)

    assert edit_configs(backend) == []

    configuration(root).system.host_name.set_data("x")
    cd.set_root(root)

    assert len(edit_configs(backend)) == 1
