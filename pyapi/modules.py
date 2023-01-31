import time
import traceback
import importlib
from pyapi.log import get_logger
import os

logger = get_logger()
modulespath = "./modules/"


def run_modules(modules):
    logger.debug(f"Modules: {modules}")
    for module in modules:
        try:
            module.setup()
        except Exception as e:
            logger.error(f"Module {module} failed with exception: {e}")
            logger.error(traceback.format_exc())


def find_modules():
    modules = []
    for root, dirs, files in os.walk(modulespath):
        for module in files:
            if not module.endswith(".py"):
                logger.debug(f"Skipping file: {module}")
                continue
            logger.debug(f"Added module {module}")
            modules.append(module[:-3])

    return modules


def load_modules(modulefilter):
    loaded_modules = []
    filtered = modulefilter.split(",")
    for modulefile in find_modules():
        if modulefile in filtered:
            logger.debug(f"Skipping module: {modulefile}")
            continue

        logger.debug(f"Importing module modules.{modulefile}")
        module = importlib.import_module("modules." + modulefile)
        loaded_modules.append(module)

    return loaded_modules


async def notify():
    while True:
        logger.debug("Notify!")
        time.sleep(2)
