import sys
import tempfile
from unittest.mock import patch

from clixon.args import parse_args, get_arg


def test_parse_args():
    """
    Test that the arguments are parsed correctly.
    """
    with tempfile.TemporaryDirectory() as tmp_file:
        sys.argv = [
            "test",
            "-m", tmp_file,
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
            assert m_path == tmp_file
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


@patch("sys.argv", ["test", "-P"])
def test_get_prettyprint():
    """
    Test that the pretty print is returned correctly.
    """

    parse_args()
    assert get_arg("pp") is True


@patch("sys.argv", ["test"])
def test_modulepath_fallback():
    """
    Test that fallback module path is added when no modulepath is provided.
    """

    fallback_mpath = "/usr/local/share/clixon/controller/modules"
    parse_args()
    mpaths = get_arg("modulepaths")
    assert mpaths == [fallback_mpath]
    assert len(mpaths) == 1


@patch("sys.argv", ["test", "-m", "/tmp"])
def test_modulepath_argument():
    """
    Test that
    - argument is added,
    - fallback module path is not added.
    """

    parse_args()
    mpaths = get_arg("modulepaths")
    assert mpaths == ["/tmp"]
    assert len(mpaths) == 1


@patch("sys.argv", ["test", "-f", "dummy_config_file"])
def test_modulepath_configfile(mocker):
    """
    Test that
    - configfile modulpath is added,
    - fallback module path is not added.
    """
    mock_path_exist = mocker.patch("os.path.exists")
    mock_path_exist.return_value = True
    mock_conf_parser = mocker.patch("clixon.args.__parse_config_file")
    mock_conf_parser.return_value = ("a", ["/tmp/conf_file_mpath"], "b", "c")

    parse_args()
    mpaths = get_arg("modulepaths")
    assert mpaths == ["/tmp/conf_file_mpath"]
    assert len(mpaths) == 1


@patch('sys.exit')
@patch('builtins.print')
def test_usage(mock_print, mock_exit):
    """
    Test that the usage function prints the correct message and exits.
    """

    parse_args(["--help"])
    mock_exit.assert_called_with(0)
