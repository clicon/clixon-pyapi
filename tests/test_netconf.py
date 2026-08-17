import getpass

import pytest

from clixon import netconf
from clixon.element import Element
from clixon.exceptions import RPCError

user = getpass.getuser()


def test_rpc_config_set():
    """
    Test the rpc_config_set function.
    """

    xmlstr = f"""<rpc xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" username="{user}" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="42" xmlns:cl="http://clicon.org/lib"><edit-config><target><actions xmlns="http://clicon.org/controller"/></target><default-operation>merge</default-operation><config><devices xmlns="http://clicon.org/controller"/></config></edit-config></rpc>"""

    config = Element("config", {})
    config.create("devices").create("device").create("name", data="foo")
    root = netconf.rpc_config_set(config)

    assert root.dumps() == xmlstr


def test_rpc_config_set_user():
    """
    Test the rpc_config_set function with user.
    """

    user = "nisse"
    xmlstr = f"""<rpc xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" username="{user}" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="42" xmlns:cl="http://clicon.org/lib"><edit-config><target><actions xmlns="http://clicon.org/controller"/></target><default-operation>merge</default-operation><config><devices xmlns="http://clicon.org/controller"/></config></edit-config></rpc>"""

    config = Element("config", {})
    config.create("devices").create("device").create("name", data="foo")
    root = netconf.rpc_config_set(config, user="nisse")

    assert root.dumps() == xmlstr


def test_rpc_config_get():
    """
    Test the rpc_config_get function.
    """

    xmlstr = f"""<rpc xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" username="{user}" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="42"><get-config><source><actions xmlns="http://clicon.org/controller"/></source><nc:filter nc:type="xpath" nc:select="/" xmlns:ctrl="http://clicon.org/controller"/></get-config></rpc>"""

    root = netconf.rpc_config_get()

    assert root.dumps() == xmlstr


def test_rpc_config_get_user():
    """
    Test the rpc_config_get function with user.
    """

    xmlstr = f"""<rpc xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" username="nisse" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="42"><get-config><source><actions xmlns="http://clicon.org/controller"/></source><nc:filter nc:type="xpath" nc:select="/" xmlns:ctrl="http://clicon.org/controller"/></get-config></rpc>"""

    root = netconf.rpc_config_get(user="nisse")

    assert root.dumps() == xmlstr


def test_rpc_commit():
    """
    Test the rpc_commit function.
    """

    xmlstr = f"""<rpc xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" username="{user}" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="42"><commit/></rpc>"""

    root = netconf.rpc_commit()

    assert root.dumps() == xmlstr


def test_rpc_commit_user():
    """
    Test the rpc_commit function with user.
    """

    xmlstr = f"""<rpc xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" username="nisse" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="42"><commit/></rpc>"""

    root = netconf.rpc_commit(user="nisse")

    assert root.dumps() == xmlstr


def test_rpc_subscription_create():
    """
    Test the rpc_subscription_create function.
    """

    xmlstr = f"""<rpc xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" cl:username="{user}" xmlns:cl="http://clicon.org/lib" message-id="42"><create-subscription xmlns="urn:ietf:params:xml:ns:netmod:notification"><stream>services-commit</stream><filter type="xpath" select=""/></create-subscription></rpc>"""

    root = netconf.rpc_subscription_create()

    assert root.dumps() == xmlstr


def test_rpc_subscription_create_user():
    """
    Test the rpc_subscription_create function with user.
    """

    xmlstr = f"""<rpc xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" cl:username="nisse" xmlns:cl="http://clicon.org/lib" message-id="42"><create-subscription xmlns="urn:ietf:params:xml:ns:netmod:notification"><stream>services-commit</stream><filter type="xpath" select=""/></create-subscription></rpc>"""

    root = netconf.rpc_subscription_create(user="nisse")

    assert root.dumps() == xmlstr


