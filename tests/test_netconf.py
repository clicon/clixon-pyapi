import getpass

import pytest

from clixon import netconf
from clixon.element import Element

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

    xmlstr = f"""<rpc xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" username="{user}" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="42"><get-config><source><actions xmlns="http://clicon.org/controller"/></source><nc:filter nc:type="xpath" nc:select="/"/></get-config></rpc>"""

    root = netconf.rpc_config_get()

    assert root.dumps() == xmlstr


def test_rpc_config_get_user():
    """
    Test the rpc_config_get function with user.
    """

    xmlstr = f"""<rpc xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" username="nisse" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="42"><get-config><source><actions xmlns="http://clicon.org/controller"/></source><nc:filter nc:type="xpath" nc:select="/"/></get-config></rpc>"""

    root = netconf.rpc_config_get(user="nisse")

    assert root.dumps() == xmlstr


def test_rpc_config_get_xpath():
    """
    Test the rpc_config_get function with custom xpath.
    """

    xmlstr = f"""<rpc xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" username="{user}" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="42"><get-config><source><actions xmlns="http://clicon.org/controller"/></source><nc:filter nc:type="xpath" nc:select="/devices/device[1]"/></get-config></rpc>"""

    root = netconf.rpc_config_get(xpath="/devices/device[1]")

    assert root.dumps() == xmlstr


def test_rpc_config_get_xpath_user():
    """
    Test the rpc_config_get function with custom xpath and user.
    """

    xmlstr = f"""<rpc xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" username="nisse" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="42"><get-config><source><actions xmlns="http://clicon.org/controller"/></source><nc:filter nc:type="xpath" nc:select="/devices/device[name='test']"/></get-config></rpc>"""

    root = netconf.rpc_config_get(user="nisse", xpath="/devices/device[name='test']")

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
