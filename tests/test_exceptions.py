import pytest
from clixon.exceptions import (
    PropertyError,
    ConfigError,
    RPCError,
    TransactionError,
    TimeoutException,
    ModuleError,
)


def test_property_error():
    """
    Test the PropertyError exception.
    """
    with pytest.raises(PropertyError):
        raise PropertyError("Property configuration failed")


def test_config_error():
    """
    Test the ConfigError exception.
    """
    with pytest.raises(ConfigError):
        raise ConfigError("Invalid configuration settings")


def test_rpc_error():
    """
    Test the RPCError exception.
    """
    with pytest.raises(RPCError):
        raise RPCError("Remote procedure call failed")


def test_transaction_error():
    """
    Test the TransactionError exception.
    """
    with pytest.raises(TransactionError):
        raise TransactionError("Transaction could not be completed")


def test_timeout_exception():
    """
    Test the TimeoutException exception.
    """
    with pytest.raises(TimeoutException):
        raise TimeoutException("Operation timed out")


def test_module_error():
    """
    Test the ModuleError exception.
    """
    with pytest.raises(ModuleError):
        raise ModuleError("Module initialization failed")


def test_exception_messages():
    """
    Test the messages of the exceptions.
    """
    with pytest.raises(PropertyError) as exc_info:
        raise PropertyError("Specific property error message")
    assert str(exc_info.value) == "Specific property error message"

    with pytest.raises(ConfigError) as exc_info:
        raise ConfigError("Detailed config error description")
    assert str(exc_info.value) == "Detailed config error description"
