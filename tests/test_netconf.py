from clixon.parser import parse_string
from clixon import netconf
from clixon.element import Element
import pytest


def test_rpc_config_set():
    """
    Test the rpc_config_set function.
    """

    xmlstr = """<rpc xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" username="root" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="42"><edit-config><target><actions xmlns="http://clicon.org/controller"/></target><default-operation>none</default-operation><config/></edit-config></rpc>"""

    config = Element("config", {})
    root = netconf.rpc_config_set(config)

    assert root.dumps() == xmlstr


def test_rpc_config_get():
    """
    Test the rpc_config_get function.
    """

    xmlstr = """<rpc xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" username="root" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="42"><get-config><source><actions xmlns="http://clicon.org/controller"/></source><nc:filter nc:type="xpath" nc:select="/"/></get-config></rpc>"""

    root = netconf.rpc_config_get()

    assert root.dumps() == xmlstr


def test_rpc_commit():
    """
    Test the rpc_commit function.
    """

    xmlstr = """<rpc xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" username="root" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="42"><commit/></rpc>"""

    root = netconf.rpc_commit()

    assert root.dumps() == xmlstr


def test_rpc_subscription_create():
    """
    Test the rpc_subscription_create function.
    """

    xmlstr = """<rpc xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="42"><create-subscription xmlns="urn:ietf:params:xml:ns:netmod:notification"><stream>services-commit</stream><filter type="xpath" select=""/></create-subscription></rpc>"""

    root = netconf.rpc_subscription_create()

    assert root.dumps() == xmlstr


def test_rpc_header_get():
    """
    Test the rpc_header_get function.
    """

    xmlstr1 = """<rpc xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" username="root" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="42"><get-config/></rpc>"""
    xmlstr2 = """<rpc xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" username="root" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="42"><edit-config/></rpc>"""
    xmlstr3 = """<rpc xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" username="root" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="42"><commit/></rpc>"""
    xmlstr4 = """<rpc xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" username="root" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="42"><transaction-actions-done xmlns="http://clicon.org/controller"/></rpc>"""
    xmlstr5 = """<rpc xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" username="root" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="42"><transaction-error xmlns="http://clicon.org/controller"/></rpc>"""
    xmlstr6 = """<rpc xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" username="root" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="42"><controller-commit xmlns="http://clicon.org/controller"><device>*</device><push>COMMIT</push><actions>NONE</actions><source>ds:running</source></controller-commit></rpc>"""
    xmlstr7 = """<rpc xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" username="root" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="42"><config-pull xmlns="http://clicon.org/controller"><devname>*</devname></config-pull></rpc>"""

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

    root = netconf.rpc_header_get(netconf.RPCTypes(5), "root")

    assert root.dumps() == xmlstr6

    root = netconf.rpc_header_get(netconf.RPCTypes(6), "root")

    assert root.dumps() == xmlstr7


def test_rpc_push():
    """
    Test the rpc_push function.
    """

    xmlstr = """<rpc xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" username="root" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="42"><controller-commit xmlns="http://clicon.org/controller"><device>*</device><push>COMMIT</push><actions>NONE</actions><source>ds:running</source></controller-commit></rpc>"""

    root = netconf.rpc_push()

    assert root.dumps() == xmlstr


def test_rpc_pull():
    """
    Test the rpc_pull function.
    """

    xmlstr = """<rpc xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" username="root" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="42"><config-pull xmlns="http://clicon.org/controller"><devname>*</devname></config-pull></rpc>"""

    root = netconf.rpc_pull()

    assert root.dumps() == xmlstr


def test_rpc_error_get():
    """
    Test the rpc_error_get function.
    """

    xmlstr1 = """client already registered"""
    xmlstr2 = """garbage"""
    xmlstr3 = """<rpc-reply><rpc-error><error-type>application</error-type><error-tag>operation-failed</error-tag><error-severity>error</error-severity><error-message>client already registered</error-message></rpc-error></rpc-reply>"""

    with pytest.raises(SystemExit):
        netconf.rpc_error_get(xmlstr1)

    with pytest.raises(netconf.RPCError):
        netconf.rpc_error_get(xmlstr2)
