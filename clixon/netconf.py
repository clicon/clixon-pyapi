import getpass
import sys

from enum import Enum
from typing import Optional

from clixon.args import get_logger
from clixon.element import Element
from clixon.exceptions import RPCError
from clixon.parser import parse_string

from xml.sax._exceptions import SAXParseException

logger = get_logger()


class RPCTypes(Enum):
    GET_CONFIG = 0
    EDIT_CONFIG = 1
    COMMIT = 2
    TRANSACTION_DONE = 3
    TRANSACTION_ERROR = 4
    PUSH_COMMIT = 5
    PULL = 6


CONTROLLER_NS = {"xmlns": "http://clicon.org/controller"}
BASE_ATTRIBUTES = {
    "xmlns": "urn:ietf:params:xml:ns:netconf:base:1.0",
    "message-id": "42",
    "username": None,
}


def rpc_config_get(
    user: Optional[str] = None, source: Optional[str] = "actions"
) -> Element:
    """
    Create a get-config RPC element.

    :param user: User name
    :type user: str
    :param source: Source of the configuration
    :type source: str
    :return: RPC element
    :rtype: Element

    """
    attributes = {}
    xpath_attributes = {"nc:type": "xpath", "nc:select": "/"}

    if not user:
        user = getpass.getuser()

    if source == "actions":
        attributes = CONTROLLER_NS

    root = rpc_header_get(RPCTypes.GET_CONFIG, user)
    root.rpc.get_config.create("source")
    root.rpc.get_config.source.create(source, attributes=attributes)
    root.rpc.get_config.create("nc:filter", attributes=xpath_attributes)

    return root


def rpc_config_set(
    config: Element,
    user: Optional[str] = None,
    device: Optional[bool] = False,
    target: Optional[str] = "actions",
    target_attributes: Optional[dict] = {},
) -> Element:
    """
    Create a RPC config set element.

    :param config: Configuration to set
    :type config: Element
    :param user: User name
    :type user: str
    :param device: Device configuration
    :type device: bool
    :param target: Target of the configuration
    :type target: str
    :param target_attributes: Target attributes
    :type target_attributes: dict
    :return: RPC element
    :rtype: Element

    """

    if not user:
        user = getpass.getuser()

    if target_attributes == {} and target == "actions":
        target_attributes = CONTROLLER_NS

    root = rpc_header_get(RPCTypes.EDIT_CONFIG, user)
    root.rpc.edit_config.create("target")
    root.rpc.edit_config.target.create(target, attributes=target_attributes)
    root.rpc.edit_config.create("default-operation")
    root.rpc.edit_config.default_operation.cdata = "none"
    root.rpc.edit_config.create("config")

    for node in config.get_elements():
        if node.get_name() == "devices":
            continue

        root.rpc.edit_config.config.add(node)

    for device in config.devices.device:
        if device.find_modified():
            logger.debug(f"Modifications found on device {device.name.get_data()}")
            root.rpc.edit_config.config.devices.add(device)
        else:
            logger.debug(f"No modifications found on device {device.name.get_data()}")

    return root


def rpc_commit(user: Optional[str] = None) -> Element:
    """
    Create a RPC commit element.

    :param user: User name
    :type user: str
    :return: RPC element
    :rtype: Element

    """

    if not user:
        user = getpass.getuser()

    return rpc_header_get(RPCTypes.COMMIT, user)


def rpc_push(user: Optional[str] = None) -> Element:
    """
    Create a RPC push element.

    :return: RPC element
    :rtype: Element

    """

    if not user:
        user = getpass.getuser()

    return rpc_header_get(RPCTypes.PUSH_COMMIT, user)


def rpc_pull(
    device: Optional[str] = "*",
    transient: Optional[bool] = False,
    user: Optional[str] = None,
) -> Element:
    """
    Create a RPC pull element.

    :return: RPC element
    :rtype: Element

    """

    if not user:
        user = getpass.getuser()

    rpc = rpc_header_get(RPCTypes.PULL, user=user, device=device)

    if transient:
        rpc.rpc.config_pull.create("transient", data="true")

    return rpc


