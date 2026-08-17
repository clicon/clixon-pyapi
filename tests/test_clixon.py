from unittest.mock import MagicMock, patch

import pytest

from clixon.clixon import Clixon, rpc
from clixon.element import Element
from clixon.exceptions import RPCError, TransactionError

OK = '<rpc-reply xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"><ok/></rpc-reply>'

SERVICES = (
    '<rpc-reply xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"><data>'
    '<services xmlns="http://clicon.org/controller">'
    "<ssh-users><service-name>test</service-name></ssh-users>"
    "</services></data></rpc-reply>"
)

DEVICES = (
    '<rpc-reply xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"><data>'
    '<devices xmlns="http://clicon.org/controller">'
    "<device><name>r1</name><conn-state>OPEN</conn-state></device>"
    "</devices></data></rpc-reply>"
)

NOTIFICATION = (
    '<notification xmlns="urn:ietf:params:xml:ns:netconf:notification:1.0">'
    '<controller-transaction xmlns="http://clicon.org/controller">'
    "<tid>42</tid><result>SUCCESS</result>"
    "</controller-transaction></notification>"
)

FAILED = (
    '<notification xmlns="urn:ietf:params:xml:ns:netconf:notification:1.0">'
    '<controller-transaction xmlns="http://clicon.org/controller">'
    "<tid>42</tid><result>FAILED</result>"
    "</controller-transaction></notification>"
)

ERROR = (
    '<rpc-reply xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"><rpc-error>'
    "<error-tag>operation-failed</error-tag>"
    "<error-message>Something went wrong</error-message>"
    "</rpc-error></rpc-reply>"
)

DIFF = (
    '<rpc-reply xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">'
    '<diff xmlns="http://clicon.org/controller">+ hostname foo</diff>'
    "</rpc-reply>"
)

SCHEMAS = (
    '<rpc-reply xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"><data>'
    '<netconf-state xmlns="urn:ietf:params:xml:ns:yang:ietf-netconf-monitoring">'
    "<schemas><schema><identifier>ssh-users</identifier>"
    "<version>2023-05-22</version><format>yang</format>"
    "<namespace>http://clicon.org/ssh-users</namespace></schema></schemas>"
    "</netconf-state></data></rpc-reply>"
)


def clixon(read_values, **kwargs):
    """
    Return a Clixon object reading the given replies, and the patched send and
    read functions.
    """

    patches = {
        "create_socket": patch("clixon.clixon.create_socket"),
        "send": patch("clixon.clixon.send"),
        "read": patch("clixon.clixon.read"),
    }

    started = {name: p.start() for name, p in patches.items()}
    started["read"].side_effect = list(read_values)

    clx = Clixon(sockpath="/tmp/test.sock", **kwargs)

    return clx, started["send"], started["read"]


@pytest.fixture(autouse=True)
def stop_patches():
    """
    Stop the patches started by the clixon helper.
    """

    yield

    patch.stopall()


def sent(send, call=-1):
    """
    Return the XML of a call to send.
    """

    return send.call_args_list[call][0][1].dumps()


def test_invalid_socket():
    """
    Test that a missing default socket is an error.
    """

    with patch("os.path.exists", return_value=False):
        with pytest.raises(ValueError):
            Clixon()


def test_given_socket():
    """
    Test that an already connected socket is used as it is.
    """

    with patch("clixon.clixon.create_socket") as create_socket:
        sock = MagicMock()
        clx = Clixon(socket=sock)

        assert clx is not None
        create_socket.assert_not_called()


def test_commit():
    """
    Test that a commit is sent.
    """

    clx, send, _ = clixon([OK])
    clx.commit()

    assert "<commit/>" in sent(send)


def test_commit_read_only():
    """
    Test that a commit is not sent in read only mode.
    """

    clx, send, _ = clixon([], read_only=True)
    clx.commit()

    send.assert_not_called()


def test_commit_error():
    """
    Test that an error from the backend is raised.
    """

    clx, _, _ = clixon([ERROR])

    with pytest.raises(RPCError):
        clx.commit()


