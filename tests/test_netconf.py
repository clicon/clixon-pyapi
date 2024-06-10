from clixon.parser import parse_string
from clixon import netconf
from clixon.element import Element
import pytest


def test_rpc_config_set():
    """
    Test the rpc_config_set function.
    """

    xmlstr = """<rpc xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" username="root" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="42" xmlns:cl="http://clicon.org/lib"><edit-config><target><actions xmlns="http://clicon.org/controller"/></target><default-operation>none</default-operation><config/></edit-config></rpc>"""

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
    xmlstr2 = """<rpc xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" username="root" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="42" xmlns:cl="http://clicon.org/lib"><edit-config/></rpc>"""
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


def test_rpc_apply_service():
    """
    Test the rpc_apply_service function.
    """

    xmlstr = """<rpc xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="42" username="root"><controller-commit xmlns="http://clicon.org/controller"><device>*</device><push>NONE</push><actions>FORCE</actions><service-instance>foo[service-name=\'bar\']</service-instance><source>ds:candidate</source></controller-commit></rpc>"""

    root = netconf.rpc_apply_service("foo", "bar")

    assert root.dumps() == xmlstr


def test_rpc_datastore_diff():
    """
    Test the rpc_datastore_diff function.
    """

    xmlstr = """<rpc xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="42" username="root"><datastore-diff xmlns="http://clicon.org/controller"><devname>*</devname><config-type1>RUNNING</config-type1><config-type2>ACTIONS</config-type2></datastore-diff></rpc>"""

    root = netconf.rpc_datastore_diff()

    assert root.dumps() == xmlstr


def test_rpc_datastore_diff_transient():
    """
    Test the rpc_datastore_diff transient function.
    """

    xmlstr = """<rpc xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="42" username="root"><datastore-diff xmlns="http://clicon.org/controller"><devname>*</devname><config-type1>TRANSIENT</config-type1><config-type2>RUNNING</config-type2></datastore-diff></rpc>"""

    assert netconf.rpc_datastore_diff(transient=True).dumps() == xmlstr


def test_rpc_datastore_diff_compare():
    """
    Test the rpc_datastore_diff compare function.
    """

    xmlstr = """<rpc xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="42" username="root"><datastore-diff xmlns="http://clicon.org/controller"><format>text</format><dsref1>ds:running</dsref1><dsref2>ds:candidate</dsref2></datastore-diff></rpc>"""

    assert netconf.rpc_datastore_diff(compare=True).dumps() == xmlstr


def test_rpc_lock():
    """
    Test the rpc_lock function.
    """

    xmlstr = """<rpc xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="42" username="root"><lock><target><candidate/></target></lock></rpc>"""

    assert netconf.rpc_lock().dumps() == xmlstr

    xmlstr = """<rpc xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="42" username="root"><lock><target><foobar/></target></lock></rpc>"""

    assert netconf.rpc_lock("foobar").dumps() == xmlstr


def test_rpc_unlock():
    """
    Test the rpc_unlock function.
    """

    xmlstr = """<rpc xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="42" username="root"><unlock><target><candidate/></target></unlock></rpc>"""

    assert netconf.rpc_unlock().dumps() == xmlstr

    xmlstr = """<rpc xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="42" username="root"><unlock><target><foobar/></target></unlock></rpc>"""

    assert netconf.rpc_unlock("foobar").dumps() == xmlstr