def test_rpc_header_get():
    """
    Test the rpc_header_get function.
    """

    xmlstr1 = f"""<rpc xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" username="{user}" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="42"><get-config/></rpc>"""
    xmlstr2 = f"""<rpc xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" username="{user}" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="42" xmlns:cl="http://clicon.org/lib"><edit-config/></rpc>"""
    xmlstr3 = f"""<rpc xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" username="{user}" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="42"><commit/></rpc>"""
    xmlstr4 = f"""<rpc xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" username="{user}" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="42"><transaction-actions-done xmlns="http://clicon.org/controller"/></rpc>"""
    xmlstr5 = f"""<rpc xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" username="{user}" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="42"><transaction-error xmlns="http://clicon.org/controller"/></rpc>"""
    xmlstr6 = f"""<rpc xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" username="{user}" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="42"><controller-commit xmlns="http://clicon.org/controller"><device>*</device><push>COMMIT</push><actions>NONE</actions><source>ds:running</source></controller-commit></rpc>"""
    xmlstr7 = f"""<rpc xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" username="{user}" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="42"><config-pull xmlns="http://clicon.org/controller"><device>*</device></config-pull></rpc>"""

    root = netconf.rpc_header_get(netconf.RPCTypes(0), f"{user}")

    assert root.dumps() == xmlstr1

    root = netconf.rpc_header_get(netconf.RPCTypes(1), f"{user}")

    assert root.dumps() == xmlstr2

    root = netconf.rpc_header_get(netconf.RPCTypes(2), f"{user}")

    assert root.dumps() == xmlstr3

    root = netconf.rpc_header_get(netconf.RPCTypes(3), f"{user}")

    assert root.dumps() == xmlstr4

    root = netconf.rpc_header_get(netconf.RPCTypes(4), f"{user}")

    assert root.dumps() == xmlstr5

    root = netconf.rpc_header_get(netconf.RPCTypes(5), f"{user}")

    assert root.dumps() == xmlstr6

    root = netconf.rpc_header_get(netconf.RPCTypes(6), f"{user}")

    assert root.dumps() == xmlstr7


def test_rpc_header_get_user():
    """
    Test the rpc_header_get function with user.
    """

    xmlstr1 = f"""<rpc xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" username="nisse" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="42"><get-config/></rpc>"""
    xmlstr2 = f"""<rpc xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" username="nisse" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="42" xmlns:cl="http://clicon.org/lib"><edit-config/></rpc>"""
    xmlstr3 = f"""<rpc xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" username="nisse" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="42"><commit/></rpc>"""
    xmlstr4 = f"""<rpc xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" username="nisse" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="42"><transaction-actions-done xmlns="http://clicon.org/controller"/></rpc>"""
    xmlstr5 = f"""<rpc xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" username="nisse" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="42"><transaction-error xmlns="http://clicon.org/controller"/></rpc>"""
    xmlstr6 = f"""<rpc xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" username="nisse" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="42"><controller-commit xmlns="http://clicon.org/controller"><device>*</device><push>COMMIT</push><actions>NONE</actions><source>ds:running</source></controller-commit></rpc>"""
    xmlstr7 = f"""<rpc xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" username="nisse" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="42"><config-pull xmlns="http://clicon.org/controller"><device>*</device></config-pull></rpc>"""

    root = netconf.rpc_header_get(netconf.RPCTypes(0), "nisse")

    assert root.dumps() == xmlstr1

    root = netconf.rpc_header_get(netconf.RPCTypes(1), "nisse")

    assert root.dumps() == xmlstr2

    root = netconf.rpc_header_get(netconf.RPCTypes(2), "nisse")

    assert root.dumps() == xmlstr3

    root = netconf.rpc_header_get(netconf.RPCTypes(3), "nisse")

    assert root.dumps() == xmlstr4

    root = netconf.rpc_header_get(netconf.RPCTypes(4), "nisse")

    assert root.dumps() == xmlstr5

    root = netconf.rpc_header_get(netconf.RPCTypes(5), "nisse")

    assert root.dumps() == xmlstr6

    root = netconf.rpc_header_get(netconf.RPCTypes(6), "nisse")

    assert root.dumps() == xmlstr7