def test_commit_and_push():
    """
    Test that a commit pushes when the object is created with push.
    """

    clx, send, _ = clixon([OK, OK, NOTIFICATION], push=True)
    clx.commit()

    assert "controller-commit" in sent(send)
    assert "<push>COMMIT</push>" in sent(send)


def test_close_session():
    """
    Test that a session is closed.
    """

    clx, send, _ = clixon([OK])
    clx.close_session()

    assert "<close-session/>" in sent(send)


def test_close_session_unexpected_reply():
    """
    Test that an unexpected reply to a close-session is an error.
    """

    clx, _, _ = clixon(["<rpc-reply/>"])

    with pytest.raises(ValueError):
        clx.close_session()


def test_get_root():
    """
    Test that the root object is returned.
    """

    clx, send, _ = clixon([SERVICES])
    root = clx.get_root()

    assert "get-config" in sent(send)
    assert root.services.ssh_users.service_name == "test"


def test_get_root_xpath():
    """
    Test that an xpath and its namespaces end up in the filter.
    """

    clx, send, _ = clixon([SERVICES])
    clx.get_root(
        xpath="/ctrl:services/l2c:l2c", namespaces={"l2c": "http://example.com/l2c"}
    )

    assert 'nc:select="/ctrl:services/l2c:l2c"' in sent(send)
    assert 'xmlns:l2c="http://example.com/l2c"' in sent(send)


def test_get_root_path():
    """
    Test that a path returns the element it points at.
    """

    clx, _, _ = clixon([SERVICES])
    element = clx.get_root(path="services/ssh-users")

    assert element.service_name == "test"


def test_set_root():
    """
    Test that the root object is written to the candidate datastore.
    """

    root = Element()
    root.create("services").create("ssh-users").create("service-name", data="test")

    clx, send, _ = clixon([OK], target="candidate")
    clx.set_root(root)

    assert "edit-config" in sent(send)
    assert "<candidate/>" in sent(send)
    assert "<service-name>test</service-name>" in sent(send)


def test_set_root_read_only():
    """
    Test that nothing is written in read only mode.
    """

    clx, send, _ = clixon([], read_only=True)
    clx.set_root(Element())

    send.assert_not_called()


def test_pull():
    """
    Test that a pull is sent and waited for.
    """

    clx, send, _ = clixon([OK, NOTIFICATION])
    clx.pull(device="r1")

    assert "config-pull" in sent(send)
    assert "<device>r1</device>" in sent(send)


def test_pull_transient():
    """
    Test that a transient pull is marked as such.
    """

    clx, send, _ = clixon([OK, NOTIFICATION])
    clx.pull(transient=True)

    assert "<transient>true</transient>" in sent(send)


def test_pull_failed():
    """
    Test that a failed transaction is raised.
    """

    clx, _, _ = clixon([OK, FAILED])

    with pytest.raises((TransactionError, RPCError)):
        clx.pull()


def test_push():
    """
    Test that a push is sent.
    """

    clx, send, _ = clixon([OK, NOTIFICATION])
    clx.push()

    assert "controller-commit" in sent(send)


def test_push_read_only():
    """
    Test that nothing is pushed in read only mode.
    """

    clx, send, _ = clixon([], read_only=True)
    clx.push()

    send.assert_not_called()


def test_rollback():
    """
    Test that the changes are discarded.
    """

    clx, send, _ = clixon([OK])
    clx.rollback()

    assert "<discard-changes/>" in sent(send)


def test_lock_and_unlock():
    """
    Test that a datastore is locked and unlocked.
    """

    clx, send, _ = clixon([OK, OK])
    clx.lock()

    assert "<lock><target><candidate/></target></lock>" in sent(send)

    clx.unlock("running")

    assert "<unlock><target><running/></target></unlock>" in sent(send)


def test_show_transactions():
    """
    Test that the transactions are fetched.
    """

    clx, send, _ = clixon(["<rpc-reply><data/></rpc-reply>"])
    clx.show_transactions(tid=7)

    assert "co:transaction[co:tid='7']" in sent(send)


