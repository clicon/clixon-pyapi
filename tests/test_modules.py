from types import SimpleNamespace

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
