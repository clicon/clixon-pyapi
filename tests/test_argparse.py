from unittest.mock import patch
import sys

from clixon.args import (
    get_logger,
    get_sockpath,
    get_prettyprint,
    parse_args,
    __sanitize_paths
)


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


def test_sanitize_paths():
    paths = ["/usr/bin", "/usr/bin/", "/var/run", "/var/run"]
    normalized = __sanitize_paths(paths)

    assert len(normalized) == 2
    for m_path in normalized:
        assert m_path in ["/usr/bin", "/run"]