def test_show_devices():
    """
    Test that the devices are fetched.
    """

    clx, send, _ = clixon([DEVICES])
    data = clx.show_devices()

    assert "co:devices/co:device/co:name" in sent(send)
    assert "<name>r1</name>" in data


def test_show_compare():
    """
    Test that the compare is stripped of its rpc-reply.
    """

    clx, send, _ = clixon([DIFF])
    data = clx.show_compare()

    assert "datastore-diff" in sent(send)
    assert data == "+ hostname foo"


def test_show_devices_diff():
    """
    Test that the devices are pulled and compared.
    """

    reply = (
        '<rpc-reply xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">'
        '<diff xmlns="http://clicon.org/controller">'
        "r1:\n- hostname a\n+ hostname b\n</diff></rpc-reply>"
    )

    clx, _, _ = clixon([OK, NOTIFICATION, reply])
    diff = clx.show_devices_diff(dict_format=True)

    assert diff == {"r1": "- hostname a\n+ hostname b\n\n"}


def test_show_devices_diff_empty():
    """
    Test that no difference is an empty result.
    """

    empty = '<rpc-reply xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"></rpc-reply>'

    clx, _, _ = clixon([OK, NOTIFICATION, empty])

    assert clx.show_devices_diff() is None
    assert clx.show_devices_diff.__doc__ is not None


def test_connection_open():
    """
    Test that a connection is opened.
    """

    clx, send, _ = clixon([OK, NOTIFICATION, DIFF])
    clx.connection_open(devname="r1")

    assert "connection-change" in sent(send)
    assert "<operation>OPEN</operation>" in sent(send)


def test_connection_open_failure():
    """
    Test that a failed connection returns None.
    """

    clx, _, _ = clixon([OK, FAILED])

    assert clx.connection_open() is None


def test_apply_service():
    """
    Test that a service is applied and its diff returned.
    """

    clx, send, _ = clixon([OK, NOTIFICATION, DIFF])
    diff = clx.apply_service("ssh-users", "test")

    assert "<service-instance>ssh-users[service-name='test']</service-instance>" in (
        send.call_args_list[1][0][1].dumps()
    )
    assert diff == "+ hostname foo"


def test_apply_service_read_only():
    """
    Test that a service can only be applied with a diff in read only mode.
    """

    clx, _, _ = clixon([], read_only=True)

    with pytest.raises(ValueError):
        clx.apply_service("ssh-users", "test", diff=False)


def test_apply_template():
    """
    Test that a configuration template is applied.
    """

    clx, send, _ = clixon([OK, OK])
    clx.apply_template(devname="r1", template="test", variables={"a": "b"})

    assert "device-template-apply" in sent(send)
    assert "<type>CONFIG</type>" in sent(send)
    assert "<name>a</name><value>b</value>" in sent(send)


def test_apply_template_group():
    """
    Test that a template can be applied to a device group.
    """

    clx, send, _ = clixon([OK, OK])
    clx.apply_template(groupname="group1", template="test")

    assert "<device-group>group1</device-group>" in sent(send)


def test_apply_template_arguments():
    """
    Test that a device or a device group is required.
    """

    clx, _, _ = clixon([])

    with pytest.raises(ValueError):
        clx.apply_template(template="test")

    with pytest.raises(ValueError):
        clx.apply_template(devname="r1", groupname="group1", template="test")


def test_apply_template_failed():
    """
    Test that a template which is not applied is an error.
    """

    clx, _, _ = clixon([OK, "<rpc-reply></rpc-reply>"])

    with pytest.raises(ValueError):
        clx.apply_template(devname="r1", template="test")


def test_device_rpc():
    """
    Test that a RPC template is applied and its result returned.
    """

    result = (
        '<rpc-reply xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">'
        '<devices xmlns="http://clicon.org/controller">'
        "<device><name>r1</name><config>ok</config></device>"
        "</devices></rpc-reply>"
    )

    clx, send, _ = clixon([OK, NOTIFICATION, result])
    devices = clx.device_rpc(devname="r1", template="test")

    assert "<type>RPC</type>" in send.call_args_list[1][0][1].dumps()
    assert devices.device.name == "r1"


