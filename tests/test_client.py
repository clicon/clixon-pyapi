from unittest.mock import MagicMock, patch

import pytest

from clixon import client

HELLO = (
    '<hello xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">'
    "<session-id>42</session-id></hello>"
)

TRANSACTION = (
    '<rpc-reply xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"><data>'
    '<transactions xmlns="http://clicon.org/controller"><transaction>'
    "<tid>7</tid><username>test-user</username></transaction></transactions>"
    "</data></rpc-reply>"
)

SERVICES_COMMIT = (
    '<notification xmlns="urn:ietf:params:xml:ns:netconf:notification:1.0">'
    '<services-commit xmlns="http://clicon.org/controller"><tid>7</tid>'
    "<service>ssh-users[service-name='test']</service>"
    "</services-commit></notification>"
)

SERVICES_COMMIT_ALL = (
    '<notification xmlns="urn:ietf:params:xml:ns:netconf:notification:1.0">'
    '<services-commit xmlns="http://clicon.org/controller"><tid>7</tid>'
    "</services-commit></notification>"
)

SERVICES_COMMIT_DIFF = SERVICES_COMMIT.replace(
    "<tid>7</tid>", "<tid>7</tid><diff>true</diff>"
)

TRANSACTION_FAILED = (
    '<notification xmlns="urn:ietf:params:xml:ns:netconf:notification:1.0">'
    '<controller-transaction xmlns="http://clicon.org/controller">'
    "<tid>7</tid><result>FAILED</result></controller-transaction></notification>"
)

TRANSACTION_SUCCESS = TRANSACTION_FAILED.replace("FAILED", "SUCCESS")


@pytest.fixture(autouse=True)
def clean_transactions():
    """
    Leave the transactions of the client empty between the tests.
    """

    client.transactions.clear()

    yield

    client.transactions.clear()


def test_hello():
    """
    Test that a hello is sent and answered.
    """

    with patch("clixon.client.send") as send, patch(
        "clixon.client.read", return_value=HELLO
    ):
        assert client.hello(MagicMock(), False) == HELLO
        assert "<hello" in send.call_args[0][1].dumps()


def test_hello_invalid():
    """
    Test that a reply which is not a hello is an error.
    """

    with patch("clixon.client.send"), patch(
        "clixon.client.read", return_value="<rpc-reply/>"
    ):
        with pytest.raises(ValueError):
            client.hello(MagicMock(), False)


def test_enable_service_notify():
    """
    Test that the service subscription is created.
    """

    with patch("clixon.client.send") as send, patch(
        "clixon.client.read", return_value="<ok/>"
    ):
        client.enable_service_notify(MagicMock(), False)

    assert "<stream>services-commit</stream>" in send.call_args[0][1].dumps()


def test_enable_transaction_notify():
    """
    Test that the transaction subscription is created.
    """

    with patch("clixon.client.send") as send, patch(
        "clixon.client.read", return_value="<ok/>"
    ):
        client.enable_transaction_notify(MagicMock(), False)

    assert "<stream>controller-transaction</stream>" in send.call_args[0][1].dumps()


def test_services_commit_cb():
    """
    Test that a services-commit notification runs the modules of the service.
    """

    with patch("clixon.client.send") as send, patch(
        "clixon.client.read", return_value=TRANSACTION
    ), patch("clixon.client.run_modules") as run_modules, patch(
        "clixon.client.run_hooks"
    ) as run_hooks:
        client.services_commit_cb(
            data=SERVICES_COMMIT, sock=MagicMock(), modules=["m"], pp=False
        )

    assert run_modules.call_args[0][1:] == (["m"], "ssh-users", "test", False)
    assert run_modules.call_args[1] == {"user": "test-user"}
    run_hooks.assert_called_once()

    done = send.call_args[0][1].dumps()

    assert "transaction-actions-done" in done
    assert "<tid>7</tid>" in done
    assert "<service>ssh-users</service>" in done


def test_services_commit_cb_all_services():
    """
    Test that a notification without services runs all of them.
    """

    with patch("clixon.client.send") as send, patch(
        "clixon.client.read", return_value=TRANSACTION
    ), patch("clixon.client.run_modules") as run_modules:
        client.services_commit_cb(
            data=SERVICES_COMMIT_ALL, sock=MagicMock(), modules=["m"], pp=False
        )

    assert run_modules.call_args[0][2] is None
    assert "transaction-actions-done" in send.call_args[0][1].dumps()