def test_rpc_push():
    """
    Test the rpc_push function.
    """

    xmlstr = f"""<rpc xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" username="{user}" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="42"><controller-commit xmlns="http://clicon.org/controller"><device>*</device><push>COMMIT</push><actions>NONE</actions><source>ds:running</source></controller-commit></rpc>"""

    root = netconf.rpc_push()

    assert root.dumps() == xmlstr


def test_rpc_push_user():
    """
    Test the rpc_push function with user.
    """

    xmlstr = f"""<rpc xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" username="nisse" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="42"><controller-commit xmlns="http://clicon.org/controller"><device>*</device><push>COMMIT</push><actions>NONE</actions><source>ds:running</source></controller-commit></rpc>"""

    root = netconf.rpc_push(user="nisse")

    assert root.dumps() == xmlstr


def test_rpc_pull():
    """
    Test the rpc_pull function.
    """

    xmlstr = f"""<rpc xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" username="{user}" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="42"><config-pull xmlns="http://clicon.org/controller"><device>*</device></config-pull></rpc>"""

    root = netconf.rpc_pull()

    assert root.dumps() == xmlstr


def test_rpc_pull_user():
    """
    Test the rpc_pull function with user.
    """

    xmlstr = f"""<rpc xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" username="nisse" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="42"><config-pull xmlns="http://clicon.org/controller"><device>*</device></config-pull></rpc>"""

    root = netconf.rpc_pull(user="nisse")

    assert root.dumps() == xmlstr


def test_rpc_error_get():
    """
    Test the rpc_error_get function.
    """

    xmlstr1 = """client already registered"""
    xmlstr2 = """garbage"""

    with pytest.raises(SystemExit):
        netconf.rpc_error_get(xmlstr1)

    with pytest.raises(netconf.RPCError):
        netconf.rpc_error_get(xmlstr2)


def test_rpc_apply_template():
    """
    Test the rpc_apply_template function.
    """

    xmlstr = f"""<rpc xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="42" username="{user}"><device-template-apply xmlns="http://clicon.org/controller"><type>RPC</type><device>test</device><template>test</template><variables><variable><name>test</name><value>test</value></variable></variables></device-template-apply></rpc>"""

    root = netconf.rpc_apply_template("test", "test", {"test": "test"})

    assert root.dumps() == xmlstr


def test_rpc_apply_template_user():
    """
    Test the rpc_apply_template function with user.
    """

    xmlstr = f"""<rpc xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="42" username="nisse"><device-template-apply xmlns="http://clicon.org/controller"><type>RPC</type><device>test</device><template>test</template><variables><variable><name>test</name><value>test</value></variable></variables></device-template-apply></rpc>"""

    root = netconf.rpc_apply_template("test", "test", {"test": "test"}, user="nisse")

    assert root.dumps() == xmlstr


def test_rpc_apply_service():
    """
    Test the rpc_apply_service function.
    """

    xmlstr = f"""<rpc xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="42" username="{user}"><controller-commit xmlns="http://clicon.org/controller"><device>*</device><push>NONE</push><actions>FORCE</actions><service-instance>foo[service-name=\'bar\']</service-instance><source>ds:candidate</source></controller-commit></rpc>"""

    root = netconf.rpc_apply_service("foo", "bar")

    assert root.dumps() == xmlstr


def test_rpc_apply_service_user():
    """
    Test the rpc_apply_service function with user.
    """

    xmlstr = f"""<rpc xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="42" username="nisse"><controller-commit xmlns="http://clicon.org/controller"><device>*</device><push>NONE</push><actions>FORCE</actions><service-instance>foo[service-name=\'bar\']</service-instance><source>ds:candidate</source></controller-commit></rpc>"""

    root = netconf.rpc_apply_service("foo", "bar", user="nisse")

    assert root.dumps() == xmlstr


