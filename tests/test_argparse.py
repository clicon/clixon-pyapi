from unittest.mock import patch
from clixon.args import parse_args, get_logger, get_sockpath, get_prettyprint, usage


@patch("sys.argv", ["test", "-s", "/test/socket", "-p", "/test/pidfile", "-m", "./modules/", "-l" "o", "-F", "-d", "-P"])
def test_parse_args():
    """
    Test that the arguments are parsed correctly.
    """

    sockpath, modulepath, modulefilter, pidfile, foreground, pp, log, debug = parse_args()

    assert sockpath == "/test/socket"
    assert modulepath == "./modules/"
    assert modulefilter == ""
    assert pidfile == "/test/pidfile"
    assert foreground is True
    assert pp is True
    assert log == "o"
    assert debug is True


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

    usage('error message')
    mock_exit.assert_called_with(0)