def test_services_commit_cb_diff():
    """
    Test that a diff is passed on to the modules and not remembered as a
    transaction.
    """

    with patch("clixon.client.send"), patch(
        "clixon.client.read", return_value=TRANSACTION
    ), patch("clixon.client.run_modules") as run_modules, patch(
        "clixon.client.run_hooks"
    ):
        client.services_commit_cb(
            data=SERVICES_COMMIT_DIFF, sock=MagicMock(), modules=["m"], pp=False
        )

    assert run_modules.call_args[0][4] is True
    assert client.transactions == {}


def test_services_commit_cb_remembers_transaction():
    """
    Test that the services of a commit are remembered for the hooks.
    """

    with patch("clixon.client.send"), patch(
        "clixon.client.read", return_value=TRANSACTION
    ), patch("clixon.client.run_modules"), patch("clixon.client.run_hooks"):
        client.services_commit_cb(
            data=SERVICES_COMMIT, sock=MagicMock(), modules=["m"], pp=False
        )

    assert "7" in client.transactions


def test_services_commit_cb_error():
    """
    Test that a failing module is reported back to the backend.
    """

    with patch("clixon.client.send") as send, patch(
        "clixon.client.read", return_value=TRANSACTION
    ), patch("clixon.client.run_modules", side_effect=ValueError("boom")), patch(
        "clixon.client.run_hooks"
    ):
        client.services_commit_cb(
            data=SERVICES_COMMIT, sock=MagicMock(), modules=["m"], pp=False
        )

    error = send.call_args[0][1].dumps()

    assert "transaction-error" in error
    assert "<origin>pyapi</origin>" in error
    assert "boom" in error


def test_services_commit_cb_invalid_service():
    """
    Test that a service which can not be parsed is reported as an error.
    """

    data = SERVICES_COMMIT.replace("ssh-users[service-name='test']", "ssh-users")

    with patch("clixon.client.send") as send, patch(
        "clixon.client.read", return_value=TRANSACTION
    ), patch("clixon.client.run_modules"), patch("clixon.client.run_hooks"):
        client.services_commit_cb(data=data, sock=MagicMock(), modules=["m"], pp=False)

    assert "transaction-error" in send.call_args[0][1].dumps()


def test_controller_transaction_cb_success():
    """
    Test that a successful transaction runs no hooks.
    """

    with patch("clixon.client.run_hooks") as run_hooks:
        client.controller_transaction_cb(
            data=TRANSACTION_SUCCESS, sock=MagicMock(), modules=["m"]
        )

    run_hooks.assert_not_called()


def test_controller_transaction_cb_unknown():
    """
    Test that a transaction which is not ours runs no hooks.
    """

    with patch("clixon.client.run_hooks") as run_hooks:
        client.controller_transaction_cb(
            data=TRANSACTION_FAILED, sock=MagicMock(), modules=["m"]
        )

    run_hooks.assert_not_called()


def test_controller_transaction_cb_failed():
    """
    Test that a failed transaction runs the post commit failed hooks.
    """

    with patch("clixon.client.send"), patch(
        "clixon.client.read", return_value=TRANSACTION
    ), patch("clixon.client.run_modules"), patch("clixon.client.run_hooks"):
        client.services_commit_cb(
            data=SERVICES_COMMIT, sock=MagicMock(), modules=["m"], pp=False
        )

    with patch("clixon.client.run_hooks") as run_hooks:
        client.controller_transaction_cb(
            data=TRANSACTION_FAILED, sock=MagicMock(), modules=["m"]
        )

    assert run_hooks.call_args[0][2:] == ("ssh-users", "test", False, "FAILED")


def test_readloop_socket_failure():
    """
    Test that the read loop gives up when the hello fails.
    """

    with patch("clixon.client.create_socket"), patch(
        "clixon.client.hello", side_effect=ValueError("no hello")
    ):
        assert client.readloop("/tmp/test.sock", []) is None


def test_readloop_emits_events():
    """
    Test that the read loop hands the notifications to the event handler.
    """

    emitted = []

    def emit(**kwargs):
        emitted.append(kwargs["data"])

        if len(emitted) > 2:
            raise SystemExit(0)

    with patch("clixon.client.create_socket"), patch("clixon.client.hello"), patch(
        "clixon.client.enable_service_notify", return_value="<ok/>"
    ), patch("clixon.client.enable_transaction_notify", return_value="<ok/>"), patch(
        "clixon.client.read", return_value=TRANSACTION_SUCCESS
    ), patch.object(
        client.events, "emit", side_effect=emit
    ):
        with pytest.raises(SystemExit):
            client.readloop("/tmp/test.sock", [])

    assert emitted[-1] == TRANSACTION_SUCCESS
