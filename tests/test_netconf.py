from pyapi import netconf
from pyapi.element import Element


def test_rpc_config_set():
    xmlstr = """<rpc xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" username="root" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="42"><edit-config><target><candidate/></target><default-operation>replace</default-operation><config/></edit-config></rpc>"""

    config = Element("config", {})
    root = netconf.rpc_config_set(config)

    assert root.dumps() == xmlstr


def test_rpc_config_get():
    xmlstr = """<rpc xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" username="root" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="42"><get-config><source><candidate/></source><nc:filter nc:type="xpath" nc:select="/"/></get-config></rpc>"""

    root = netconf.rpc_config_get()
    xmlout = root.dumps()

    assert xmlout == xmlstr


def test_rpc_commit():
    xmlstr = """<rpc xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" username="root" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="42"><commit/></rpc>"""

    root = netconf.rpc_commit()
    xmlout = root.dumps()

    assert xmlout == xmlstr


def test_rpc_subscription_create():
    xmlstr = """<rpc xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="42"><create-subscription xmlns="urn:ietf:params:xml:ns:netmod:notification"><stream>controller</stream><filter type="xpath" select=""/></create-subscription></rpc>"""

    root = netconf.rpc_subscription_create()
    xmlout = root.dumps()

    assert xmlout == xmlstr
