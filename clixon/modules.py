import importlib.util
import os
import sys
import traceback

from typing import List
from typing import Optional

from clixon.args import get_logger
from clixon.clixon import Clixon
from clixon.exceptions import ModuleError


logger = get_logger()


def get_service_depth(module: object) -> Optional[int]:
    """
    Return the module's SERVICE_DEPTH, or None if it is not set.

    :param module: Service module
    :type module: object
    :return: Depth, a positive integer, or None
    :rtype: Optional[int]
    :raises ValueError: If SERVICE_DEPTH is not a positive integer

    """

    depth = getattr(module, "SERVICE_DEPTH", None)

    if depth is None:
        return None

    if isinstance(depth, bool) or not isinstance(depth, int) or depth < 1:
        raise ValueError(
            f"SERVICE_DEPTH in {module} must be a positive integer, got {depth!r}"
        )

    return depth


def get_module_root(cd: Clixon, module: object) -> object:
    """
    Fetch the configuration a module should operate on.

    If the module sets both SERVICE_XPATH and SERVICE_NAMESPACES, only that
    xpath is fetched, otherwise the whole configuration.

    If the module sets SERVICE_DEPTH, the configuration is fetched with that
    depth, counted from the top of the tree (devices and services are level
    1). /services is always fetched in full, whatever the depth.

    :param cd: Clixon object
    :type cd: Clixon
    :param module: Service module
    :type module: object
    :return: Root object
    :rtype: object

    """

    depth = get_service_depth(module)
    xpath = None
    namespaces = None

    if hasattr(module, "SERVICE_XPATH") and hasattr(module, "SERVICE_NAMESPACES"):
        xpath = module.SERVICE_XPATH
        namespaces = module.SERVICE_NAMESPACES

    if depth is None:
        if xpath:
            return cd.get_root(xpath=xpath, namespaces=namespaces)

        return cd.get_root()

    logger.debug(f"Using SERVICE_DEPTH {depth} for {module}")

    # Fetched first: the tree from the last get_root() is the one written back
    services = cd.get_root(xpath="/services")
    root = cd.get_root(xpath=xpath or "/", namespaces=namespaces, depth=depth)

    for element in root.get_elements("services"):
        root.delete(element=element)

    for element in services.get_elements("services"):
        root.add(element)

    return root


def run_hooks(
    socket,
    modules: List,
    service_name: str,
    instance: str,
    diff: bool,
    result: str,
    user: Optional[str] = None,
) -> None:
    if modules == []:
        logger.info("No modules found.")
        return

    run_hooks = False

    for module in modules:
        if getattr(module, "SERVICE") != service_name:
            continue

        if (
            hasattr(module, "setup_pre_commit")
            or hasattr(module, "setup_post_commit")
            or hasattr(module, "setup_post_commit_failed")
        ):
            run_hooks = True

    if not run_hooks:
        logger.info("No hooks found.")
        return

    with Clixon(socket=socket, user=user, from_server=True) as cd:
        for module in modules:
            if service_name:
                if module.SERVICE != service_name:
                    logger.debug(f"Skipping module {module} for service {service_name}")
                    continue

            try:
                logger.info(f"Running hooks for module {module}")

                root = get_module_root(cd, module)

                match result:
                    case "pre-commit":
                        logger.debug(f"Running pre-commit hook for module {module}")
                        if hasattr(module, "setup_pre_commit"):
                            module.setup_pre_commit(
                                root, logger, instance=instance, diff=diff
                            )
                    case "SUCCESS":
                        logger.debug(f"Running post-commit hook for module {module}")
                        if hasattr(module, "setup_post_commit"):
                            module.setup_post_commit(
                                root,
                                logger,
                                instance=instance,
                                result=result,
                                diff=diff,
                            )
                    case "FAILED":
                        logger.debug(
                            f"Running post-commit-failed hook for module {module}"
                        )
                        if hasattr(module, "setup_post_commit_failed"):
                            module.setup_post_commit_failed(
                                root,
                                logger,
                                instance=instance,
                                result=result,
                                diff=diff,
                            )

            except Exception as e:
                logger.error(f"Module {module} failed with exception: {e}")
                logger.error(traceback.format_exc())

                raise ModuleError(e)


def run_modules(
    socket,
    modules: List,
    service_name: str,
    instance: str,
    service_diff: Optional[bool] = False,
    user: Optional[str] = None,
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

    with Clixon(socket=socket, user=user, from_server=True) as cd:
        for module in modules:
            if service_name:
                if module.SERVICE != service_name:
                    logger.debug(f"Skipping module {module} for service {service_name}")
                    continue

            try:
                logger.info(f"Running module {module}")
                logger.debug(f"Module {module} is getting config")

                root = get_module_root(cd, module)

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
            raise
        else:
            loaded_modules.append(module)

    return loaded_modules