def test_rpc_datastore_diff():
    """
    Test the rpc_datastore_diff function.
    """

    xmlstr = f"""<rpc xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="42" username="{user}"><datastore-diff xmlns="http://clicon.org/controller"><device>*</device><config-type1>RUNNING</config-type1><config-type2>ACTIONS</config-type2></datastore-diff></rpc>"""

    root = netconf.rpc_datastore_diff()

    assert root.dumps() == xmlstr


def test_rpc_datastore_diff_user():
    """
    Test the rpc_datastore_diff function with user.
    """

    xmlstr = f"""<rpc xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="42" username="nisse"><datastore-diff xmlns="http://clicon.org/controller"><device>*</device><config-type1>RUNNING</config-type1><config-type2>ACTIONS</config-type2></datastore-diff></rpc>"""

    root = netconf.rpc_datastore_diff(user="nisse")

    assert root.dumps() == xmlstr


def test_rpc_datastore_diff_transient():
    """
    Test the rpc_datastore_diff transient function.
    """

    xmlstr = f"""<rpc xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="42" username="{user}"><datastore-diff xmlns="http://clicon.org/controller"><device>*</device><config-type1>TRANSIENT</config-type1><config-type2>RUNNING</config-type2></datastore-diff></rpc>"""

    assert netconf.rpc_datastore_diff(transient=True).dumps() == xmlstr


def test_rpc_datastore_diff_transient_user():
    """
    Test the rpc_datastore_diff transient function with user.
    """

    xmlstr = f"""<rpc xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="42" username="nisse"><datastore-diff xmlns="http://clicon.org/controller"><device>*</device><config-type1>TRANSIENT</config-type1><config-type2>RUNNING</config-type2></datastore-diff></rpc>"""

    assert netconf.rpc_datastore_diff(transient=True, user="nisse").dumps() == xmlstr


def test_rpc_datastore_diff_compare():
    """
    Test the rpc_datastore_diff compare function.
    """

    xmlstr = f"""<rpc xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="42" username="{user}"><datastore-diff xmlns="http://clicon.org/controller"><format>text</format><dsref1>ds:running</dsref1><dsref2>ds:candidate</dsref2></datastore-diff></rpc>"""

    assert netconf.rpc_datastore_diff(compare=True).dumps() == xmlstr


def test_rpc_datastore_diff_compare_user():
    """
    Test the rpc_datastore_diff compare function with user.
    """

    xmlstr = f"""<rpc xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="42" username="nisse"><datastore-diff xmlns="http://clicon.org/controller"><format>text</format><dsref1>ds:running</dsref1><dsref2>ds:candidate</dsref2></datastore-diff></rpc>"""

    assert netconf.rpc_datastore_diff(compare=True, user="nisse").dumps() == xmlstr


def test_rpc_lock():
    """
    Test the rpc_lock function.
    """

    xmlstr = f"""<rpc xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="42" username="{user}"><lock><target><candidate/></target></lock></rpc>"""

    assert netconf.rpc_lock().dumps() == xmlstr

    xmlstr = f"""<rpc xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="42" username="{user}"><lock><target><foobar/></target></lock></rpc>"""

    assert netconf.rpc_lock("foobar").dumps() == xmlstr


def test_rpc_unlock():
    """
    Test the rpc_unlock function.
    """

    xmlstr = f"""<rpc xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="42" username="{user}"><unlock><target><candidate/></target></unlock></rpc>"""

    assert netconf.rpc_unlock().dumps() == xmlstr

    xmlstr = f"""<rpc xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="42" username="{user}"><unlock><target><foobar/></target></unlock></rpc>"""

    assert netconf.rpc_unlock("foobar").dumps() == xmlstr