def rpc_header_get(
    rpc_type: object,
    user: str,
    attributes: Optional[dict] = None,
    device: Optional[str] = "*",
) -> Element:
    """
    Create a RPC header element.

    :param rpc_type: RPC type
    :type rpc_type: object
    :param user: User name
    :type user: str
    :param attributes: Attributes
    :type attributes: dict
    :return: RPC element
    :rtype: Element

    """

    if attributes is None:
        attributes = {
            "xmlns": "urn:ietf:params:xml:ns:netconf:base:1.0",
            "username": user,
            "xmlns:nc": "urn:ietf:params:xml:ns:netconf:base:1.0",
            "message-id": 42,
        }

    if rpc_type == RPCTypes.EDIT_CONFIG:
        attributes["xmlns:cl"] = "http://clicon.org/lib"

    root = Element("root", {})
    root.create("rpc", attributes=attributes)

    # This could be a match/case but keeping if-statements
    # for Python backward compatibility.
    if rpc_type == RPCTypes.GET_CONFIG:
        root.rpc.create("get-config")
    elif rpc_type == RPCTypes.EDIT_CONFIG:
        root.rpc.create("edit-config")
    elif rpc_type == RPCTypes.COMMIT:
        root.rpc.create("commit")
    elif rpc_type == RPCTypes.TRANSACTION_DONE:
        root.rpc.create("transaction-actions-done", attributes=CONTROLLER_NS)
    elif rpc_type == RPCTypes.TRANSACTION_ERROR:
        root.rpc.create("transaction-error", attributes=CONTROLLER_NS)
    elif rpc_type == RPCTypes.PUSH_COMMIT:
        root.rpc.create("controller-commit", attributes=CONTROLLER_NS)
        root.rpc.controller_commit.create("device", data=device)
        root.rpc.controller_commit.create("push", data="COMMIT")
        root.rpc.controller_commit.create("actions", data="NONE")
        root.rpc.controller_commit.create("source", data="ds:running")
    elif rpc_type == RPCTypes.PULL:
        root.rpc.create("config-pull", attributes=CONTROLLER_NS)
        root.rpc.config_pull.create("device", data=device)

    return root


def rpc_subscription_create(
    stream: Optional[str] = "services-commit", user: Optional[str] = None
) -> Element:
    """
    Create a RPC subscription element.

    :param stream: Stream name
    :type stream: str
    :return: RPC element
    :rtype: Element

    """

    if not user:
        user = getpass.getuser()

    attributes = {
        "xmlns": "urn:ietf:params:xml:ns:netmod:notification",
    }

    rpcattrs = {
        "xmlns": "urn:ietf:params:xml:ns:netconf:base:1.0",
        "xmlns:nc": "urn:ietf:params:xml:ns:netconf:base:1.0",
        "cl:username": user,
        "xmlns:cl": "http://clicon.org/lib",
        "message-id": "42",
    }

    root = rpc_header_get("", user, rpcattrs)
    root.rpc.create("create-subscription", attributes=attributes)
    root.rpc.create_subscription.create("stream")
    root.rpc.create_subscription.stream.cdata = stream
    root.rpc.create_subscription.create("filter", {"type": "xpath", "select": ""})

    return root


def rpc_error_get(xmlstr: str, standalone: Optional[bool] = False) -> None:
    """
    Parse the XML string and raise an exception if an error is found.

    :param xmlstr: XML string
    :type xmlstr: str
    :param standalone: Standalone mode
    :type standalone: bool
    :return: None
    :rtype: None

    """

    try:
        root = parse_string(xmlstr)
    except SAXParseException:
        if "client already registered" in xmlstr:
            logger.error("Client already registered.")
            sys.exit(1)

        logger.error("XML parse error, XML was: %s", xmlstr)
        raise RPCError("XML parse error, XML was: %s", xmlstr)

    if "notification xmlns" in xmlstr:
        try:
            message = str(root.notification.controller_transaction.reason.cdata)
            if standalone:
                logger.error(f"Error in notification: {message}")

            logger.error(message)
        except AttributeError:
            if "SUCCESS" in xmlstr:
                pass
            else:
                logger.error(f"Unknown notification error: {xmlstr}")
    elif "error-message" in xmlstr:
        try:
            message = str(root.rpc_reply.rpc_error.error_message.cdata)
            if standalone:
                logger.error(message)
                sys.exit(1)

            raise RPCError(message)
        except AttributeError:
            raise RPCError(f"Unknown error: {xmlstr}")
    elif "error-path" in xmlstr:
        try:
            message = (
                root.rpc_reply.rpc_error.error_app_tag.cdata
                + ": "
                + root.rpc_reply.rpc_error.error_path.cdata
            )
            raise RPCError(message)
        except AttributeError:
            raise RPCError(f"Unknown error: {xmlstr}")
    elif "non-unique" in xmlstr:
        try:
            message = (
                root.rpc_reply.rpc_error.error_app_tag.cdata
                + ": "
                + root.rpc_reply.rpc_error.error_info.non_unique.cdata
            )
            raise RPCError(message)
        except AttributeError:
            raise RPCError(f"Unknown error: {xmlstr}")
    elif "rpc-error" in xmlstr:
        try:
            message = (
                root.rpc_reply.rpc_error.error_tag.cdata
                + ": "
                + root.rpc_reply.rpc_error.error_message.cdata
            )
            raise RPCError(message)
        except AttributeError:
            raise RPCError(f"Unknown error: {xmlstr}")
    elif "<result>FAILED</result>" in xmlstr:
        try:
            message = root.notification.controller_transaction.reason
            raise RPCError(message)
        except AttributeError:
            return None


