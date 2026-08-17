from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from clixon import modules
from clixon.exceptions import ModuleError

MODULE = """
SERVICE = "{service}"

calls = []


def setup(root, log, **kwargs):
    calls.append(("setup", kwargs))


def setup_pre_commit(root, log, **kwargs):
    calls.append(("pre-commit", kwargs))


def setup_post_commit(root, log, **kwargs):
    calls.append(("post-commit", kwargs))
"""


def write_modules(path, names, extra=""):
    """
    Write a set of loadable modules and return their path.
    """

    for name in names:
        (path / f"{name}.py").write_text(MODULE.format(service=name) + extra)

    return str(path)


def fake_clixon():
    """
    Patch the Clixon object of the modules module and return it.
    """

    clx = MagicMock()
    clx.__enter__ = MagicMock(return_value=clx)
    clx.__exit__ = MagicMock(return_value=False)

    return clx


def module(service, **attributes):
    """
    Return a module like object.
    """

    calls = []

    def record(name):
        def hook(root, log, **kwargs):
            calls.append((name, kwargs))

        return hook

    fake = SimpleNamespace(SERVICE=service, setup=record("setup"), calls=calls)

    for name, value in attributes.items():
        setattr(fake, name, record(name) if value is True else value)

    return fake


def test_find_modules(tmp_path):
    """
    Test that the modules of a directory are found.
    """

    path = write_modules(tmp_path, ["a", "b"])
    (tmp_path / "c.txt").write_text("not a module")
    (tmp_path / "d.py~").write_text("a backup file")
    (tmp_path / "#e.py").write_text("an editor file")

    found = modules.find_modules(path)

    assert sorted(f.split("/")[-1] for f in found) == ["a.py", "b.py"]


def test_find_modules_recursive(tmp_path):
    """
    Test that the modules of a subdirectory are found with their path.
    """

    subdir = tmp_path / "sub"
    subdir.mkdir()
    write_modules(tmp_path, ["a"])
    write_modules(subdir, ["b"])

    found = modules.find_modules(str(tmp_path))

    assert str(subdir / "b.py") in found
    assert str(tmp_path / "a.py") in found


def test_find_modules_empty(tmp_path):
    """
    Test that a directory without modules gives no modules.
    """

    assert modules.find_modules(str(tmp_path)) == []


def test_load_modules(tmp_path):
    """
    Test that the modules of a directory are loaded.
    """

    path = write_modules(tmp_path, ["mod_a", "mod_b"])
    loaded = modules.load_modules(path, "")

    assert sorted(m.SERVICE for m in loaded) == ["mod_a", "mod_b"]


def test_load_modules_filter(tmp_path):
    """
    Test that filtered modules are skipped.
    """

    path = write_modules(tmp_path, ["mod_c", "mod_d"])
    loaded = modules.load_modules(path, "mod_c")

    assert [m.SERVICE for m in loaded] == ["mod_d"]


def test_load_modules_without_service(tmp_path):
    """
    Test that a module without a SERVICE attribute is not loaded.
    """

    (tmp_path / "mod_e.py").write_text("def setup(root, log, **kwargs):\n    pass\n")

    assert modules.load_modules(str(tmp_path), "") == []


def test_load_modules_without_setup(tmp_path):
    """
    Test that a module without a setup function is not loaded.
    """

    (tmp_path / "mod_f.py").write_text('SERVICE = "mod_f"\n')

    assert modules.load_modules(str(tmp_path), "") == []


def test_load_modules_broken(tmp_path):
    """
    Test that a module which does not import is skipped.
    """

    (tmp_path / "mod_g.py").write_text("this is not python")

    assert modules.load_modules(str(tmp_path), "") == []


def test_run_modules():
    """
    Test that the setup function of a module is run.
    """

    mod = module("test")
    clx = fake_clixon()

    with patch("clixon.modules.Clixon", return_value=clx):
        modules.run_modules(None, [mod], "test", "instance1")

    assert mod.calls == [("setup", {"instance": "instance1", "diff": False})]


def test_run_modules_other_service():
    """
    Test that a module of another service is skipped.
    """

    mod = module("test")
    clx = fake_clixon()

    with patch("clixon.modules.Clixon", return_value=clx):
        modules.run_modules(None, [mod], "other", "instance1")

    assert mod.calls == []


