import logging
from logging.handlers import SysLogHandler
from typing import Optional
import os


def get_log_factory(
    output: Optional[str] = "s",
    debug: Optional[bool] = False,
    timestamp: Optional[bool] = False,
    override: Optional[bool] = False,
) -> logging.Logger:
    """
    Get logger for the application.

    :param output: Output type. "s" for syslog anything else for stdout
    :type output: str
    :param debug: Debug mode.
    :type debug: bool
    :return: Logger
    :rtype: logging.Logger

    """

    logger = logging.getLogger("pyserver")
    if not logger.handlers or override:
        if logger.handlers:
            logger.handlers.clear()

        if timestamp:
            formatter = logging.Formatter(
                "%(asctime)s %(name)s[%(process)d] %(filename)s:%(lineno)d: %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        else:
            formatter = logging.Formatter(
                "%(name)s[%(process)d] %(filename)s:%(lineno)d: %(message)s"
            )

        if output == "s":
            if os.path.exists("/dev/log"):
                handler = SysLogHandler(address="/dev/log")
            else:
                handler = SysLogHandler()
        else:
            handler = logging.StreamHandler()

        handler.setFormatter(formatter)
        logger.addHandler(handler)

    if debug or os.environ.get("PYAPI_DEBUG") == "1":
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    return logger
