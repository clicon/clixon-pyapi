from pytest import  raises
from unittest.mock import patch
import sys

from clixon import __version__
from clixon.args import parse_args, get_logger, get_sockpath, get_prettyprint


@patch("sys.argv", [
    "test", "-s", "/test/socket", "-p", "/test/pidfile", "-m", "./modules/",
    "-l" "o", "-F", "-d", "-P"])
def test_parse_args():
    """
    Test that the arguments are parsed correctly.
    """

    sys.argv = [
        "test",
        "-m", "/tmp",
        "-s", "/test/socket",
        "-p", "/test/pidfile",
        "-F",
        "-P",
        "-l", "o",
        "-d"
    ]

    (
        sockpath,
        modulepaths,
        modulefilter,
        pidfile,
        foreground,
        pp,
        log,
        debug
    ) = parse_args()

    assert sockpath == "/test/socket"
    for m_path in modulepaths:
        assert m_path == "/tmp"
    assert modulefilter == ""
    assert pidfile == "/test/pidfile"
    assert foreground is True
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

    assert get_sockpath() == '/test/socket'


@patch("sys.argv", ["test", "-P"])
def test_get_prettyprint():
    """
    Test that the prettyprint flag is returned correctly.
    """

    assert get_prettyprint() is True


@patch('sys.exit')
@patch('builtins.print')
def test_usage(mock_print, mock_exit):
    """
    Test that the usage function prints the correct message and exits.
    """

    parse_args(["--help"])
    mock_exit.assert_called_with(0)


def test_version(capsys):
    """
    Test version prints and exits.
    """
    with raises(SystemExit) as exc_info:
        parse_args(["--version"])
    assert exc_info.value.code == 0
    out, err = capsys.readouterr()
    assert out.strip() == __version__
    assert err == ""
