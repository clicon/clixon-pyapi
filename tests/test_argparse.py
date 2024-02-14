import os
import tempfile
from unittest.mock import patch

from clixon.args import parse_args, get_arg


def test_parse_args():
    """
    Test that the arguments are parsed correctly.
    """
    with tempfile.TemporaryDirectory() as tmp_file:
        (
            sockpath,
            modulepaths,
            modulefilter,
            pidfile,
            foreground,
            pp,
            log,
            debug
        ) = parse_args(
            ["-s", "/test/socket",
             "-p", "/test/pidfile",
             "-m", tmp_file,
             "-l" "o",
             "-F", "-d", "-P"])
        assert sockpath == "/test/socket"
        for m_path in modulepaths:
            assert m_path in ["/usr/local/share/clixon/controller/modules/",
                              tmp_file]
        assert modulefilter == ""
        assert pidfile == "/test/pidfile"
        assert foreground is True
        assert pp is True
        assert log == "o"
        assert debug is True


@patch("sys.argv", ["test", "-s", "/test/socket"])
def test_get_sockpath():
    """
    Test that the socket path is returned correctly.
    """

    parse_args()
    assert get_arg("sockpath") == '/test/socket'


@patch('sys.exit')
@patch('builtins.print')
def test_usage(mock_print, mock_exit):
    """
    Test that the usage function prints the correct message and exits.
    """

    parse_args(["--help"])
    mock_exit.assert_called_with(0)
