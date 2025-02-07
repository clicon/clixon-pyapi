class PropertyError(Exception):
    """
    Exception raised when a property configuration fails.
    """
    pass


class ConfigError(Exception):
    """
    Exception raised when invalid configuration settings are detected.
    """
    pass


class RPCError(Exception):
    """
    Exception raised when a remote procedure call fails.
    """
    pass


class TransactionError(Exception):
    """
    Exception raised when a transaction cannot be completed.
    """
    pass


class TimeoutException(Exception):
    """
    Exception raised when an operation times out.
    """
    pass


class ModuleError(Exception):
    """
    Exception raised when a module initialization fails.
    """
    pass