def test_run_modules_none():
    """
    Test that no modules is not an error.
    """

    assert modules.run_modules(None, [], "test", "instance1") is None


def test_run_modules_xpath():
    """
    Test that a module with a service xpath gets a filtered root.
    """

    mod = module(
        "test",
        SERVICE_XPATH="/ctrl:services",
        SERVICE_NAMESPACES='xmlns:ctrl="http://clicon.org/controller"',
    )
    clx = fake_clixon()

    with patch("clixon.modules.Clixon", return_value=clx):
        modules.run_modules(None, [mod], "test", "instance1")

    clx.get_root.assert_called_with(
        xpath="/ctrl:services",
        namespaces='xmlns:ctrl="http://clicon.org/controller"',
    )


def test_run_modules_exception():
    """
    Test that a failing module raises a module error.
    """

    def fail(root, log, **kwargs):
        raise ValueError("boom")

    mod = SimpleNamespace(SERVICE="test", setup=fail)
    clx = fake_clixon()

    with patch("clixon.modules.Clixon", return_value=clx):
        with pytest.raises(ModuleError):
            modules.run_modules(None, [mod], "test", "instance1")


def test_run_hooks():
    """
    Test that the hooks of a module are run.
    """

    mod = module("test", setup_pre_commit=True, setup_post_commit=True)
    clx = fake_clixon()

    with patch("clixon.modules.Clixon", return_value=clx):
        modules.run_hooks(None, [mod], "test", "instance1", False, "pre-commit")
        modules.run_hooks(None, [mod], "test", "instance1", False, "SUCCESS")

    assert [c[0] for c in mod.calls] == ["setup_pre_commit", "setup_post_commit"]


def test_run_hooks_without_hooks():
    """
    Test that a module without hooks is not run.
    """

    mod = module("test")
    clx = fake_clixon()

    with patch("clixon.modules.Clixon", return_value=clx) as clixon:
        modules.run_hooks(None, [mod], "test", "instance1", False, "pre-commit")

    assert mod.calls == []
    clixon.assert_not_called()


def test_run_hooks_none():
    """
    Test that no modules is not an error.
    """

    assert modules.run_hooks(None, [], "test", "instance1", False, "pre-commit") is None


def test_run_hooks_post_commit_failed():
    """
    Test that a failed transaction runs the post commit failed hook.
    """

    mod = module("test", setup_post_commit_failed=True)
    clx = fake_clixon()

    with patch("clixon.modules.Clixon", return_value=clx):
        modules.run_hooks(None, [mod], "test", "instance1", False, "FAILED")

    assert [c[0] for c in mod.calls] == ["setup_post_commit_failed"]


def test_run_hooks_other_service():
    """
    Test that the hooks of another service are not run.
    """

    mod = module("test", setup_pre_commit=True)
    other = module("other", setup_pre_commit=True)
    clx = fake_clixon()

    with patch("clixon.modules.Clixon", return_value=clx):
        modules.run_hooks(None, [mod, other], "test", "instance1", False, "pre-commit")

    assert [c[0] for c in mod.calls] == ["setup_pre_commit"]
    assert other.calls == []


def test_run_hooks_xpath():
    """
    Test that a module with a service xpath gets a filtered root.
    """

    mod = module(
        "test",
        setup_pre_commit=True,
        SERVICE_XPATH="/ctrl:services",
        SERVICE_NAMESPACES='xmlns:ctrl="http://clicon.org/controller"',
    )
    clx = fake_clixon()

    with patch("clixon.modules.Clixon", return_value=clx):
        modules.run_hooks(None, [mod], "test", "instance1", False, "pre-commit")

    clx.get_root.assert_called_with(
        xpath="/ctrl:services",
        namespaces='xmlns:ctrl="http://clicon.org/controller"',
    )


def test_run_hooks_exception():
    """
    Test that a failing hook raises a module error.
    """

    def fail(root, log, **kwargs):
        raise ValueError("boom")

    mod = SimpleNamespace(SERVICE="test", setup=fail, setup_pre_commit=fail)
    clx = fake_clixon()

    with patch("clixon.modules.Clixon", return_value=clx):
        with pytest.raises(ModuleError):
            modules.run_hooks(None, [mod], "test", "instance1", False, "pre-commit")
