import os

from clixon.log import get_log_factory


def test_get_log_factory():
    """
    Test the get_log_factory function.
    """
    log_factory = get_log_factory()
    assert log_factory is not None

    assert log_factory.level == 20


def test_log_factory_debug():
    """
    Test the log_factory debug function.
    """
    log_factory = get_log_factory(debug=True)

    assert log_factory.level == 10


def test_log_factory_debug_env():
    """
    Test the log_factory debug function with environment variable.
    """

    # Set PYAPI_DEBUG=1
    os.environ["PYAPI_DEBUG"] = "1"

    log_factory = get_log_factory()

    assert log_factory.level == 10
