from unittest.mock import patch

import pytest

import clixon.args as args

from clixon.args import parse_args, get_arg, get_logger, get_sockpath, get_prettyprint
from clixon.version import __version__
import sys


@patch(
    "sys.argv",
    [
        "test",
        "-s",
        "/test/socket",
        "-p",
        "/test/pidfile",
        "-m",
        "./modules/",
        "-l" "o",
        "-d",
        "-P",
    ],
)
def test_parse_args():
    """
    Test that the arguments are parsed correctly.
    """

    sys.argv = [
        "test",
        "-m",
        "/tmp",
        "-s",
        "/test/socket",
        "-p",
        "/test/pidfile",
        "-P",
        "-l",
        "o",
        "-d",
    ]

    (sockpath, modulepaths, modulefilter, pidfile, pp, log, debug) = parse_args()

    assert sockpath == "/test/socket"
    for m_path in modulepaths:
        assert m_path == "/tmp"
    assert modulefilter == ""
    assert pidfile == "/test/pidfile"
    assert pp is True
    assert log == "o"
    assert debug is True


@patch("sys.argv", ["test"])
def test_get_logger():
    """
    Test that the logger is created correctly.
    """

    logger = get_logger()

    assert logger is not None


@patch("sys.argv", ["test", "-s", "/test/socket"])
def test_get_sockpath():
    """
    Test that the socket path is returned correctly.
    """

    assert get_sockpath() == "/test/socket"


@patch("sys.argv", ["test", "-P"])
def test_get_prettyprint():
    """
    Test that the prettyprint flag is returned correctly.
    """

    assert get_prettyprint() is True


@patch("sys.exit")
@patch("builtins.print")
def test_usage(mock_print, mock_exit):
    """
    Test that the usage function prints the correct message and exits.
    """

    parse_args(["--help"])
    mock_exit.assert_called_with(0)


def test_parse_args_configfile(tmp_path):
    """
    Test that the arguments are read from a configuration file.
    """

    config = tmp_path / "controller.xml"
    config.write_text(
        """<clixon-config xmlns="http://clicon.org/config">
        <CLICON_SOCK>/test/sock</CLICON_SOCK>
        <CONTROLLER_PYAPI_MODULE_PATH>%s</CONTROLLER_PYAPI_MODULE_PATH>
        <CONTROLLER_PYAPI_MODULE_FILTER>skipme</CONTROLLER_PYAPI_MODULE_FILTER>
        <CONTROLLER_PYAPI_PIDFILE>/test/pidfile</CONTROLLER_PYAPI_PIDFILE>
        </clixon-config>"""
        % tmp_path
    )

    (sockpath, modulepaths, modulefilter, pidfile, _, _, _) = parse_args(
        ["-f", str(config)]
    )

    assert sockpath == "/test/sock"
    assert modulepaths == [str(tmp_path)]
    assert modulefilter == "skipme"
    assert pidfile == "/test/pidfile"


def test_parse_args_missing_configfile(tmp_path):
    """
    Test that a configuration file which does not exist stops the program.
    """

    with pytest.raises(SystemExit):
        parse_args(["-f", str(tmp_path / "nosuch.xml")])


def test_parse_args_broken_configfile(tmp_path):
    """
    Test that a configuration file which can not be parsed stops the program.
    """

    config = tmp_path / "broken.xml"
    config.write_text("<clixon-config></clixon-config>")

    with pytest.raises(SystemExit):
        parse_args(["-f", str(config)])


def test_parse_args_missing_modulepath():
    """
    Test that a module path which does not exist stops the program.
    """

    with pytest.raises(SystemExit):
        parse_args(["-m", "/nosuch/path"])


def test_parse_args_version(capsys):
    """
    Test that the version is printed.
    """

    with pytest.raises(SystemExit):
        parse_args(["-V"])

    assert capsys.readouterr().out.strip() == __version__


def test_get_arg_from_configfile(tmp_path):
    """
    Test that an argument is refreshed from the configuration file.
    """

    config = tmp_path / "controller.xml"
    config.write_text(
        """<clixon-config xmlns="http://clicon.org/config">
        <CLICON_SOCK>/test/sock2</CLICON_SOCK>
        <CONTROLLER_PYAPI_MODULE_PATH>%s</CONTROLLER_PYAPI_MODULE_PATH>
        <CONTROLLER_PYAPI_MODULE_FILTER></CONTROLLER_PYAPI_MODULE_FILTER>
        <CONTROLLER_PYAPI_PIDFILE>/test/pidfile2</CONTROLLER_PYAPI_PIDFILE>
        </clixon-config>"""
        % tmp_path
    )

    args.global_args = {"configfile": str(config)}

    assert get_arg("sockpath") == "/test/sock2"
    assert get_arg("pidfile") == "/test/pidfile2"

    args.global_args = {}


def test_get_arg_unknown_option():
    """
    Test that an option which is not ours is None.
    """

    args.global_args = {}

    with patch("sys.argv", ["test", "--not-a-clixon-argument"]):
        assert get_arg("sockpath") is None

    args.global_args = {}


def test_get_arg_does_not_print_the_help_of_others(capsys):
    """
    Test that the help of another program is not printed when its arguments
    are parsed.
    """

    args.global_args = {}

    with patch("sys.argv", ["test", "--help"]):
        get_arg("log")

    output = capsys.readouterr()

    assert "clixon PyAPI" not in output.out
    assert "clixon PyAPI" not in output.err

    args.global_args = {}


def test_get_arg_without_arguments():
    """
    Test that nothing is returned when there are no arguments at all.
    """

    args.global_args = {}

    with patch("sys.argv", ["test"]):
        assert get_arg("sockpath") is None


def test_get_arg_disabled(monkeypatch):
    """
    Test that the arguments can be turned off with an environment variable.
    """

    monkeypatch.setenv("NO_CLIXON_ARGS", "1")

    assert get_arg("sockpath") is None
