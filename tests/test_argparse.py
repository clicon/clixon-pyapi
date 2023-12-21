from unittest.mock import patch
from clixon.args import parse_args, get_logger, get_sockpath, get_prettyprint, usage


@patch("sys.argv", ["test", "-s", "/test/socket", "-p", "/test/pidfile", "-m", "./modules/", "-l" "o", "-F", "-d", "-P"])
def test_parse_args():
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
    logger = get_logger()

    assert logger is not None


@patch("sys.argv", ["test", "-s", "/test/socket"])
def test_get_sockpath():
    assert get_sockpath() == '/test/socket'


@patch("sys.argv", ["test", "-P"])
def test_get_prettyprint():
    assert get_prettyprint() is True


@patch('sys.exit')
@patch('builtins.print')
def test_usage(mock_print, mock_exit):
    usage('error message')
    mock_exit.assert_called_with(0)
