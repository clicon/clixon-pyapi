from unittest.mock import patch

from clixon.log import get_log_factory
import logging


def test_log():
    """
    Test the default log factory.
    """

    logger = get_log_factory()

    assert logger.name == "pyserver"
    assert logger.level == logging.INFO
    assert logger.hasHandlers() is True


def test_log_stdout(caplog):
    """
    Test the default log factory with output to stdout.
    """

    logger = get_log_factory(output="stdout")

    assert logger.name == "pyserver"
    assert logger.level == logging.INFO
    assert logger.hasHandlers() is True

    assert logger.debug("debug test") is None
    assert "debug test" not in caplog.text

    assert logger.info("info test") is None
    assert "info test" in caplog.text


def test_log_debug(caplog):
    """
    Test the default log factory with debug enabled.
    """

    logger = get_log_factory(debug=True)

    assert logger.name == "pyserver"
    assert logger.level == logging.DEBUG
    assert logger.hasHandlers() is True

    assert logger.info("info test") is None
    assert "info test" in caplog.text

    assert logger.debug("debug test") is None
    assert "debug test" in caplog.text


def test_get_log_factory_syslog():
    """
    Test that the logger can log to syslog.
    """

    with patch("clixon.log.SysLogHandler") as handler:
        logger = get_log_factory("s", False, override=True)

        assert logger is not None
        handler.assert_called()

    get_log_factory("o", False, override=True)


def test_get_log_factory_syslog_without_dev_log():
    """
    Test that syslog is used over the network when there is no /dev/log.
    """

    with patch("clixon.log.SysLogHandler") as handler, patch(
        "os.path.exists", return_value=False
    ):
        get_log_factory("s", False, override=True)

        assert handler.call_args[1] == {}

    get_log_factory("o", False, override=True)


def test_get_log_factory_timestamp():
    """
    Test that the log can be timestamped.
    """

    logger = get_log_factory("o", False, timestamp=True, override=True)

    assert "%(asctime)s" in logger.handlers[0].formatter._fmt

    get_log_factory("o", False, override=True)


def test_get_log_factory_debug_from_environment(monkeypatch):
    """
    Test that debug can be turned on with an environment variable.
    """

    monkeypatch.setenv("PYAPI_DEBUG", "1")

    assert get_log_factory("o", False).level == logging.DEBUG
