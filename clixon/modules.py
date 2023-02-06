import importlib
import os
import threading
import traceback

from clixon.log import get_logger

logger = get_logger()
modulespath = "./modules/"


def run_modules(modules):
    logger.debug(f"Modules: {modules}")
    threads = []

    for module in modules:
        try:
            thread = threading.Thread(target=module.setup, args=())
            thread.start()
            threads.append(thread)
        except Exception as e:
            logger.error(f"Module {module} failed with exception: {e}")
            logger.error(traceback.format_exc())


def find_modules():
    modules = []
    for root, dirs, files in os.walk(modulespath):
        for module in files:
            if not module.endswith(".py") and not module.startswith("#"):
                logger.debug(f"Skipping file: {module}")
                continue
            logger.debug(f"Added module {module}")
            modules.append(module[:-3])
    modules.reverse()

    return modules


def load_modules(modulefilter):
    loaded_modules = []
    filtered = modulefilter.split(",")
    for modulefile in find_modules():
        if modulefile in filtered:
            logger.debug(f"Skipping module: {modulefile}")
            continue

        logger.debug(f"Importing module modules.{modulefile}")

        try:
            module = importlib.import_module("modules." + modulefile)
        except Exception as e:
            logger.debug(f"Failed to load module {modulefile}: {e}")
        else:
            loaded_modules.append(module)

    return loaded_modules
