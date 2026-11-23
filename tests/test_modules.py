from types import SimpleNamespace

import pytest

from clixon.element import mark_truncated
from clixon.modules import (
    get_module_root,
    get_service_xpaths,
    service_instance_xpath,
)
from clixon.parser import parse_string


SERVICE_XPATHS_REPLY = """<rpc-reply xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"><data><services xmlns="http://clicon.org/controller"><testA xmlns="urn:example:test"><service-name>foo</service-name><service-xpaths><xpath>/ctrl:devices/ctrl:device/ctrl:config</xpath><xpath>/ctrl:devices/ctrl:device/ctrl:name</xpath><xpath>/ctrl:devices/ctrl:device/ctrl:name</xpath></service-xpaths></testA></services></data></rpc-reply>"""

EMPTY_REPLY = """<rpc-reply xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"><data/></rpc-reply>"""


class FakeClixon:
    def __init__(self, lookup_reply):
        self.lookup_reply = lookup_reply
        self.calls = []

    def get_root(self, xpath="/", namespaces=None, with_defaults="report-all"):
        self.calls.append(
            {"xpath": xpath, "namespaces": namespaces, "with_defaults": with_defaults}
        )

        if "service-xpaths" in xpath:
            return parse_string(self.lookup_reply).rpc_reply.data

        return "ROOT"


def test_service_instance_xpath():
    """
    Test the xpath selecting a service instance.
    """

    assert (
        service_instance_xpath("testA", "foo")
        == "/ctrl:services/*[local-name()='testA'][*[local-name()='service-name']='foo']"
    )


def test_service_instance_xpath_prefixed_and_quoted():
    """
    Test that a service prefix is stripped and quotes are handled.
    """

    assert (
        service_instance_xpath("ex:testA", "it's")
        == "/ctrl:services/*[local-name()='testA'][*[local-name()='service-name']=\"it's\"]"
    )


def test_get_service_xpaths():
    """
    Test that configured service-xpaths are returned, including defaults.
    """

    cd = FakeClixon(SERVICE_XPATHS_REPLY)

    assert get_service_xpaths(cd, "testA", "foo") == [
        "/ctrl:devices/ctrl:device/ctrl:config",
        "/ctrl:devices/ctrl:device/ctrl:name",
    ]
    assert cd.calls[0]["with_defaults"] == "report-all"


def test_get_module_root_with_service_xpaths():
    """
    Test that service-xpaths are combined with the service instance.
    """

    cd = FakeClixon(SERVICE_XPATHS_REPLY)
    module = SimpleNamespace(
        SERVICE="testA",
        SERVICE_XPATH="/services/ignored",
        SERVICE_NAMESPACES={"ex": "urn:example:test"},
    )

    assert get_module_root(cd, module, "testA", "foo") == "ROOT"
    assert cd.calls[-1]["xpath"] == (
        "/ctrl:devices/ctrl:device/ctrl:config | "
        "/ctrl:devices/ctrl:device/ctrl:name | "
        + service_instance_xpath("testA", "foo")
    )
    assert cd.calls[-1]["namespaces"] == {"ex": "urn:example:test"}


def test_get_module_root_without_service_xpaths():
    """
    Test that the whole config is fetched when no service-xpaths are configured.
    """

    cd = FakeClixon(EMPTY_REPLY)
    module = SimpleNamespace(SERVICE="testA")

    get_module_root(cd, module, "testA", "foo")

    assert len(cd.calls) == 2
    assert cd.calls[-1]["xpath"] == "/"


def test_get_module_root_falls_back_to_service_xpath():
    """
    Test that SERVICE_XPATH is used when no service-xpaths are configured.
    """

    cd = FakeClixon(EMPTY_REPLY)
    module = SimpleNamespace(
        SERVICE="testA", SERVICE_XPATH="/services", SERVICE_NAMESPACES={}
    )

    get_module_root(cd, module, "testA", "foo")

    assert cd.calls[-1]["xpath"] == "/services"