def test_device_rpc_arguments():
    """
    Test that a device or a device group is required.
    """

    clx, _, _ = clixon([])

    with pytest.raises(ValueError):
        clx.device_rpc(template="test")

    with pytest.raises(ValueError):
        clx.device_rpc(devname="r1", groupname="group1", template="test")


def test_get_schemas():
    """
    Test that the schemas of the backend are returned.
    """

    clx, send, _ = clixon([SCHEMAS])
    schemas = clx.get_schemas()

    assert "/ncm:netconf-state/ncm:schemas" in sent(send)
    assert schemas == [
        {
            "identifier": "ssh-users",
            "version": "2023-05-22",
            "format": "yang",
            "namespace": "http://clicon.org/ssh-users",
        }
    ]


def test_get_service_yang():
    """
    Test that the YANG of a module is returned.
    """

    reply = (
        '<rpc-reply xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">'
        '<data xmlns="urn:ietf:params:xml:ns:yang:ietf-netconf-monitoring">'
        "module ssh-users {\n    description &quot;a &lt; b&quot;;\n}"
        "</data></rpc-reply>"
    )

    clx, send, _ = clixon([reply])
    text = clx.get_service_yang("ssh-users", revision="2023-05-22")

    assert "<identifier>ssh-users</identifier>" in sent(send)
    assert "<version>2023-05-22</version>" in sent(send)
    assert text == 'module ssh-users {\n    description "a < b";\n}'


def test_get_service_yang_cdata():
    """
    Test that YANG wrapped in CDATA is unwrapped.
    """

    reply = (
        '<rpc-reply xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">'
        "<data><![CDATA[module foo { }]]></data></rpc-reply>"
    )

    clx, _, _ = clixon([reply])

    assert clx.get_service_yang("foo") == "module foo { }"


def test_get_service_yang_error():
    """
    Test that a module the backend does not have is an error.
    """

    clx, _, _ = clixon([ERROR])

    with pytest.raises(RPCError):
        clx.get_service_yang("nosuch")


def test_get_service_yang_without_data():
    """
    Test that a reply without a schema is an error.
    """

    clx, _, _ = clixon(["<rpc-reply></rpc-reply>"])

    with pytest.raises(ValueError):
        clx.get_service_yang("nosuch")


def test_get_logger():
    """
    Test that the logger of the object is returned.
    """

    clx, _, _ = clixon([])

    assert clx.get_logger() is not None


def test_context_manager():
    """
    Test that the configuration is written and committed on exit.
    """

    clx, send, _ = clixon([SERVICES, OK, OK], commit=True)

    with clx:
        pass

    assert "edit-config" in send.call_args_list[1][0][1].dumps()
    assert "<commit/>" in send.call_args_list[2][0][1].dumps()


def test_context_manager_read_only():
    """
    Test that nothing is written on exit in read only mode.
    """

    clx, send, _ = clixon([OK], read_only=True)

    with clx:
        pass

    # Only the close-session of the exit.
    assert len(send.call_args_list) == 1
    assert "<close-session/>" in sent(send)


def test_context_manager_pull():
    """
    Test that the devices are pulled on entry.
    """

    clx, send, _ = clixon([OK, NOTIFICATION, OK], pull=True, read_only=True)

    with clx:
        pass

    assert "config-pull" in send.call_args_list[1][0][1].dumps()


def test_cron():
    """
    Test that cron mode reads from the running datastore.
    """

    clx, send, _ = clixon([SERVICES], cron=True)
    clx.get_root()

    assert "<source><running/></source>" in sent(send)


def test_rpc_decorator():
    """
    Test that the rpc decorator hands a Clixon object to the function.
    """

    with patch("clixon.clixon.create_socket"), patch("clixon.clixon.send"), patch(
        "clixon.clixon.read", side_effect=[SERVICES, "<rpc-reply/>"]
    ):

        @rpc(sockpath="/tmp/test.sock")
        def func(root, log, **kwargs):
            return root.get_root()

        assert func().services.ssh_users.service_name == "test"