def test_rpc_unlock():
    """
    Test the rpc_unlock function.
    """

    xmlstr = f"""<rpc xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="42" username="{user}"><unlock><target><candidate/></target></unlock></rpc>"""

    assert netconf.rpc_unlock().dumps() == xmlstr

    xmlstr = f"""<rpc xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="42" username="{user}"><unlock><target><foobar/></target></unlock></rpc>"""

    assert netconf.rpc_unlock("foobar").dumps() == xmlstr


def test_rpc_connection_open():
    """
    Test the rpc_connection_open function.
    """

    xmlstr0 = f"""<rpc xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="42" username="{user}"><connection-change xmlns="http://clicon.org/controller"><operation>OPEN</operation><device>*</device></connection-change></rpc>"""
    xmlstr1 = f"""<rpc xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="42" username="{user}"><connection-change xmlns="http://clicon.org/controller"><operation>OPEN</operation><device>test</device></connection-change></rpc>"""

    assert netconf.rpc_connection_open().dumps() == xmlstr0
    assert netconf.rpc_connection_open(device="test").dumps() == xmlstr1


def test_rpc_transactions_get():
    """
    Test the rpc_transactions_get function.
    """

    xmlstr0 = f"""<rpc xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" cl:username="{user}" xmlns:cl="http://clicon.org/lib" message-id="42"><get cl:content="nonconfig" xmlns:cl="http://clicon.org/lib"><nc:filter nc:type="xpath" nc:select="co:transactions" xmlns:co="http://clicon.org/controller"/><with-defaults xmlns="urn:ietf:params:xml:ns:yang:ietf-netconf-with-defaults">report-all</with-defaults></get></rpc>"""
    xmlstr1 = f"""<rpc xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" cl:username="{user}" xmlns:cl="http://clicon.org/lib" message-id="42"><get cl:content="nonconfig" xmlns:cl="http://clicon.org/lib"><nc:filter nc:type="xpath" nc:select="/co:transactions/co:transaction[co:tid=\'123\']" xmlns:co="http://clicon.org/controller"/><with-defaults xmlns="urn:ietf:params:xml:ns:yang:ietf-netconf-with-defaults">report-all</with-defaults></get></rpc>"""
    xmlstr2 = f"""<rpc xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" cl:username="test123" xmlns:cl="http://clicon.org/lib" message-id="42"><get cl:content="nonconfig" xmlns:cl="http://clicon.org/lib"><nc:filter nc:type="xpath" nc:select="co:transactions" xmlns:co="http://clicon.org/controller"/><with-defaults xmlns="urn:ietf:params:xml:ns:yang:ietf-netconf-with-defaults">report-all</with-defaults></get></rpc>"""
    xmlstr3 = f"""<rpc xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" cl:username="test123" xmlns:cl="http://clicon.org/lib" message-id="42"><get cl:content="nonconfig" xmlns:cl="http://clicon.org/lib"><nc:filter nc:type="xpath" nc:select="/co:transactions/co:transaction[co:tid=\'123\']" xmlns:co="http://clicon.org/controller"/><with-defaults xmlns="urn:ietf:params:xml:ns:yang:ietf-netconf-with-defaults">report-all</with-defaults></get></rpc>"""

    assert netconf.rpc_transactions_get().dumps() == xmlstr0
    assert netconf.rpc_transactions_get(tid=123).dumps() == xmlstr1
    assert netconf.rpc_transactions_get(user="test123").dumps() == xmlstr2
    assert netconf.rpc_transactions_get(tid=123, user="test123").dumps() == xmlstr3


def test_rpc_discard_changes():
    """
    Test the rpc_discard_changes function.
    """

    xmlstr0 = f"""<rpc xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" cl:username="{user}" xmlns:cl="http://clicon.org/lib" message-id="42"><discard-changes/></rpc>"""

    assert netconf.rpc_discard_changes().dumps() == xmlstr0


