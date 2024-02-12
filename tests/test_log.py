from clixon.log import init_logger, get_logger
import logging


def test_log():
    """
    Test the default log factory.
    """

    logger = init_logger()

    assert logger.name == "pyserver"
    assert logger.level == logging.INFO
    assert logger.hasHandlers() is True


def test_get_logger():
    """
    Test that the logger is fetched correctly.
    """

    logger = get_logger()

    assert logger is not None
    assert logger.name == "pyserver"


def test_log_stdout(caplog):
    """
    Test the default log factory with output to stdout.
    """

    logger = init_logger(output="stdout")

    assert logger.name == "pyserver"
    assert logger.level == logging.INFO
    assert logger.hasHandlers() is True

    assert logger.debug("debug test") is None
    assert "debug test" not in caplog.text

    assert logger.info("info test") is None
    assert "info test" in caplog.text

    assert get_logger().level == logging.INFO


def test_log_debug(caplog):
    """
    Test the default log factory with debug enabled.
    """

    logger = init_logger(debug=True)

    assert logger.name == "pyserver"
    assert logger.level == logging.DEBUG
    assert logger.hasHandlers() is True

    assert logger.info("info test") is None
    assert "info test" in caplog.text

    assert logger.debug("debug test") is None
    assert "debug test" in caplog.text

    assert get_logger().level == logging.DEBUG
