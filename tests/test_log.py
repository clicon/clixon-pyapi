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