def test_rpc_devices_get():
    """
    Test the rpc_devices_get function.
    """

    xmlstr0 = f"""<rpc xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" cl:username="{user}" xmlns:cl="http://clicon.org/lib" message-id="42"><get cl:content="all" xmlns:cl="http://clicon.org/lib"><nc:filter nc:type="xpath" nc:select="co:devices/co:device/co:name | co:devices/co:device/co:conn-state | co:devices/co:device/co:conn-state-timestamp | co:devices/co:device/co:logmsg" xmlns:co="http://clicon.org/controller"/><with-defaults xmlns="urn:ietf:params:xml:ns:yang:ietf-netconf-with-defaults">explicit</with-defaults></get></rpc>"""

    assert netconf.rpc_devices_get().dumps() == xmlstr0


def test_rpc_schemas_get():
    """
    Test the rpc_schemas_get function.
    """

    xmlstr0 = f"""<rpc xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" cl:username="{user}" xmlns:cl="http://clicon.org/lib" message-id="42"><get cl:content="nonconfig" xmlns:cl="http://clicon.org/lib"><nc:filter nc:type="xpath" nc:select="/ncm:netconf-state/ncm:schemas" xmlns:ncm="urn:ietf:params:xml:ns:yang:ietf-netconf-monitoring"/></get></rpc>"""

    assert netconf.rpc_schemas_get().dumps() == xmlstr0


def test_rpc_get_schema():
    """
    Test the rpc_schema_get function.
    """

    xmlstr0 = f"""<rpc xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" cl:username="{user}" xmlns:cl="http://clicon.org/lib" message-id="42"><get-schema xmlns="urn:ietf:params:xml:ns:yang:ietf-netconf-monitoring"><identifier>myservice</identifier><format>yang</format></get-schema></rpc>"""
    xmlstr1 = f"""<rpc xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" cl:username="{user}" xmlns:cl="http://clicon.org/lib" message-id="42"><get-schema xmlns="urn:ietf:params:xml:ns:yang:ietf-netconf-monitoring"><identifier>myservice</identifier><version>2026-01-01</version><format>yang</format></get-schema></rpc>"""
    xmlstr2 = """<rpc xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" cl:username="test123" xmlns:cl="http://clicon.org/lib" message-id="42"><get-schema xmlns="urn:ietf:params:xml:ns:yang:ietf-netconf-monitoring"><identifier>myservice</identifier><format>yin</format></get-schema></rpc>"""

    assert netconf.rpc_schema_get("myservice").dumps() == xmlstr0
    assert netconf.rpc_schema_get("myservice", version="2026-01-01").dumps() == xmlstr1
    assert (
        netconf.rpc_schema_get("myservice", format="yin", user="test123").dumps()
        == xmlstr2
    )


def test_rpc_config_get_with_xpath():
    """
    Test the rpc_config_get function with custom xpath.
    """

    xmlstr = f"""<rpc xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" username="{user}" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="42"><get-config><source><actions xmlns="http://clicon.org/controller"/></source><nc:filter nc:type="xpath" nc:select="/ctrl:services" xmlns:ctrl="http://clicon.org/controller"/></get-config></rpc>"""

    root = netconf.rpc_config_get(xpath="/services")

    assert root.dumps() == xmlstr


def test_rpc_config_get_with_xpath_and_namespaces():
    """
    Test the rpc_config_get function with custom xpath and namespaces.
    """

    xmlstr = f"""<rpc xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" username="{user}" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="42"><get-config><source><actions xmlns="http://clicon.org/controller"/></source><nc:filter nc:type="xpath" nc:select="/ctrl:services/l2c:l2c" xmlns:ctrl="http://clicon.org/controller" xmlns:l2c="http://example.com/l2c"/></get-config></rpc>"""

    namespaces = {"l2c": "http://example.com/l2c"}
    root = netconf.rpc_config_get(xpath="/services/l2c:l2c", namespaces=namespaces)

    assert root.dumps() == xmlstr


