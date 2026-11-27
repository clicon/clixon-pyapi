import types
from unittest.mock import MagicMock

import pytest

import clixon.client as client_module
import clixon.clixon as clixon_module
from clixon.clixon import Clixon
from clixon.element import Element
from clixon.modules import ModuleSession, run_hooks, run_modules

REPLY = (
    '<rpc-reply xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"><data>'
    '<services xmlns="http://clicon.org/controller">'
    "<svc><service-name>i1</service-name></svc>"
    "<svc><service-name>i2</service-name></svc>"
    "</services>"
    '<devices xmlns="http://clicon.org/controller">'
    "<device><name>r0</name><config><system><host-name>r0</host-name></system>"
    "</config></device>"
    "</devices>"
    "</data></rpc-reply>"
)

OK = '<rpc-reply xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"><ok/></rpc-reply>'

TRANSACTION_REPLY = (
    '<rpc-reply xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"><data>'
    '<transactions xmlns="http://clicon.org/controller"><transaction>'
    "<tid>7</tid><username>alice</username>"
    "</transaction></transactions>"
    "</data></rpc-reply>"
)


@pytest.fixture
def backend(monkeypatch):
    """
    Replace the socket calls, record what is sent and answer get-config with
    REPLY, the transaction lookup with TRANSACTION_REPLY and the rest with ok.
    """

    sent = []

    def send(sock, data, pp=False):
        if isinstance(data, Element):
            data = data.dumps()
        sent.append(data)

    def read(sock, pp=False, standalone=False):
        if "<get-config" in sent[-1]:
            return REPLY
        if "co:transactions" in sent[-1]:
            return TRANSACTION_REPLY
        return OK

    for module in (clixon_module, client_module):
        monkeypatch.setattr(module, "send", send)
        monkeypatch.setattr(module, "read", read)

    return sent


def get_configs(sent):
    return [s for s in sent if "<get-config" in s]


def edit_configs(sent):
    return [s for s in sent if "<edit-config>" in s]


def module(name, setup=None, service="svc", **attributes):
    """
    Create a service module whose setup() creates a leaf named after the
    module and the instance under the device's system.
    """

    def default_setup(root, log, instance=None, **kwargs):
        root.devices.device.config.system.create(f"{name}-{instance}", data="x")

    mod = types.ModuleType(name)
    mod.SERVICE = service
    mod.setup = setup or default_setup

    for key, value in attributes.items():
        setattr(mod, key, value)

    return mod


# Clixon with several trees


def test_clixon_writes_every_modified_tree(backend):
    with Clixon(socket=MagicMock(), from_server=True, prune=True) as cd:
        first = cd.get_root()
        second = cd.get_root(xpath="/devices")
        first.devices.device.config.system.create("a", data="1")
        second.devices.device.config.system.create("b", data="2")

    edits = edit_configs(backend)

    assert len(edits) == 2
    assert "<a>1</a>" in edits[0]
    assert "<b>2</b>" in edits[1]


def test_clixon_same_view_replaces_unmodified_tree(backend):
    with Clixon(socket=MagicMock(), from_server=True, prune=False) as cd:
        cd.get_root()
        cd.get_root()

    # Without prune the last tree is sent, the replaced one is not
    assert len(edit_configs(backend)) == 1


def test_clixon_same_view_keeps_modified_tree(backend):
    with Clixon(socket=MagicMock(), from_server=True, prune=True) as cd:
        cd.get_root().devices.device.config.system.create("a", data="1")
        cd.get_root().devices.device.config.system.create("b", data="2")

    edits = edit_configs(backend)

    assert len(edits) == 2
    assert "<a>1</a>" in edits[0]
    assert "<b>2</b>" in edits[1]


def test_clixon_without_prune_skips_unmodified_earlier_tree(backend):
    with Clixon(socket=MagicMock(), from_server=True, prune=False) as cd:
        cd.get_root(xpath="/services")
        cd.get_root()

    (edit,) = edit_configs(backend)

    assert "<devices" in edit


def test_clixon_without_prune_sends_modified_earlier_tree(backend):
    with Clixon(socket=MagicMock(), from_server=True, prune=False) as cd:
        cd.get_root(xpath="/services").devices.device.config.system.create("a")
        cd.get_root()

    assert len(edit_configs(backend)) == 2


def test_clixon_write_back_false_is_not_written(backend):
    with Clixon(socket=MagicMock(), from_server=True, prune=True) as cd:
        root = cd.get_root(write_back=False)
        root.devices.device.config.system.create("a", data="1")

    assert edit_configs(backend) == []


# ModuleSession


