from enum import Enum
from typing import Optional
from xml.sax._exceptions import SAXParseException

from clixon.element import Element
from clixon.parser import parse_string
from clixon.args import get_logger

import sys

logger = get_logger()


class RPCTypes(Enum):
    GET_CONFIG = 0
    EDIT_CONFIG = 1
    COMMIT = 2
    TRANSACTION_DONE = 3
    TRANSACTION_ERROR = 4
    PUSH_COMMIT = 5
    PULL = 6


class RPCError(Exception):
    pass


def rpc_config_get(user: Optional[str] = "root",
                   source: Optional[str] = "actions") -> Element:
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
    xpath_attributes = {
        "nc:type": "xpath",
        "nc:select": "/"
    }

    if source == "actions":
        attributes = {"xmlns": "http://clicon.org/controller"}

    root = rpc_header_get(RPCTypes.GET_CONFIG, user)
    root.rpc.get_config.create("source")
    root.rpc.get_config.source.create(
        source, attributes=attributes)
    root.rpc.get_config.create("nc:filter", attributes=xpath_attributes)

    return root


def rpc_config_set(config: Element, user: Optional[str] = "root",
                   device: Optional[bool] = False,
                   target: Optional[str] = "actions",
                   target_attributes: Optional[dict] = {}) -> Element:
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

    if target_attributes == {} and target == "actions":
        target_attributes = {
            "xmlns": "http://clicon.org/controller"
        }

    root = rpc_header_get(RPCTypes.EDIT_CONFIG, user)
    root.rpc.edit_config.create("target")
    root.rpc.edit_config.target.create(
        target, attributes=target_attributes)
    root.rpc.edit_config.create("default-operation")
    root.rpc.edit_config.default_operation.cdata = "none"
    root.rpc.edit_config.create("config")

    if device:
        root.rpc.edit_config.config.delete("services")
        root.rpc.edit_config.config.create(
            "devices", attributes={"xmlns": "http://clicon.org/controller"})
        root.rpc.edit_config.config.devices.add(config)
    else:
        for node in config.get_elements():
            root.rpc.edit_config.config.add(node)

    return root


def rpc_commit(user: Optional[str] = "root") -> Element:
    """
    Create a RPC commit element.

    :param user: User name
    :type user: str
    :return: RPC element
    :rtype: Element

    """

    return rpc_header_get(RPCTypes.COMMIT, user)


def rpc_push() -> Element:
    """
    Create a RPC push element.

    :return: RPC element
    :rtype: Element

    """

    return rpc_header_get(RPCTypes.PUSH_COMMIT, "root")


def rpc_pull() -> Element:
    """
    Create a RPC pull element.

    :return: RPC element
    :rtype: Element

    """

    return rpc_header_get(RPCTypes.PULL, "root")


def rpc_header_get(rpc_type: object, user: str,
                   attributes: Optional[dict] = None) -> Element:
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
            "message-id": 42
        }

    root = Element("root", {})
    root.create("rpc", attributes=attributes)

    if rpc_type == RPCTypes.GET_CONFIG:
        root.rpc.create("get-config")
    elif rpc_type == RPCTypes.EDIT_CONFIG:
        root.rpc.create("edit-config")
    elif rpc_type == RPCTypes.COMMIT:
        root.rpc.create("commit")
    elif rpc_type == RPCTypes.TRANSACTION_DONE:
        root.rpc.create("transaction-actions-done",
                        attributes={"xmlns": "http://clicon.org/controller"})
    elif rpc_type == RPCTypes.TRANSACTION_ERROR:
        root.rpc.create("transaction-error",
                        attributes={"xmlns": "http://clicon.org/controller"})
    elif rpc_type == RPCTypes.PUSH_COMMIT:
        root.rpc.create("controller-commit",
                        attributes={"xmlns": "http://clicon.org/controller"})
        root.rpc.controller_commit.create("device", data="*")
        root.rpc.controller_commit.create("push", data="COMMIT")
        root.rpc.controller_commit.create("actions", data="NONE")
        root.rpc.controller_commit.create("source", data="ds:running")
    elif rpc_type == RPCTypes.PULL:
        root.rpc.create("config-pull",
                        attributes={"xmlns": "http://clicon.org/controller"})
        root.rpc.config_pull.create("devname", data="*")

    return root


def rpc_subscription_create(stream: Optional[str] = "services-commit") -> Element:
    """
    Create a RPC subscription element.

    :param stream: Stream name
    :type stream: str
    :return: RPC element
    :rtype: Element

    """

    attributes = {
        "xmlns": "urn:ietf:params:xml:ns:netmod:notification"
    }

    rpcattrs = {
        "xmlns": "urn:ietf:params:xml:ns:netconf:base:1.0",
        "message-id": "42"
    }

    root = rpc_header_get("", "root", rpcattrs)
    root.rpc.create("create-subscription", attributes=attributes)
    root.rpc.create_subscription.create("stream")
    root.rpc.create_subscription.stream.cdata = stream
    root.rpc.create_subscription.create(
        "filter", {"type": "xpath", "select": ""})

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

    if "error-message" in xmlstr:
        try:
            message = str(root.rpc_reply.rpc_error.error_message.cdata)
            if standalone:
                logger.error(message)
                sys.exit(1)

            raise RPCError(message)
        except AttributeError:
            return None
    elif "error-path" in xmlstr:
        try:
            message = root.rpc_reply.rpc_error.error_app_tag.cdata + \
                ": " + root.rpc_reply.rpc_error.error_path.cdata
            raise RPCError(message)
        except AttributeError:
            return None
    elif "non-unique" in xmlstr:
        try:
            message = root.rpc_reply.rpc_error.error_app_tag.cdata + \
                ": " + root.rpc_reply.rpc_error.error_info.non_unique.cdata
            raise RPCError(message)
        except AttributeError:
            return None
    elif "rpc-error" in xmlstr:
        try:
            message = root.rpc_reply.rpc_error.error_tag.cdata + \
                ": " + root.rpc_reply.rpc_error.error_message.cdata
            raise RPCError(message)
        except AttributeError:
            return None