def test_rpc_config_get_with_xpath_different_source():
    """
    Test the rpc_config_get function with xpath and different source.
    """

    xmlstr = f"""<rpc xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" username="{user}" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="42"><get-config><source><candidate/></source><nc:filter nc:type="xpath" nc:select="/ctrl:devices" xmlns:ctrl="http://clicon.org/controller"/></get-config></rpc>"""

    root = netconf.rpc_config_get(source="candidate", xpath="/devices")

    assert root.dumps() == xmlstr


def test_rpc_config_get_with_multiple_namespaces():
    """
    Test the rpc_config_get function with multiple custom namespaces.
    """

    xmlstr = f"""<rpc xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" username="{user}" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="42"><get-config><source><actions xmlns="http://clicon.org/controller"/></source><nc:filter nc:type="xpath" nc:select="/ctrl:services/l2c:l2c[l2c:service-name=\'test\']" xmlns:ctrl="http://clicon.org/controller" xmlns:l2c="http://example.com/l2c" xmlns:custom="http://example.com/custom"/></get-config></rpc>"""

    namespaces = {
        "l2c": "http://example.com/l2c",
        "custom": "http://example.com/custom",
    }
    root = netconf.rpc_config_get(
        xpath="/services/l2c:l2c[l2c:service-name='test']", namespaces=namespaces
    )

    assert root.dumps() == xmlstr


def test_rpc_config_set_without_devices():
    """
    Test the rpc_config_set function without devices in config.
    Verifies no crash when config has no devices node (e.g. xpath="/services").
    """

    xmlstr = f"""<rpc xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" username="{user}" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="42" xmlns:cl="http://clicon.org/lib"><edit-config><target><actions xmlns="http://clicon.org/controller"/></target><default-operation>merge</default-operation><config><services><service-name>test</service-name></services></config></edit-config></rpc>"""

    config = Element("config", {})
    config.create("services").create("service-name", data="test")
    root = netconf.rpc_config_set(config)

    assert root.dumps() == xmlstr


def test_rpc_config_set_with_services_and_devices():
    """
    Test the rpc_config_set function with both services and devices.
    Verifies services are included and devices block is handled correctly.
    """

    xmlstr = f"""<rpc xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" username="{user}" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="42" xmlns:cl="http://clicon.org/lib"><edit-config><target><actions xmlns="http://clicon.org/controller"/></target><default-operation>merge</default-operation><config><services><service-name>test</service-name></services><devices xmlns="http://clicon.org/controller"/></config></edit-config></rpc>"""

    config = Element("config", {})
    config.create("services").create("service-name", data="test")
    config.create("devices").create("device").create("name", data="foo")
    root = netconf.rpc_config_set(config)

    assert root.dumps() == xmlstr


def test_rpc_error_get_error_path():
    """
    Test that an error with a path is raised.
    """

    xmlstr = (
        "<rpc-reply><rpc-error><error-app-tag>bad</error-app-tag>"
        "<error-path>/devices/device</error-path></rpc-error></rpc-reply>"
    )

    with pytest.raises(RPCError, match="bad: /devices/device"):
        netconf.rpc_error_get(xmlstr)


def test_rpc_error_get_non_unique():
    """
    Test that a non-unique error is raised.
    """

    xmlstr = (
        "<rpc-reply><rpc-error><error-app-tag>data-not-unique</error-app-tag>"
        "<error-info><non-unique>/devices/device/name</non-unique>"
        "</error-info></rpc-error></rpc-reply>"
    )

    with pytest.raises(RPCError, match="data-not-unique"):
        netconf.rpc_error_get(xmlstr)


def test_rpc_error_get_rpc_error():
    """
    Test that a plain rpc-error is raised.
    """

    xmlstr = (
        "<rpc-reply><rpc-error><error-tag>operation-failed</error-tag>"
        "</rpc-error></rpc-reply>"
    )

    with pytest.raises(RPCError, match="Unknown error"):
        netconf.rpc_error_get(xmlstr)