def test_two_modules_same_service_both_written(backend):
    """
    Each module used to fetch its own tree and only the last one was written
    back, so the first module's changes were lost.
    """

    run_modules(MagicMock(), [module("a"), module("b")], "svc", "i1")

    (edit,) = edit_configs(backend)

    assert "<a-i1>x</a-i1>" in edit
    assert "<b-i1>x</b-i1>" in edit
    assert len(get_configs(backend)) == 1


def test_run_all_modules_shares_tree(backend):
    """
    Without services in the commit all modules are run, for all services.
    """

    modules = [module("a"), module("b", service="other")]
    run_modules(MagicMock(), modules, None, None)

    (edit,) = edit_configs(backend)

    assert "<a-None>x</a-None>" in edit
    assert "<b-None>x</b-None>" in edit
    assert len(get_configs(backend)) == 1


def test_session_shared_between_instances(backend):
    sock = MagicMock()

    with ModuleSession(sock) as session:
        for instance in ("i1", "i2"):
            run_modules(sock, [module("a")], "svc", instance, session=session)

    (edit,) = edit_configs(backend)

    assert "<a-i1>x</a-i1>" in edit
    assert "<a-i2>x</a-i2>" in edit
    assert len(get_configs(backend)) == 1


def test_session_hooks_and_modules_share_tree(backend):
    def pre_commit(root, log, instance=None, **kwargs):
        root.devices.device.config.system.create("hook", data="x")

    def setup(root, log, instance=None, **kwargs):
        # The module sees what the hook did
        assert root.devices.device.config.system.hook.get_data() == "x"
        root.devices.device.config.system.create("setup", data="x")

    mod = module("a", setup=setup, setup_pre_commit=pre_commit)
    sock = MagicMock()

    with ModuleSession(sock) as session:
        run_hooks(sock, [mod], "svc", "i1", False, "pre-commit", session=session)
        run_modules(sock, [mod], "svc", "i1", session=session)

    (edit,) = edit_configs(backend)

    assert "<hook>x</hook>" in edit
    assert "<setup>x</setup>" in edit
    assert len(get_configs(backend)) == 1


def test_session_one_fetch_per_view(backend):
    a = module("a")
    b = module("b", SERVICE_XPATH="/devices", SERVICE_NAMESPACES={})
    c = module("c")

    run_modules(MagicMock(), [a, b, c], "svc", "i1")

    gets = get_configs(backend)
    edits = edit_configs(backend)

    assert len(gets) == 2
    assert len(edits) == 2
    assert "<a-i1>x</a-i1>" in edits[0]
    assert "<c-i1>x</c-i1>" in edits[0]
    assert "<b-i1>x</b-i1>" in edits[1]


def test_session_without_matching_modules_sends_nothing(backend):
    """
    No module ran, so the configuration is neither fetched nor sent back.
    """

    run_modules(MagicMock(), [module("a", service="other")], "svc", "i1")

    assert backend == []


def test_session_writes_on_module_error(backend):
    """
    As before, changes made before a module fails are written when the
    session exits, and the error is raised.
    """

    def fail(root, log, **kwargs):
        raise ValueError("boom")

    with pytest.raises(Exception, match="boom"):
        run_modules(MagicMock(), [module("a"), module("b", setup=fail)], "svc", "i1")

    (edit,) = edit_configs(backend)

    assert "<a-i1>x</a-i1>" in edit


# services_commit_cb


def services_commit(*instances):
    services = "".join(
        f"<service>svc[service-name='{instance}']</service>" for instance in instances
    )

    return (
        '<notification xmlns="urn:ietf:params:xml:ns:netconf:notification:1.0">'
        '<services-commit xmlns="http://clicon.org/controller">'
        f"<tid>7</tid>{services}"
        "</services-commit></notification>"
    )


def test_services_commit_fetches_once_for_all_instances(backend):
    modules = [module("a"), module("b")]

    client_module.services_commit_cb(
        data=services_commit("i1", "i2", "i3"),
        sock=MagicMock(),
        modules=modules,
        pp=False,
    )

    gets = get_configs(backend)
    (edit,) = edit_configs(backend)

    assert len(gets) == 1
    assert 'username="alice"' in gets[0]

    for instance in ("i1", "i2", "i3"):
        assert f"<a-{instance}>x</a-{instance}>" in edit
        assert f"<b-{instance}>x</b-{instance}>" in edit

    assert "<transaction-actions-done" in backend[-1]
    assert "<service>svc</service>" in backend[-1]


def test_services_commit_module_error_is_reported(backend):
    def fail(root, log, **kwargs):
        raise ValueError("boom")

    client_module.services_commit_cb(
        data=services_commit("i1"),
        sock=MagicMock(),
        modules=[module("a", setup=fail)],
        pp=False,
    )

    assert "<transaction-error" in backend[-1]
    assert "boom" in backend[-1]
