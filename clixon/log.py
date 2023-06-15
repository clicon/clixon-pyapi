import logging
from logging.handlers import SysLogHandler
from typing import Optional
import os


def get_log_factory(output: Optional[str] = "s",
                    debug: Optional[bool] = False) -> logging.Logger:
    """
    Get logger for the application.
    """

    logger = logging.getLogger('pyserver')
    if not logger.handlers:
        formatter = logging.Formatter(
            '[%(asctime)s] %(levelname)s in %(module)s: %(message)s')

        if output == "s":
            if os.path.exists("/dev/log"):
                handler = SysLogHandler(address='/dev/log')
            else:
                handler = SysLogHandler()
        else:
            handler = logging.StreamHandler()

        handler.setFormatter(formatter)
        logger.addHandler(handler)

    if debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    return logger