def test_get_module_root_without_instance():
    """
    Test that no lookup is made when there is no service instance.
    """

    cd = FakeClixon(SERVICE_XPATHS_REPLY)
    module = SimpleNamespace(SERVICE="testA")

    get_module_root(cd, module, None, None)

    assert len(cd.calls) == 1
    assert cd.calls[0]["xpath"] == "/"


FULL_SERVICES_REPLY = """<rpc-reply xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"><data><services xmlns="http://clicon.org/controller"><testA xmlns="urn:example:test"><service-name>foo</service-name><peer><ip>10.0.0.1</ip><md5>secret</md5></peer></testA></services></data></rpc-reply>"""

# Depth 3: the services peer entry and device config are cut off
DEPTH_3_REPLY = """<rpc-reply xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"><data><devices xmlns="http://clicon.org/controller"><device><name>r1</name><config></config></device></devices><services xmlns="http://clicon.org/controller"><testA xmlns="urn:example:test"><service-name>foo</service-name><peer></peer></testA></services></data></rpc-reply>"""


class DepthFakeClixon:
    def __init__(self, depth_reply=DEPTH_3_REPLY):
        self.depth_reply = depth_reply
        self.calls = []

    def get_root(
        self, xpath="/", namespaces=None, with_defaults="report-all", depth=None
    ):
        self.calls.append({"xpath": xpath, "namespaces": namespaces, "depth": depth})

        if "service-xpaths" in xpath:
            return parse_string(EMPTY_REPLY).rpc_reply.data

        if xpath == "/services":
            return parse_string(FULL_SERVICES_REPLY).rpc_reply.data

        root = parse_string(self.depth_reply).rpc_reply.data
        mark_truncated(root, depth)

        return root


def test_get_module_root_with_service_depth():
    """
    Test that SERVICE_DEPTH limits the tree but /services is always complete.
    """

    cd = DepthFakeClixon()
    module = SimpleNamespace(SERVICE="testA", SERVICE_DEPTH=3)

    root = get_module_root(cd, module, "testA", "foo")

    # /services first, the depth-limited tree last since that one is written back
    assert cd.calls[-2] == {"xpath": "/services", "namespaces": None, "depth": None}
    assert cd.calls[-1] == {"xpath": "/", "namespaces": None, "depth": 3}

    assert len(root.get_elements("services")) == 1
    assert root.services.testA.peer.md5.get_data() == "secret"
    assert root.devices.device.name.get_data() == "r1"
    assert root.devices.device.config._truncated is True


def test_get_module_root_service_depth_without_services():
    """
    Test that /services is added even if the depth-limited xpath excludes it.
    """

    cd = DepthFakeClixon(
        """<rpc-reply xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"><data><devices xmlns="http://clicon.org/controller"><device><name>r1</name></device></devices></data></rpc-reply>"""
    )
    module = SimpleNamespace(
        SERVICE="testA",
        SERVICE_DEPTH=3,
        SERVICE_XPATH="/ctrl:devices",
        SERVICE_NAMESPACES={},
    )

    root = get_module_root(cd, module, None, None)

    assert cd.calls[-1] == {"xpath": "/ctrl:devices", "namespaces": {}, "depth": 3}
    assert root.services.testA.peer.ip.get_data() == "10.0.0.1"


@pytest.mark.parametrize("depth", [0, -1, "3", 2.5, True])
def test_get_module_root_invalid_service_depth(depth):
    """
    Test that an invalid SERVICE_DEPTH is rejected.
    """

    cd = DepthFakeClixon()
    module = SimpleNamespace(SERVICE="testA", SERVICE_DEPTH=depth)

    with pytest.raises(ValueError, match="SERVICE_DEPTH"):
        get_module_root(cd, module, "testA", "foo")

    assert cd.calls == []
