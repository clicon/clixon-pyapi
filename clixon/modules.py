import importlib.util
import os
import sys
import traceback
from typing import List, Optional

from clixon.log import get_logger

logger = get_logger()


class ModuleError(Exception):
    pass


def run_modules(modules: List) -> Optional[Exception]:
    """
    Run all modules in the list.
    """

    logger.debug(f"Modules: {modules}")

    for module in modules:
        try:
            module.setup()
        except Exception as e:
            logger.error(f"Module {module} failed with exception: {e}")
            logger.error(traceback.format_exc())

            raise (ModuleError(e))


def find_modules(modulespath: str) -> List[str]:
    """
    Find all modules in the modulespath.
    """

    modules = []
    forbidden = ["#", "~"]
    for root, dirs, files in os.walk(modulespath):
        for module in files:
            if not module.endswith(".py") or [x for x in forbidden if x in module]:
                logger.debug(f"Skipping file: {module}")
                continue
            logger.info(f"Added module {module}")
            modules.append(root + module)
    modules.reverse()

    return modules


def load_modules(modulespath: str, modulefilter: str) -> List:
    """
    Load all modules in the modulespath.
    """

    loaded_modules = []
    filtered = modulefilter.split(",")

    if not modulespath.endswith("/"):
        modulespath = modulespath + "/"

    for modulefile in find_modules(modulespath):
        if modulefile in filtered:
            logger.debug(f"Skipping module: {modulefile}")
            continue
        modulename = os.path.splitext(modulefile)[0].split("/")[-1]

        logger.info(f"Importing module {modulefile} ({modulename})")

        try:
            spec = importlib.util.spec_from_file_location(
                modulename, modulefile)
            module = importlib.util.module_from_spec(spec)
            sys.modules[modulename] = module
            spec.loader.exec_module(module)
        except Exception as e:
            logger.error(f"Failed to load module {modulefile}: {e}")
            continue
        else:
            loaded_modules.append(module)

        return loaded_modules