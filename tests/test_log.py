from clixon.log import init_root_logger, get_logger
import logging


def test_log():
    """
    Test the root logger.
    """

    logger = init_root_logger()

    assert logger.name == "root"
    assert logger.level == logging.INFO
    assert logger.parent is None
    assert logger.hasHandlers() is True


def test_get_logger(caplog):
    """
    Test that the logger is fetched correctly.
    """
    _ = init_root_logger(output="stdout", debug=True)

    logger = get_logger("module_name")

    assert logger is not None
    assert logger.parent is not None
    assert logger.name == "root.module_name"

    assert logger.debug("info test") is None
    assert "info test" in caplog.text


def test_log_stdout(caplog):
    """
    Test the default log factory with output to stdout.
    """

    logger = init_root_logger(output="stdout")

    assert logger.name == "root"
    assert logger.level == logging.INFO
    assert logger.parent is None
    assert logger.hasHandlers() is True

    assert logger.debug("debug test") is None
    assert "debug test" not in caplog.text

    assert logger.info("info test") is None
    assert "info test" in caplog.text

    assert get_logger("child_module").level == logging.NOTSET


def test_log_debug(caplog):
    """
    Test the default log factory with debug enabled.
    """

    logger = init_root_logger(debug=True)

    assert logger.name == "root"
    assert logger.level == logging.DEBUG
    assert logger.parent is None
    assert logger.hasHandlers() is True

    assert logger.info("info test") is None
    assert "info test" in caplog.text

    assert logger.debug("debug test") is None
    assert "debug test" in caplog.text

    assert get_logger("child_module").level == logging.NOTSET
