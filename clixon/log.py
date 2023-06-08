import logging
from logging.handlers import SysLogHandler
from typing import Optional


def get_logger(output: Optional[str] = "s") -> logging.Logger:
    """
    Get logger for the application.
    """

    logger = logging.getLogger('pyserver')
    if not logger.handlers:
        formatter = logging.Formatter(
            '[%(asctime)s] %(levelname)s in %(module)s: %(message)s')

        if output == "s":
            handler = SysLogHandler(address='/dev/log')
        else:
            handler = logging.StreamHandler()

        handler.setFormatter(formatter)
        logger.addHandler(handler)

    logger.setLevel(logging.INFO)

    return logger
