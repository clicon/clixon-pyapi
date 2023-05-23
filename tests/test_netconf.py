from clixon import netconf
from clixon.element import Element


def test_rpc_config_set():
    xmlstr = """<rpc xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" username="root" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="42"><edit-config><target><actions xmlns="http://clicon.org/controller"/></target><default-operation>none</default-operation><config/></edit-config></rpc>"""

    config = Element("config", {})
    root = netconf.rpc_config_set(config)

    assert root.dumps() == xmlstr


def test_rpc_config_get():
    xmlstr = """<rpc xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" username="root" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="42"><get-config><source><actions xmlns="http://clicon.org/controller"/></source><nc:filter nc:type="xpath" nc:select="/"/></get-config></rpc>"""

    root = netconf.rpc_config_get()

    assert root.dumps() == xmlstr


def test_rpc_commit():
    xmlstr = """<rpc xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" username="root" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="42"><commit/></rpc>"""

    root = netconf.rpc_commit()

    assert root.dumps() == xmlstr


def test_rpc_subscription_create():
    xmlstr = """<rpc xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="42"><create-subscription xmlns="urn:ietf:params:xml:ns:netmod:notification"><stream>services-commit</stream><filter type="xpath" select=""/></create-subscription></rpc>"""

    root = netconf.rpc_subscription_create()

    assert root.dumps() == xmlstr


def test_rpc_header_get():
    xmlstr1 = """<rpc xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" username="root" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="42"><get-config/></rpc>"""
    xmlstr2 = """<rpc xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" username="root" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="42"><edit-config/></rpc>"""
    xmlstr3 = """<rpc xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" username="root" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="42"><commit/></rpc>"""
    xmlstr4 = """<rpc xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" username="root" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="42"><transaction-actions-done xmlns="http://clicon.org/controller"/></rpc>"""
    xmlstr5 = """<rpc xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" username="root" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="42"><transaction-error xmlns="http://clicon.org/controller"/></rpc>"""

    root = netconf.rpc_header_get(netconf.RPCTypes(0), "root")

    assert root.dumps() == xmlstr1

    root = netconf.rpc_header_get(netconf.RPCTypes(1), "root")

    assert root.dumps() == xmlstr2

    root = netconf.rpc_header_get(netconf.RPCTypes(2), "root")

    assert root.dumps() == xmlstr3

    root = netconf.rpc_header_get(netconf.RPCTypes(3), "root")

    assert root.dumps() == xmlstr4

    root = netconf.rpc_header_get(netconf.RPCTypes(4), "root")

    assert root.dumps() == xmlstr5


def test_rpc_subscription_create():
    xmlstr = """<rpc xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="42"><create-subscription xmlns="urn:ietf:params:xml:ns:netmod:notification"><stream>services-commit</stream><filter type="xpath" select=""/></create-subscription></rpc>"""

    root = netconf.rpc_subscription_create()

    assert root.dumps() == xmlstr
