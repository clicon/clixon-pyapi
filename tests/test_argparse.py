from pytest import raises
import tempfile

from clixon.args import parse_args, get_arg


def test_parse_args(mocker):
    """
    Test that the arguments are parsed correctly.
    """

    mocker.patch("os.path.exists").return_value = True

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
        ) = parse_args([
            "-m", tmp_file,
            "-s", "/test/socket",
            "-p", "/test/pidfile",
            "-F",
            "-P",
            "-l", "o",
            "-d"
        ])

        assert sockpath == "/test/socket"
        for m_path in modulepaths:
            assert m_path in [tmp_file]
        assert modulefilter == ""
        assert pidfile == "/test/pidfile"
        assert foreground is True
        assert pp is True
        assert log == "o"
        assert debug is True


def test_get_sockpath(mocker):
    """
    Test that the socket path is returned correctly.
    """

    mocker.patch("os.path.exists").return_value = True

    parse_args(["-s", "/test/socket"])
    assert get_arg("sockpath") == '/test/socket'


def test_get_prettyprint(mocker):
    """
    Test that the pretty print is returned correctly.
    """

    mocker.patch("os.path.exists").return_value = True

    parse_args(["-P"])
    assert get_arg("pp") is True


def test_modulepath_default(mocker):
    """
    Test that default module path is added when no modulepath is provided.
    """

    mocker.patch("os.path.exists").return_value = True

    parse_args()
    mpaths = get_arg("modulepaths")
    default_mpath = "/usr/local/share/clixon/controller/modules"
    assert mpaths == [default_mpath]
    assert len(mpaths) == 1


def test_modulepath_argument(mocker):
    """
    Test that
    - argument is added,
    - fallback module path is not added.
    """

    mocker.patch("os.path.exists").return_value = True

    parse_args(["-m", "/tmp"])
    mpaths = get_arg("modulepaths")
    assert mpaths == ["/tmp"]
    assert len(mpaths) == 1


def test_modulepath_configfile(mocker):
    """
    Test that both configfile modulpath and default module path is added.
    """
    mocker.patch("os.path.exists").return_value = True
    mocker.patch("clixon.args.__parse_config_file").return_value = (
        "a", ["/tmp/conf_file_mpath"], "b", "c"
    )

    parse_args(["-f", "dummy_config_file"])
    mpaths = get_arg("modulepaths")

    assert len(mpaths) == 2
    for m_path in mpaths:
        assert m_path in [
                "/tmp/conf_file_mpath",
                "/usr/local/share/clixon/controller/modules"
        ]


def test_usage(capsys):
    """
    Test that the usage function prints the correct message and exits.
    """

    with raises(SystemExit) as e:
        parse_args(["--help"])
    assert e.type == SystemExit
    out, _ = capsys.readouterr()
    assert "show this help message and exit" in out
