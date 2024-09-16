import importlib.util
import os
import sys
import traceback
from typing import List, Optional

from clixon.args import get_logger, get_sockpath
from clixon.clixon import Clixon

logger = get_logger()
sockpath = get_sockpath()


class ModuleError(Exception):
    pass


def run_hooks(modules: List, service_name: str, instance: str, result: str) -> None:
    if modules == []:
        logger.info("No modules found.")
        return

    with Clixon(sockpath=sockpath) as cd:
        for module in modules:
            if service_name:
                if module.SERVICE != service_name:
                    logger.debug(f"Skipping module {module} for service {service_name}")
                    continue

            try:
                logger.info(f"Running hooks for module {module}")
                root = cd.get_root()
                match result:
                    case "pre-commit":
                        logger.debug(f"Running pre-commit hook for module {module}")
                        if hasattr(module, "setup_pre_commit"):
                            module.setup_pre_commit(root, logger, instance=instance)
                    case "SUCCESS":
                        logger.debug(f"Running post-commit hook for module {module}")
                        if hasattr(module, "setup_post_commit"):
                            module.setup_post_commit(
                                root, logger, instance=instance, result=result
                            )
                    case "FAILED":
                        logger.debug(
                            f"Running post-commit-failed hook for module {module}"
                        )
                        if hasattr(module, "setup_post_commit_failed"):
                            module.setup_post_commit_failed(
                                root, logger, instance=instance, result=result
                            )

            except Exception as e:
                logger.error(f"Module {module} failed with exception: {e}")
                logger.error(traceback.format_exc())

                raise ModuleError(e)


def run_modules(
    modules: List, service_name: str, instance: str, service_diff: bool
) -> Optional[Exception]:
    """
    Run all modules in the list.

    :param modules: List of modules to run
    :type modules: List
    :param service_name: Name of the service to run modules for
    :type service_name: str
    :param instance: Instance of the service to run modules for
    :type instance: str
    :param service_diff: Run modules only if service is different
    :type service_diff: bool
    :return: None if all modules ran successfully, otherwise the exception
    :rtype: Optional[Exception]

    """
    logger.debug(f"Modules: {modules}")

    if modules == []:
        logger.info("No modules found.")
        return

    with Clixon(sockpath=sockpath) as cd:
        for module in modules:
            if service_name:
                if module.SERVICE != service_name:
                    logger.debug(f"Skipping module {module} for service {service_name}")
                    continue

            try:
                logger.info(f"Running module {module}")
                logger.debug(f"Module {module} is getting config")
                root = cd.get_root()
                module.setup(root, logger, instance=instance, diff=service_diff)
            except Exception as e:
                logger.error(f"Module {module} failed with exception: {e}")
                logger.error(traceback.format_exc())

                raise ModuleError(e)


def find_modules(modulespath: str) -> List[str]:
    """

    Find all modules in the modulespath.

    :param modulespath: Path to the modules
    :type modulespath: str
    :return: List of modules
    :rtype: List[str]

    """

    modules = []
    forbidden_list = ["#", "~"]
    for root, dirs, files in os.walk(modulespath):
        for module in files:
            forbidden = [x for x in forbidden_list if x in module]
            if not module.endswith(".py") or forbidden:
                logger.debug(f"Skipping file: {module}")
                continue
            logger.info(f"Added module {module}")
            modules.append(root + "/" + module)
            if root not in sys.path:
                sys.path.append(root)
        for directory in dirs:
            dir_modules = find_modules(directory + "/")
            modules = modules + dir_modules
    modules.reverse()

    if modules:
        logger.debug("Modules found: " + str(modules))

    return modules


def load_modules(modulespath: str, modulefilter: str) -> List:
    """
    Load all modules in the modulespath.

    :param modulespath: Path to the modules
    :type modulespath: str
    :param modulefilter: Comma separated list of modules to skip
    :type modulefilter: str
    :return: List of loaded modules
    :rtype: List

    """

    loaded_modules = []
    filtered = modulefilter.split(",")

    if not modulespath.endswith("/"):
        modulespath = modulespath + "/"

    for modulefile in find_modules(modulespath):
        modulename = os.path.splitext(modulefile)[0].split("/")[-1]

        if modulename in filtered:
            logger.info(f"Skipping module: {modulename}")
            continue

        logger.debug(f"Importing module {modulename}")
        try:
            spec = importlib.util.spec_from_file_location(modulename, modulefile)
            module = importlib.util.module_from_spec(spec)
            sys.modules[modulename] = module
            spec.loader.exec_module(module)

            if not hasattr(module, "SERVICE"):
                logger.debug(
                    f"Failed to load module, {modulename} does not have SERVICE attribute"
                )
                continue

            if not hasattr(module, "setup"):
                logger.debug(
                    f"Failed to load module, {modulename} does not have setup function"
                )
                continue
        except Exception as e:
            logger.error(f"Failed to load module {modulefile}: {e}")
            continue
        else:
            loaded_modules.append(module)

    return loaded_modules