def rpc_apply_template(
    devname: str,
    template: str,
    variables: dict,
    template_type: Optional[str] = "RPC",
    user: Optional[str] = None,
    inline: Optional[bool] = False,
) -> Element:
    if not user:
        BASE_ATTRIBUTES["username"] = getpass.getuser()
    else:
        BASE_ATTRIBUTES["username"] = user

    root = Element()
    root.create("rpc", attributes=BASE_ATTRIBUTES)
    root.rpc.create("device-template-apply", attributes=CONTROLLER_NS)
    root.rpc.device_template_apply.create("type", data=template_type)
    root.rpc.device_template_apply.create("device", data=devname)

    if inline:
        inline_element = parse_string(template).config
        root.rpc.device_template_apply.create("inline").add(inline_element)
    else:
        root.rpc.device_template_apply.create("template", data=template)

    if variables:
        root.rpc.device_template_apply.create("variables")
        for key, value in variables.items():
            var = root.rpc.device_template_apply.variables.create("variable")
            var.create("name", data=key)
            var.create("value", data=value)

    return root


def rpc_apply_service(
    service: str, instance: str, diff: Optional[bool] = True, user: Optional[str] = None
) -> Element:
    """
    Create a RPC service-apply element.

    :param service: Service name
    :type service: str
    :param instance: Instance name
    :type instance: str
    :return: RPC element
    :rtype: Element

    """

    if diff:
        action = "NONE"
    else:
        action = "COMMIT"

    if not user:
        BASE_ATTRIBUTES["username"] = getpass.getuser()
    else:
        BASE_ATTRIBUTES["username"] = user

    instance = f"{service}[service-name='{instance}']"

    root = Element()
    root.create("rpc", attributes=BASE_ATTRIBUTES)
    root.rpc.create("controller-commit", attributes=CONTROLLER_NS)
    root.rpc.controller_commit.create("device", data="*")
    root.rpc.controller_commit.create("push", data=action)
    root.rpc.controller_commit.create("actions", data="FORCE")
    root.rpc.controller_commit.create("service-instance", data=instance)
    root.rpc.controller_commit.create("source", data="ds:candidate")

    return root


def rpc_datastore_diff(
    compare: Optional[bool] = False,
    transient: Optional[bool] = False,
    user: Optional[str] = None,
) -> Element:
    """
    Create a RPC datastore-diff element.

    :return: RPC element
    :rtype: Element

    """

    if not user:
        BASE_ATTRIBUTES["username"] = getpass.getuser()
    else:
        BASE_ATTRIBUTES["username"] = user

    root = Element()
    root.create("rpc", attributes=BASE_ATTRIBUTES)
    root.rpc.create("datastore-diff", attributes=CONTROLLER_NS)

    if compare:
        root.rpc.datastore_diff.create("format", data="text")
        root.rpc.datastore_diff.create("dsref1", data="ds:running")
        root.rpc.datastore_diff.create("dsref2", data="ds:candidate")
    else:
        if transient:
            config_type1 = "TRANSIENT"
            config_type2 = "RUNNING"
        else:
            config_type1 = "RUNNING"
            config_type2 = "ACTIONS"

        root.rpc.datastore_diff.create("device", data="*")
        root.rpc.datastore_diff.create("config-type1", data=config_type1)
        root.rpc.datastore_diff.create("config-type2", data=config_type2)

    return root


def rpc_lock(
    target: Optional[str] = "candidate", user: Optional[str] = None
) -> Element:
    """
    Create a RPC lock element.

    :return: RPC element
    :rtype: Element

    """

    if not user:
        BASE_ATTRIBUTES["username"] = getpass.getuser()
    else:
        BASE_ATTRIBUTES["username"] = user

    root = Element()
    root.create("rpc", attributes=BASE_ATTRIBUTES)
    root.rpc.create("lock").create("target").create(target)

    return root


def rpc_unlock(
    target: Optional[str] = "candidate", user: Optional[str] = None
) -> Element:
    """
    Create a RPC unlock element.

    :return: RPC element
    :rtype: Element

    """

    if not user:
        BASE_ATTRIBUTES["username"] = getpass.getuser()
    else:
        BASE_ATTRIBUTES["username"] = user

    root = Element()
    root.create("rpc", attributes=BASE_ATTRIBUTES)
    root.rpc.create("unlock").create("target").create(target)

    return root


