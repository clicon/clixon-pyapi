from types import SimpleNamespace

import pytest

from clixon.element import mark_truncated
from clixon.modules import get_module_root
from clixon.parser import parse_string


FULL_SERVICES_REPLY = """<rpc-reply xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"><data><services xmlns="http://clicon.org/controller"><testA xmlns="urn:example:test"><service-name>foo</service-name><peer><ip>10.0.0.1</ip><md5>secret</md5></peer></testA></services></data></rpc-reply>"""

# Depth 3: the services peer entry and the device config are cut off
DEPTH_3_REPLY = """<rpc-reply xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"><data><devices xmlns="http://clicon.org/controller"><device><name>r1</name><config></config></device></devices><services xmlns="http://clicon.org/controller"><testA xmlns="urn:example:test"><service-name>foo</service-name><peer></peer></testA></services></data></rpc-reply>"""

DEVICES_ONLY_REPLY = """<rpc-reply xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"><data><devices xmlns="http://clicon.org/controller"><device><name>r1</name></device></devices></data></rpc-reply>"""


class FakeClixon:
    def __init__(self, depth_reply=DEPTH_3_REPLY):
        self.depth_reply = depth_reply
        self.calls = []

    def get_root(self, xpath="/", namespaces=None, depth=None, write_back=True):
        call = {"xpath": xpath, "namespaces": namespaces, "depth": depth}

        if not write_back:
            call["write_back"] = False

        self.calls.append(call)

        if depth is None:
            return parse_string(FULL_SERVICES_REPLY).rpc_reply.data

        root = parse_string(self.depth_reply).rpc_reply.data
        mark_truncated(root)

        return root


def test_get_module_root_without_service_depth():
    """
    Test that the whole config is fetched once without SERVICE_DEPTH.
    """

    cd = FakeClixon()
    get_module_root(cd, SimpleNamespace(SERVICE="testA"))

    assert cd.calls == [{"xpath": "/", "namespaces": None, "depth": None}]


def test_get_module_root_service_xpath():
    """
    Test that SERVICE_XPATH is used when SERVICE_NAMESPACES is also set.
    """

    cd = FakeClixon()
    module = SimpleNamespace(
        SERVICE="testA", SERVICE_XPATH="/services", SERVICE_NAMESPACES={}
    )

    get_module_root(cd, module)

    assert cd.calls == [{"xpath": "/services", "namespaces": {}, "depth": None}]


def test_get_module_root_with_service_depth():
    """
    Test that SERVICE_DEPTH limits the tree but /services is always complete.
    """

    cd = FakeClixon()
    root = get_module_root(cd, SimpleNamespace(SERVICE="testA", SERVICE_DEPTH=3))

    # /services is only used to fill in the depth-limited tree, which is the
    # one written back
    assert cd.calls == [
        {"xpath": "/services", "namespaces": None, "depth": None, "write_back": False},
        {"xpath": "/", "namespaces": None, "depth": 3},
    ]

    assert len(root.get_elements("services")) == 1
    assert root.services.testA.peer.md5.get_data() == "secret"
    assert root.devices.device.name.get_data() == "r1"
    assert root.devices.device.config._truncated is True

    # The moved services are unchanged configuration
    assert root.services.prune() is None
    assert root.services._parent is root


def test_get_module_root_service_depth_with_service_xpath():
    """
    Test that /services is added even if SERVICE_XPATH excludes it.
    """

    cd = FakeClixon(DEVICES_ONLY_REPLY)
    module = SimpleNamespace(
        SERVICE="testA",
        SERVICE_DEPTH=3,
        SERVICE_XPATH="/ctrl:devices",
        SERVICE_NAMESPACES={},
    )

    root = get_module_root(cd, module)

    assert cd.calls[-1] == {"xpath": "/ctrl:devices", "namespaces": {}, "depth": 3}
    assert root.services.testA.peer.ip.get_data() == "10.0.0.1"


@pytest.mark.parametrize("depth", [0, -1, "3", 2.5, True])
def test_get_module_root_invalid_service_depth(depth):
    """
    Test that an invalid SERVICE_DEPTH is rejected before anything is fetched.
    """

    cd = FakeClixon()
    module = SimpleNamespace(SERVICE="testA", SERVICE_DEPTH=depth)

    with pytest.raises(ValueError, match="SERVICE_DEPTH"):
        get_module_root(cd, module)

    assert cd.calls == []