def test_rpc_error_get_incomplete_errors():
    """
    Test that errors which can not be read are still errors.
    """

    for xmlstr in [
        "<rpc-reply><rpc-error><error-message/></rpc-error></rpc-reply>",
        "<rpc-reply><foo>error-path</foo></rpc-reply>",
        "<rpc-reply><foo>non-unique</foo></rpc-reply>",
    ]:
        with pytest.raises(RPCError):
            netconf.rpc_error_get(xmlstr)


def test_rpc_error_get_failed_result():
    """
    Test that a failed result without a reason is not an error of its own.
    """

    assert netconf.rpc_error_get("<rpc-reply><result>FAILED</result></rpc-reply>") is (
        None
    )


def test_rpc_error_get_notification_reason():
    """
    Test that the reason of a failed notification is raised.
    """

    xmlstr = (
        '<notification xmlns="urn:ietf:params:xml:ns:netconf:notification:1.0">'
        '<controller-transaction xmlns="http://clicon.org/controller">'
        "<result>FAILED</result><reason>device is closed</reason>"
        "</controller-transaction></notification>"
    )

    with pytest.raises(RPCError, match="device is closed"):
        netconf.rpc_error_get(xmlstr)


def test_rpc_error_get_notification_success():
    """
    Test that a successful notification is not an error.
    """

    xmlstr = (
        '<notification xmlns="urn:ietf:params:xml:ns:netconf:notification:1.0">'
        '<controller-transaction xmlns="http://clicon.org/controller">'
        "<result>SUCCESS</result></controller-transaction></notification>"
    )

    assert netconf.rpc_error_get(xmlstr) is None


def test_rpc_config_set_modified_device():
    """
    Test that a device which is modified is added to the configuration.
    """

    config = Element("config", {})
    device = config.create("devices").create("device")
    device.create("name", data="foo")
    device.create("description", data="changed").set_modified(True)

    xmlstr = netconf.rpc_config_set(config).dumps()

    assert "<description>changed</description>" in xmlstr


def test_rpc_apply_template_inline():
    """
    Test that an inline template is used as it is.
    """

    template = "<config><system><hostname>foo</hostname></system></config>"
    xmlstr = netconf.rpc_apply_template("r1", template, {}, inline=True).dumps()

    assert (
        "<inline><config><system><hostname>foo</hostname></system>"
        "</config></inline>" in xmlstr
    )


def test_rpc_users():
    """
    Test that the user of the caller is used by all the RPCs.
    """

    for rpc in [
        netconf.rpc_lock("candidate", user="nisse"),
        netconf.rpc_unlock("candidate", user="nisse"),
        netconf.rpc_connection_open("r1", user="nisse"),
        netconf.rpc_device_rpc_result(1, user="nisse"),
        netconf.rpc_datastore_diff(user="nisse"),
        netconf.rpc_apply_service("s", "i", user="nisse"),
        netconf.rpc_close_session(user="nisse"),
        netconf.rpc_discard_changes(user="nisse"),
        netconf.rpc_devices_get(user="nisse"),
        netconf.rpc_schemas_get(user="nisse"),
        netconf.rpc_schema_get("m", user="nisse"),
    ]:
        assert 'username="nisse"' in rpc.dumps()


def test_rpc_default_users():
    """
    Test that the running user is used when no user is given.
    """

    for rpc in [
        netconf.rpc_lock(),
        netconf.rpc_unlock(),
        netconf.rpc_connection_open(),
        netconf.rpc_device_rpc_result(1),
        netconf.rpc_datastore_diff(),
        netconf.rpc_apply_service("s", "i"),
        netconf.rpc_close_session(),
        netconf.rpc_discard_changes(),
        netconf.rpc_devices_get(),
        netconf.rpc_schemas_get(),
        netconf.rpc_schema_get("m"),
        netconf.rpc_hello(),
        netconf.rpc_commit(),
        netconf.rpc_push(),
        netconf.rpc_pull(),
        netconf.rpc_subscription_create(),
        netconf.rpc_apply_template("r1", "t", {}),
    ]:
        assert user in rpc.dumps()