def rpc_discard_changes(user: Optional[str] = None) -> Element:
    """
    Discard changes aka rollback.

    :return: RPC element
    :rtype: Element

    """
    #  Example:
    #  <rpc xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0"
    #  cl:username="snc" xmlns:cl="http://clicon.org/lib" message-id="42"><discard-changes/></rpc>

    BASE_ATTRIBUTES = {
        "xmlns": "urn:ietf:params:xml:ns:netconf:base:1.0",
        "xmlns:nc": "urn:ietf:params:xml:ns:netconf:base:1.0",
        "cl:username": None,
        "xmlns:cl": "http://clicon.org/lib",
        "message-id": "42",
    }

    if not user:
        BASE_ATTRIBUTES["cl:username"] = getpass.getuser()
    else:
        BASE_ATTRIBUTES["cl:username"] = user

    root = Element()
    root.create("rpc", attributes=BASE_ATTRIBUTES)
    root.rpc.create("discard-changes")

    return root


def rpc_connection_open(
    device: Optional[str] = "*", user: Optional[str] = None
) -> Element:
    """
    Create a RPC connection-open element.

    :return: RPC element
    :rtype: Element

    """

    if not user:
        BASE_ATTRIBUTES["username"] = getpass.getuser()
    else:
        BASE_ATTRIBUTES["username"] = user

    root = Element()
    root.create("rpc", attributes=BASE_ATTRIBUTES)
    root.rpc.create("connection-change", attributes=CONTROLLER_NS)
    root.rpc.connection_change.create("operation", data="OPEN")
    root.rpc.connection_change.create("device", data=device)

    return root


def rpc_transactions_get(
    tid: Optional[int] = None, user: Optional[str] = None
) -> Element:
    """
    Get either all transactions or a single transaction status.
    """

    # Example:
    # <rpc xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" cl:username="debian" xmlns:cl="http://clicon.org/lib" message-id="43">
    #     <get cl:content="all" xmlns:cl="http://clicon.org/lib">
    #         <nc:filter nc:type="xpath" nc:select="co:transactions" xmlns:co="http://clicon.org/controller"/>
    #         <with-defaults xmlns="urn:ietf:params:xml:ns:yang:ietf-netconf-with-defaults">report-all</with-defaults>
    #     </get>
    # </rpc>

    if not user:
        user = getpass.getuser()

    rpc_attributes = {
        "xmlns": "urn:ietf:params:xml:ns:netconf:base:1.0",
        "xmlns:nc": "urn:ietf:params:xml:ns:netconf:base:1.0",
        "cl:username": user,
        "xmlns:cl": "http://clicon.org/lib",
        "message-id": "42",
    }

    attributes = {
        "nc:type": "xpath",
        "nc:select": "co:transactions",
        "xmlns:co": "http://clicon.org/controller",
    }

    if tid:
        attributes["nc:select"] = f"/co:transactions/co:transaction[co:tid='{tid}']"

    root = Element()
    root.create("rpc", attributes=rpc_attributes)
    root.rpc.create(
        "get",
        attributes={"cl:content": "nonconfig", "xmlns:cl": "http://clicon.org/lib"},
    )
    root.rpc.get.create("nc:filter", attributes=attributes)
    root.rpc.get.create(
        "with-defaults",
        attributes={"xmlns": "urn:ietf:params:xml:ns:yang:ietf-netconf-with-defaults"},
        data="report-all",
    )

    return root


def rpc_devices_get(user: Optional[str] = None) -> Element:
    """
    Get device names, connection states, timestamps, and log messages.
    """
    if not user:
        user = getpass.getuser()

    rpc_attributes = {
        "xmlns": "urn:ietf:params:xml:ns:netconf:base:1.0",
        "xmlns:nc": "urn:ietf:params:xml:ns:netconf:base:1.0",
        "cl:username": user,
        "xmlns:cl": "http://clicon.org/lib",
        "message-id": "42",
    }

    filter_attributes = {
        "nc:type": "xpath",
        "nc:select": "co:devices/co:device/co:name | co:devices/co:device/co:conn-state | co:devices/co:device/co:conn-state-timestamp | co:devices/co:device/co:logmsg",
        "xmlns:co": "http://clicon.org/controller",
    }

    root = Element()
    root.create("rpc", attributes=rpc_attributes)

    root.rpc.create(
        "get",
        attributes={"cl:content": "all", "xmlns:cl": "http://clicon.org/lib"},
    )

    root.rpc.get.create("nc:filter", attributes=filter_attributes)

    root.rpc.get.create(
        "with-defaults",
        attributes={"xmlns": "urn:ietf:params:xml:ns:yang:ietf-netconf-with-defaults"},
        data="explicit",
    )

    return root
