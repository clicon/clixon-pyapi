#!/usr/bin/env python3

"""
This module provides the clixon_rest program.

clixon_rest is a small HTTP server, intended to run behind NGINX, which
exposes the controller services as a REST API. The endpoints are not static:
at startup the service YANG modules are fetched from the backend using
NETCONF get-schema, and the resources, the JSON bodies and the OpenAPI
(Swagger) description are rendered from that YANG.

A service defined as:

    augment "/ctrl:services" {
        list ssh-users {
            key service-name;
            ...
        }
    }

is served as:

    GET    /api/v1/services/ssh-users
    POST   /api/v1/services/ssh-users
    GET    /api/v1/services/ssh-users/{service-name}
    PUT    /api/v1/services/ssh-users/{service-name}
    PATCH  /api/v1/services/ssh-users/{service-name}
    DELETE /api/v1/services/ssh-users/{service-name}
    POST   /api/v1/services/ssh-users/{service-name}/apply

The rest of the Python API is served as well:

    GET    /api/v1/config             get_root, by xpath
    PATCH  /api/v1/config             set_root, with a XML body
    POST   /api/v1/commit             commit
    POST   /api/v1/push               push
    POST   /api/v1/rollback           rollback
    GET    /api/v1/compare            show_compare
    GET    /api/v1/transactions       show_transactions
    GET    /api/v1/transactions/{tid} show_transactions
    GET    /api/v1/devices            show_devices
    GET    /api/v1/devices/diff       show_devices_diff
    POST   /api/v1/devices/pull       pull
    POST   /api/v1/devices/connect    connection_open
    POST   /api/v1/devices/rpc        device_rpc
    POST   /api/v1/devices/template   apply_template
    GET    /api/v1/schemas            get_schemas
    GET    /api/v1/yang/{module}      get_service_yang

The write requests take the query parameters commit, push and lock. The
OpenAPI description is served on /api/v1/openapi.json and Swagger UI on
/api/v1/docs.

Example NGINX configuration:

    location /api/v1/ {
        proxy_pass http://127.0.0.1:8088/api/v1/;
        proxy_set_header X-Forwarded-Prefix /api/v1;
        proxy_set_header X-Remote-User $remote_user;
    }
"""

import argparse
import json
import os
import re
import signal
import socket
import sys
import threading
import time

from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from socketserver import ThreadingMixIn, UnixStreamServer
from typing import Optional
from urllib.parse import parse_qs, unquote, urlparse
from xml.sax.saxutils import escape as xml_escape
from xml.sax.saxutils import unescape as xml_unescape

import xmltodict

import clixon.args
import clixon.parser

from clixon import yang
from clixon.clixon import Clixon
from clixon.element import Element
from clixon.exceptions import RPCError, TimeoutException
from clixon.log import get_log_factory
from clixon.parser import parse_string
from clixon.sock import SocketClosedError
from clixon.version import __version__

DEFAULT_SOCKPATH = "/usr/local/var/run/controller/controller.sock"
DEFAULT_ADDRESS = "127.0.0.1"
DEFAULT_PORT = 8088
DEFAULT_PREFIX = "/api/v1"
DEFAULT_SWAGGER_UI = "https://unpkg.com/swagger-ui-dist@5"
DEFAULT_TIMEOUT = 30

CONTROLLER_NS_URI = "http://clicon.org/controller"

# Largest accepted request body.
MAX_BODY = 1024 * 1024

# Shortest time between two service YANG reloads triggered by a request for
# an unknown service.
RELOAD_INTERVAL = 5

# Longest timeout a request may ask for.
MAX_TIMEOUT = 3600


def parse_args(cli_args: Optional[list] = None) -> argparse.Namespace:
    """
    Parse command line arguments.

    :param cli_args: List of command line arguments
    :type cli_args: list
    :return: Parsed arguments
    :rtype: argparse.Namespace

    """

    parser = argparse.ArgumentParser(description="clixon REST API server")

    parser.add_argument(
        "-f", "--configfile", help="Clixon controller configuration file"
    )
    parser.add_argument(
        "-s", "--sockpath", default=DEFAULT_SOCKPATH, help="Clixon socket path"
    )
    parser.add_argument(
        "-a", "--address", default=DEFAULT_ADDRESS, help="Address to listen on"
    )
    parser.add_argument(
        "-p", "--port", type=int, default=DEFAULT_PORT, help="Port to listen on"
    )
    parser.add_argument(
        "-U",
        "--unix-socket",
        help="Listen on a UNIX socket instead of a TCP port",
    )
    parser.add_argument(
        "-x",
        "--prefix",
        default=DEFAULT_PREFIX,
        help="Path prefix of the API",
    )
    parser.add_argument(
        "-u",
        "--user",
        help="User of the NETCONF sessions, defaults to the running user",
    )
    parser.add_argument(
        "-H",
        "--user-header",
        default="X-Remote-User",
        help="Header holding the user authenticated by the web server",
    )
    parser.add_argument(
        "-r", "--read-only", action="store_true", help="Refuse all write requests"
    )
    parser.add_argument(
        "-t",
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT,
        help="Seconds to wait for the backend to finish an operation",
    )
    parser.add_argument(
        "-S",
        "--swagger-ui",
        default=DEFAULT_SWAGGER_UI,
        help="Base URL of the Swagger UI assets",
    )
    parser.add_argument(
        "-d", "--debug", action="store_true", help="Enable verbose debug logging"
    )
    parser.add_argument(
        "-l",
        "--log",
        choices=["s", "o"],
        default="o",
        help="Log on (s)yslog, std(o)ut",
    )
    parser.add_argument("-P", "--pp", action="store_true", help="Prettyprint XML")
    parser.add_argument("-V", "--version", action="store_true", help="Print version")

    args = parser.parse_args(cli_args)

    if args.configfile:
        args.sockpath = get_sockpath(args.configfile)

    return args


def get_sockpath(configfile: str) -> str:
    """
    Return CLICON_SOCK from a clixon configuration file.

    :param configfile: Clixon configuration file
    :type configfile: str
    :return: Socket path
    :rtype: str

    """

    try:
        config = clixon.parser.parse_file(configfile)

        return config.clixon_config.CLICON_SOCK.cdata
    except Exception as e:
        print(f"Could not parse configuration file {configfile}: {e}")
        sys.exit(1)


def init_args(cli_args: Optional[list] = None) -> argparse.Namespace:
    """
    Parse the arguments and hand them over to the clixon package, which reads
    its arguments from clixon.args and would otherwise try to parse ours.

    :param cli_args: List of command line arguments
    :type cli_args: list
    :return: Parsed arguments
    :rtype: argparse.Namespace

    """

    args = parse_args(cli_args)

    clixon.args.global_args = {
        # The configuration file has already been read, and the clixon package
        # expects a clixon_server configuration file, so it is left out here.
        "configfile": None,
        "debug": args.debug,
        "log": args.log,
        "modulefilter": "",
        "modulepaths": [],
        "pidfile": None,
        "pp": args.pp,
        "sockpath": args.sockpath,
    }

    return args


# Arguments are only read from the command line when running as a program,
# not when imported, since the argv of the importer is none of our business.
if os.path.basename(sys.argv[0]).startswith("clixon_rest"):
    ARGS = init_args(sys.argv[1:])
else:
    ARGS = init_args([])

# The logger of the clixon package is created when the package is imported,
# before the arguments are known, and is reconfigured here.
logger = get_log_factory(ARGS.log, ARGS.debug, override=True)


class RestError(Exception):
    """
    An error which is returned to the client.
    """

    def __init__(self, status: HTTPStatus, message: str) -> None:
        """
        Create an error.

        :param status: HTTP status
        :type status: HTTPStatus
        :param message: Error message
        :type message: str
        :return: None
        :rtype: None

        """

        super().__init__(message)

        self.status = status
        self.message = message


class Service:
    """
    A service, ie a YANG list augmenting the controller services container.
    """

    def __init__(self, node: object, module: object) -> None:
        """
        Create a service.

        :param node: Schema node of the service list
        :type node: yang.Node
        :param module: Module the service is defined in
        :type module: yang.Module
        :return: None
        :rtype: None

        """

        self.node = node
        self.name = node.name
        self.description = node.description
        self.keys = node.keys
        self.module = module.name
        self.namespace = module.namespace
        self.revision = module.revision

    def __repr__(self) -> str:
        return f"<Service {self.name}>"

    def key_values(self, instance: str) -> list:
        """
        Split the instance part of an URL into key values. Multiple keys are
        separated by comma, as in RESTCONF.

        :param instance: Instance part of the URL
        :type instance: str
        :return: List of key values
        :rtype: list

        """

        values = [unquote(v) for v in instance.split(",")]

        if len(values) != len(self.keys):
            raise RestError(
                HTTPStatus.BAD_REQUEST,
                f"Service {self.name} has the keys {', '.join(self.keys)}, "
                f"expected {len(self.keys)} comma separated key values",
            )

        for value in values:
            if "'" in value:
                raise RestError(
                    HTTPStatus.BAD_REQUEST, "Key values may not contain quotes"
                )

        return values

    def xpath(self, instance: Optional[str] = None) -> str:
        """
        Return the xpath of the service, or of one of its instances.

        :param instance: Instance part of the URL
        :type instance: str
        :return: Xpath
        :rtype: str

        """

        xpath = f"/ctrl:services/svc:{self.name}"

        if instance is None:
            return xpath

        predicates = ""

        for key, value in zip(self.keys, self.key_values(instance)):
            predicates += f"[svc:{key}='{value}']"

        return xpath + predicates


class Registry:
    """
    The services the backend serves YANG for.
    """

    def __init__(self, sockpath: str, user: Optional[str] = None) -> None:
        """
        Create a registry.

        :param sockpath: Path to the clixon socket
        :type sockpath: str
        :param user: User of the NETCONF session
        :type user: str
        :return: None
        :rtype: None

        """

        self.__sockpath = sockpath
        self.__user = user
        self.__lock = threading.Lock()
        self.__services = {}
        self.__modules = {}
        self.__loaded = 0

    @property
    def services(self) -> dict:
        """
        Return the services, keyed on service name.

        :return: Dict of services
        :rtype: dict

        """

        with self.__lock:
            return dict(self.__services)

    @property
    def modules(self) -> dict:
        """
        Return the YANG text of the service modules, keyed on module name.

        :return: Dict of YANG modules
        :rtype: dict

        """

        with self.__lock:
            return dict(self.__modules)

    def service(self, name: str) -> Service:
        """
        Return a service by name. The services are reloaded if the name is
        unknown, a service may have been added to the backend since the last
        load.

        :param name: Service name
        :type name: str
        :return: Service
        :rtype: Service

        """

        services = self.services

        if name not in services and time.time() - self.__loaded > RELOAD_INTERVAL:
            self.load()
            services = self.services

        if name not in services:
            raise RestError(HTTPStatus.NOT_FOUND, f"No such service: {name}")

        return services[name]

    def load(self) -> dict:
        """
        Fetch the YANG of the services from the backend and build the schema
        tree of each service.

        :return: Dict of services
        :rtype: dict

        """

        logger.debug("Loading service YANG from the backend")

        services = {}
        modules = {}

        with connect(self.__sockpath, self.__user) as clx:
            context = yang.Context(loader=clx.get_service_yang)

            for schema in clx.get_schemas():
                name = schema.get("identifier")

                if not name or schema.get("format", "yang") != "yang":
                    continue

                # The standard modules never augment the services container,
                # not fetching them saves a round trip each.
                if name.startswith(("ietf-", "iana-")):
                    continue

                try:
                    text = clx.get_service_yang(name)
                except Exception as e:
                    logger.warning(f"Could not fetch YANG for {name}: {e}")
                    continue

                if not yang.is_service_module(text):
                    continue

                try:
                    module = context.add(text)
                except yang.YangError as e:
                    logger.warning(f"Could not parse YANG module {name}: {e}")
                    continue

                nodes = yang.service_nodes(context, module)

                if not nodes:
                    continue

                modules[module.name] = text

                for node in nodes:
                    if node.name in services:
                        logger.warning(
                            f"Service {node.name} of {module.name} shadows the "
                            f"service of {services[node.name].module}"
                        )

                    services[node.name] = Service(node, module)

        logger.info(
            f"Loaded {len(services)} services from {len(modules)} YANG modules: "
            + ", ".join(sorted(services))
        )

        with self.__lock:
            self.__services = services
            self.__modules = modules
            self.__loaded = time.time()

        return services


class Connection:
    """
    Context manager opening and closing a NETCONF session to the backend.
    """

    def __init__(
        self,
        sockpath: str,
        user: Optional[str] = None,
        read_only: Optional[bool] = True,
        source: Optional[str] = "running",
        push: Optional[bool] = False,
        timeout: Optional[int] = DEFAULT_TIMEOUT,
    ) -> None:
        self.__sockpath = sockpath
        self.__user = user
        self.__read_only = read_only
        self.__source = source
        self.__push = push
        self.__timeout = timeout
        self.__clixon = None

    def __enter__(self) -> object:
        try:
            self.__clixon = Clixon(
                sockpath=self.__sockpath,
                user=self.__user,
                source=self.__source,
                target="candidate",
                read_only=self.__read_only,
                push=self.__push,
                timeout=self.__timeout,
            )
        except (OSError, ValueError) as e:
            raise RestError(
                HTTPStatus.BAD_GATEWAY, f"Could not connect to the backend: {e}"
            )

        return self.__clixon

    def __exit__(self, *args: object) -> None:
        # Clixon.__exit__ writes the root object back to the backend, which is
        # not wanted here, only the session is closed.
        try:
            self.__clixon.close_session()
        except Exception as e:
            logger.debug(f"Could not close the session: {e}")


def connect(
    sockpath: str,
    user: Optional[str] = None,
    read_only: Optional[bool] = True,
    source: Optional[str] = "running",
    push: Optional[bool] = False,
    timeout: Optional[int] = DEFAULT_TIMEOUT,
) -> Connection:
    """
    Open a NETCONF session to the backend.

    :param sockpath: Path to the clixon socket
    :type sockpath: str
    :param user: User of the NETCONF session
    :type user: str
    :param read_only: Refuse writes
    :type read_only: bool
    :param source: Datastore to read from
    :type source: str
    :param push: Push to the devices when committing
    :type push: bool
    :param timeout: Seconds to wait for the backend to finish an operation
    :type timeout: int
    :return: Connection
    :rtype: Connection

    """

    return Connection(
        sockpath,
        user,
        read_only=read_only,
        source=source,
        push=push,
        timeout=timeout,
    )


class Locked:
    """
    Context manager locking a datastore for the duration of a request. A lock
    only lives as long as the NETCONF session it was taken in, and each
    request has a session of its own, which is why locking is done here and
    not exposed as a resource of its own.
    """

    def __init__(
        self,
        clx: object,
        enabled: bool,
        target: Optional[str] = "candidate",
    ) -> None:
        self.__clixon = clx
        self.__enabled = enabled
        self.__target = target

    def __enter__(self) -> object:
        if self.__enabled:
            try:
                self.__clixon.lock(self.__target)
            except RPCError as e:
                raise RestError(
                    HTTPStatus.CONFLICT, f"Could not lock {self.__target}: {e}"
                )

        return self

    def __exit__(self, *args: object) -> None:
        if not self.__enabled:
            return

        try:
            self.__clixon.unlock(self.__target)
        except Exception as e:
            logger.warning(f"Could not unlock {self.__target}: {e}")


def element_to_dict(element: object) -> object:
    """
    Convert an element of an unknown schema to JSON. Used where there is no
    YANG to convert with, such as the configuration of a device.

    :param element: Element to convert
    :type element: Element
    :return: Dict of the element, None if it is empty
    :rtype: object

    """

    if element is None:
        return None

    xmlstr = element.dumps()

    if not xmlstr:
        return None

    return xmltodict.parse(f"<data>{xmlstr}</data>").get("data")


def elements_to_json(data: str, name: str) -> list:
    """
    Return the elements of a given name in a reply as a list of dicts of their
    leafs. Used for the flat state data of the controller, such as the devices
    and the transactions.

    :param data: Reply from the backend
    :type data: str
    :param name: Name of the elements to return
    :type name: str
    :return: List of dicts
    :rtype: list

    """

    found = []

    for element in parse_string(data).get_elements(name, recursive=True):
        entry = {}

        for child in element.get_elements():
            if child.get_elements():
                entry[child.origname()] = element_to_dict(child)
            else:
                entry[child.origname()] = xml_unescape(
                    child.get_data(), {"&quot;": '"', "&apos;": "'"}
                )

        found.append(entry)

    return found


def value_to_json(node: object, value: str) -> object:
    """
    Convert the value of a leaf to its JSON type.

    :param node: Schema node of the leaf
    :type node: yang.Node
    :param value: Value of the element
    :type value: str
    :return: Converted value
    :rtype: object

    """

    value = xml_unescape(value, {"&quot;": '"', "&apos;": "'"})

    if node.type == "boolean":
        return value == "true"

    if node.type == "empty":
        return True

    if node.type and node.type.startswith(("int", "uint")):
        try:
            return int(value)
        except ValueError:
            return value

    if node.type == "decimal64":
        try:
            return float(value)
        except ValueError:
            return value

    return value


def value_to_xml(node: object, value: object) -> str:
    """
    Convert a JSON value to the cdata of an element.

    :param node: Schema node of the leaf
    :type node: yang.Node
    :param value: JSON value
    :type value: object
    :return: Value as XML cdata
    :rtype: str

    """

    if isinstance(value, bool):
        return "true" if value else "false"

    if value is None:
        return ""

    if isinstance(value, (dict, list)):
        raise RestError(
            HTTPStatus.BAD_REQUEST, f"Expected a value for the leaf {node.name}"
        )

    return xml_escape(str(value))


def element_to_json(node: object, element: object) -> dict:
    """
    Convert an element to JSON using a schema node.

    Nodes which are not in the YANG are dropped, the schema is what the API
    promises to return.

    :param node: Schema node of the element
    :type node: yang.Node
    :param element: Element to convert
    :type element: Element
    :return: Dict of the element
    :rtype: dict

    """

    out = {}

    for child in node.children:
        elements = element.get_elements(child.name)

        if not elements:
            continue

        if child.kind == "leaf":
            out[child.name] = value_to_json(child, elements[0].get_data())
        elif child.kind == "leaf-list":
            out[child.name] = [value_to_json(child, e.get_data()) for e in elements]
        elif child.kind == "container":
            out[child.name] = element_to_json(child, elements[0])
        elif child.kind == "list":
            out[child.name] = [element_to_json(child, e) for e in elements]

    return out


def json_to_element(node: object, data: dict, element: object) -> None:
    """
    Add the JSON data of a container or list entry to an element, using a
    schema node.

    :param node: Schema node of the element
    :type node: yang.Node
    :param data: JSON data
    :type data: dict
    :param element: Element to add the data to
    :type element: Element
    :return: None
    :rtype: None

    """

    if not isinstance(data, dict):
        raise RestError(
            HTTPStatus.BAD_REQUEST, f"Expected an object for {node.name}, got a value"
        )

    unknown = [k for k in data if node.child(k) is None]

    if unknown:
        raise RestError(
            HTTPStatus.BAD_REQUEST,
            f"Unknown fields in {node.name}: {', '.join(sorted(unknown))}",
        )

    # Keys are written first, the backend expects them before the other
    # elements of a list entry.
    children = [node.child(k) for k in node.keys]
    children += [c for c in node.children if c.name not in node.keys]

    for child in children:
        if child.name not in data:
            if child.name in node.keys:
                raise RestError(
                    HTTPStatus.BAD_REQUEST, f"Missing key {child.name} in {node.name}"
                )
            if child.mandatory:
                raise RestError(
                    HTTPStatus.BAD_REQUEST,
                    f"Missing mandatory field {child.name} in {node.name}",
                )
            continue

        value = data[child.name]

        if child.kind == "leaf":
            element.create(child.name, data=value_to_xml(child, value))
        elif child.kind == "leaf-list":
            if not isinstance(value, list):
                raise RestError(
                    HTTPStatus.BAD_REQUEST, f"Expected a list for {child.name}"
                )

            for entry in value:
                element.create(child.name, data=value_to_xml(child, entry))
        elif child.kind == "container":
            json_to_element(child, value, element.create(child.name))
        elif child.kind == "list":
            if not isinstance(value, list):
                raise RestError(
                    HTTPStatus.BAD_REQUEST, f"Expected a list for {child.name}"
                )

            for entry in value:
                json_to_element(child, entry, element.create(child.name))


def instance_element(
    service: Service,
    data: Optional[dict] = None,
    operation: Optional[str] = None,
) -> Element:
    """
    Build the services element of an edit-config for one service instance.

    :param service: Service
    :type service: Service
    :param data: JSON data of the instance
    :type data: dict
    :param operation: NETCONF operation of the instance element
    :type operation: str
    :return: Element
    :rtype: Element

    """

    root = Element()
    services = root.create("services", attributes={"xmlns": CONTROLLER_NS_URI})

    attributes = {"xmlns": service.namespace}

    if operation:
        attributes["nc:operation"] = operation

    element = services.create(service.name, attributes=attributes)

    if data is not None:
        json_to_element(service.node, data, element)

    return root


def instances(clx: object, service: Service, instance: Optional[str] = None) -> list:
    """
    Read the instances of a service from the backend.

    :param clx: Clixon object
    :type clx: Clixon
    :param service: Service
    :type service: Service
    :param instance: Instance part of the URL, all instances if omitted
    :type instance: str
    :return: List of elements
    :rtype: list

    """

    root = clx.get_root(
        xpath=service.xpath(instance),
        namespaces={"svc": service.namespace},
    )

    if root is None:
        return []

    found = []

    for services in root.get_elements("services"):
        found.extend(services.get_elements(service.name))

    return found


def openapi_type(node: object) -> dict:
    """
    Return the OpenAPI schema of a leaf.

    :param node: Schema node of the leaf
    :type node: yang.Node
    :return: OpenAPI schema
    :rtype: dict

    """

    schema = {"type": "string"}

    if node.type == "boolean":
        schema = {"type": "boolean"}
    elif node.type == "empty":
        schema = {"type": "boolean"}
    elif node.type == "decimal64":
        schema = {"type": "number"}
    elif node.type and node.type.startswith(("int", "uint")):
        schema = {"type": "integer"}

        if node.type in ["int64", "uint64"]:
            schema["format"] = "int64"
        elif node.type not in ["int8", "uint8", "int16", "uint16"]:
            schema["format"] = "int32"

    if node.enums:
        schema["enum"] = node.enums

    if node.default is not None:
        schema["default"] = value_to_json(node, node.default)

    if node.units:
        schema["x-yang-units"] = node.units

    if node.type:
        schema["x-yang-type"] = node.type

    return schema


def openapi_schema(node: object, writable: Optional[bool] = False) -> dict:
    """
    Return the OpenAPI schema of a container or list entry.

    :param node: Schema node
    :type node: yang.Node
    :param writable: Leave out the nodes which can not be written
    :type writable: bool
    :return: OpenAPI schema
    :rtype: dict

    """

    properties = {}
    required = []

    for child in node.children:
        if writable and (child.hidden or not child.config):
            continue

        if child.kind == "leaf":
            schema = openapi_type(child)
        elif child.kind == "leaf-list":
            schema = {"type": "array", "items": openapi_type(child)}
        elif child.kind == "container":
            schema = openapi_schema(child, writable=writable)
        elif child.kind == "list":
            schema = {
                "type": "array",
                "items": openapi_schema(child, writable=writable),
            }
        else:
            continue

        if child.description:
            schema["description"] = child.description

        if not writable and not child.config:
            schema["readOnly"] = True

        properties[child.name] = schema

        if child.name in node.keys or child.mandatory:
            required.append(child.name)

    schema = {"type": "object", "properties": properties}

    if node.description:
        schema["description"] = node.description

    if required:
        schema["required"] = required

    return schema


PARAMETERS = {
    "source": {
        "description": "Datastore to read from",
        "schema": {
            "type": "string",
            "enum": ["running", "candidate", "actions"],
            "default": "running",
        },
    },
    "commit": {
        "description": "Commit the candidate datastore, which runs the service "
        "scripts. If false the change is left in the candidate datastore.",
        "schema": {"type": "boolean", "default": True},
    },
    "push": {
        "description": "Run the services which changed, commit and push the "
        "result to the devices, which is the commit of the controller CLI. "
        "If false the candidate datastore is committed locally and the "
        "services are not run, the controller only runs them in a transaction "
        "which pushes.",
        "schema": {"type": "boolean", "default": True},
    },
    "lock": {
        "description": "Lock the candidate datastore while the request is "
        "handled. The lock is released when the request is done, since it can "
        "not outlive the NETCONF session of the request.",
        "schema": {"type": "boolean", "default": False},
    },
    "timeout": {
        "description": "Seconds to wait for the backend to finish. Operations "
        "which wait for the devices, such as a pull or a push, may need more "
        "than the default.",
        "schema": {"type": "integer", "default": DEFAULT_TIMEOUT},
    },
    "device": {
        "description": "Device name, or * for all of them",
        "schema": {"type": "string", "default": "*"},
    },
    "diff": {
        "description": "Only return what applying would change, without "
        "touching the datastores. If false the service is applied, committed "
        "and pushed.",
        "schema": {"type": "boolean", "default": True},
    },
}


def openapi_parameter(name: str) -> dict:
    """
    Return a query parameter of an operation.

    :param name: Name of the parameter
    :type name: str
    :return: OpenAPI parameter
    :rtype: dict

    """

    return {"name": name, "in": "query", "required": False, **PARAMETERS[name]}


def openapi_parameters(write: Optional[bool] = False) -> list:
    """
    Return the query parameters of a read or a write operation.

    :param write: Parameters of a write operation
    :type write: bool
    :return: List of OpenAPI parameters
    :rtype: list

    """

    if not write:
        return [openapi_parameter("source")]

    return [openapi_parameter(name) for name in ["commit", "push", "lock", "timeout"]]


def openapi_template_body() -> dict:
    """
    Return the request body of the template operations.

    :return: OpenAPI request body
    :rtype: dict

    """

    return {
        "required": True,
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "required": ["template"],
                    "properties": {
                        "device": {
                            "type": "string",
                            "description": "Device name, mutually exclusive "
                            "with device-group",
                        },
                        "device-group": {
                            "type": "string",
                            "description": "Device group name, mutually "
                            "exclusive with device",
                        },
                        "template": {
                            "type": "string",
                            "description": "Name of the template, or the "
                            "template itself when inline is true",
                        },
                        "variables": {
                            "type": "object",
                            "description": "Variables of the template",
                            "additionalProperties": {"type": "string"},
                        },
                        "inline": {
                            "type": "boolean",
                            "default": False,
                            "description": "The template is given inline "
                            "instead of by name",
                        },
                    },
                }
            }
        },
    }


def openapi(services: dict, prefix: str, sockpath: str) -> dict:
    """
    Render the OpenAPI description of the services.

    :param services: Dict of services
    :type services: dict
    :param prefix: Path prefix of the API
    :type prefix: str
    :param sockpath: Path to the clixon socket
    :type sockpath: str
    :return: OpenAPI description
    :rtype: dict

    """

    paths = {
        "/health": {
            "get": {
                "tags": ["controller"],
                "summary": "Health of the API and of the backend connection",
                "operationId": "health",
                "responses": {
                    "200": {"description": "The backend is reachable"},
                    "502": {"description": "The backend is not reachable"},
                },
            }
        },
        "/services": {
            "get": {
                "tags": ["controller"],
                "summary": "List the services the backend serves YANG for",
                "operationId": "listServices",
                "responses": {"200": {"description": "List of services"}},
            }
        },
        "/push": {
            "post": {
                "tags": ["controller"],
                "summary": "Push the committed configuration to the devices",
                "operationId": "push",
                "parameters": [openapi_parameter("timeout")],
                "responses": {
                    "200": {"description": "The configuration was pushed"},
                    "400": {"description": "The push failed"},
                },
            }
        },
        "/yang/{module}": {
            "get": {
                "tags": ["controller"],
                "summary": "YANG of a module the backend serves",
                "operationId": "getYang",
                "parameters": [
                    {
                        "name": "module",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "string"},
                    }
                ],
                "responses": {
                    "200": {
                        "description": "The YANG module",
                        "content": {"text/plain": {"schema": {"type": "string"}}},
                    },
                    "404": {"description": "No such module"},
                },
            }
        },
        "/schemas": {
            "get": {
                "tags": ["controller"],
                "summary": "The YANG schemas the backend serves",
                "operationId": "listSchemas",
                "responses": {"200": {"description": "List of schemas"}},
            }
        },
        "/commit": {
            "post": {
                "tags": ["controller"],
                "summary": "Commit the candidate datastore",
                "description": "Committing runs the service scripts of the "
                "changed services.",
                "operationId": "commit",
                "parameters": [
                    openapi_parameter("push"),
                    openapi_parameter("lock"),
                ],
                "responses": {
                    "200": {"description": "The candidate datastore was committed"},
                    "400": {"description": "The commit failed"},
                },
            }
        },
        "/rollback": {
            "post": {
                "tags": ["controller"],
                "summary": "Discard the changes of the candidate datastore",
                "operationId": "rollback",
                "responses": {"200": {"description": "The changes were discarded"}},
            }
        },
        "/compare": {
            "get": {
                "tags": ["controller"],
                "summary": "Difference between the running and the candidate "
                "datastore",
                "operationId": "compare",
                "responses": {"200": {"description": "The difference, as text"}},
            }
        },
        "/transactions": {
            "get": {
                "tags": ["controller"],
                "summary": "The transactions of the backend",
                "operationId": "listTransactions",
                "responses": {"200": {"description": "List of transactions"}},
            }
        },
        "/transactions/{tid}": {
            "get": {
                "tags": ["controller"],
                "summary": "One transaction of the backend",
                "operationId": "getTransaction",
                "parameters": [
                    {
                        "name": "tid",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "integer"},
                    }
                ],
                "responses": {
                    "200": {"description": "The transaction"},
                    "404": {"description": "No such transaction"},
                },
            }
        },
        "/config": {
            "get": {
                "tags": ["controller"],
                "summary": "Any part of the configuration, selected by an xpath",
                "description": "The services are served as resources of their "
                "own, this is the way to the rest of the configuration, such "
                "as the devices.",
                "operationId": "getConfig",
                "parameters": [
                    {
                        "name": "xpath",
                        "in": "query",
                        "required": False,
                        "description": "Xpath of the wanted configuration",
                        "schema": {"type": "string", "default": "/"},
                    },
                    {
                        "name": "namespace",
                        "in": "query",
                        "required": False,
                        "description": "Namespace of a prefix of the xpath, "
                        "given as prefix:uri. May be repeated.",
                        "schema": {"type": "array", "items": {"type": "string"}},
                    },
                    {
                        "name": "format",
                        "in": "query",
                        "required": False,
                        "schema": {
                            "type": "string",
                            "enum": ["json", "xml"],
                            "default": "json",
                        },
                    },
                    openapi_parameter("source"),
                ],
                "responses": {"200": {"description": "The configuration"}},
            },
            "patch": {
                "tags": ["controller"],
                "summary": "Merge XML configuration into the candidate datastore",
                "description": "The body is a piece of NETCONF configuration "
                "XML. Use the nc:operation attribute for anything but a merge.",
                "operationId": "editConfig",
                "parameters": openapi_parameters(write=True),
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/xml": {"schema": {"type": "string"}},
                    },
                },
                "responses": {
                    "200": {"description": "The configuration was merged"},
                    "400": {"description": "Invalid body or failed commit"},
                },
            },
        },
        "/devices": {
            "get": {
                "tags": ["devices"],
                "summary": "The devices, their connection state and their log "
                "message",
                "operationId": "listDevices",
                "responses": {"200": {"description": "List of devices"}},
            }
        },
        "/devices/diff": {
            "get": {
                "tags": ["devices"],
                "summary": "Difference between the devices and the controller",
                "description": "The devices are pulled transiently to make the "
                "comparison.",
                "operationId": "devicesDiff",
                "parameters": [
                    openapi_parameter("device"),
                    openapi_parameter("timeout"),
                ],
                "responses": {
                    "200": {"description": "The difference, keyed on device"}
                },
            }
        },
        "/devices/pull": {
            "post": {
                "tags": ["devices"],
                "summary": "Pull the configuration of the devices",
                "operationId": "pull",
                "parameters": [openapi_parameter("timeout")],
                "requestBody": {
                    "required": False,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "device": {"type": "string", "default": "*"},
                                    "transient": {
                                        "type": "boolean",
                                        "default": False,
                                    },
                                },
                            }
                        }
                    },
                },
                "responses": {
                    "200": {"description": "The devices were pulled"},
                    "400": {"description": "The pull failed"},
                },
            }
        },
        "/devices/connect": {
            "post": {
                "tags": ["devices"],
                "summary": "Open the connection to the devices",
                "operationId": "connect",
                "parameters": [openapi_parameter("timeout")],
                "requestBody": {
                    "required": False,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "device": {"type": "string", "default": "*"}
                                },
                            }
                        }
                    },
                },
                "responses": {
                    "200": {"description": "The connection was opened"},
                    "502": {"description": "The connection could not be opened"},
                },
            }
        },
        "/devices/rpc": {
            "post": {
                "tags": ["devices"],
                "summary": "Apply a RPC template to the devices",
                "operationId": "deviceRpc",
                "parameters": [openapi_parameter("timeout")],
                "requestBody": openapi_template_body(),
                "responses": {
                    "200": {"description": "The replies of the devices"},
                    "400": {"description": "The RPC failed"},
                },
            }
        },
        "/devices/template": {
            "post": {
                "tags": ["devices"],
                "summary": "Apply a configuration template to the devices",
                "operationId": "applyTemplate",
                "parameters": openapi_parameters(write=True),
                "requestBody": openapi_template_body(),
                "responses": {
                    "200": {"description": "The template was applied"},
                    "400": {"description": "The template failed"},
                },
            }
        },
    }

    schemas = {}

    for name in sorted(services):
        service = services[name]
        schemas[name] = openapi_schema(service.node)
        schemas[f"{name}.request"] = openapi_schema(service.node, writable=True)

        instance = ",".join("{" + key + "}" for key in service.keys)
        summary = service.description or f"The {name} service"

        content = {
            "application/json": {"schema": {"$ref": f"#/components/schemas/{name}"}}
        }
        request = {
            "required": True,
            "content": {
                "application/json": {
                    "schema": {"$ref": f"#/components/schemas/{name}.request"}
                }
            },
        }

        paths[f"/services/{name}"] = {
            "get": {
                "tags": [name],
                "summary": f"All instances of {name}",
                "description": summary,
                "operationId": f"list_{name}",
                "parameters": openapi_parameters(),
                "responses": {
                    "200": {
                        "description": f"Instances of {name}",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "array",
                                    "items": {"$ref": f"#/components/schemas/{name}"},
                                }
                            }
                        },
                    }
                },
            },
            "post": {
                "tags": [name],
                "summary": f"Create an instance of {name}",
                "description": summary,
                "operationId": f"create_{name}",
                "parameters": openapi_parameters(write=True),
                "requestBody": request,
                "responses": {
                    "201": {"description": "The instance was created"},
                    "400": {"description": "Invalid body or failed commit"},
                    "409": {"description": "The instance already exists"},
                },
            },
        }

        parameters = [
            {
                "name": key,
                "in": "path",
                "required": True,
                "description": f"Key {key} of the instance",
                "schema": {"type": "string"},
            }
            for key in service.keys
        ]

        paths[f"/services/{name}/{instance}"] = {
            "get": {
                "tags": [name],
                "summary": f"One instance of {name}",
                "operationId": f"get_{name}",
                "parameters": parameters + openapi_parameters(),
                "responses": {
                    "200": {"description": "The instance", "content": content},
                    "404": {"description": "No such instance"},
                },
            },
            "put": {
                "tags": [name],
                "summary": f"Replace an instance of {name}",
                "operationId": f"replace_{name}",
                "parameters": parameters + openapi_parameters(write=True),
                "requestBody": request,
                "responses": {
                    "200": {"description": "The instance was replaced"},
                    "400": {"description": "Invalid body or failed commit"},
                },
            },
            "patch": {
                "tags": [name],
                "summary": f"Merge into an instance of {name}",
                "operationId": f"merge_{name}",
                "parameters": parameters + openapi_parameters(write=True),
                "requestBody": request,
                "responses": {
                    "200": {"description": "The instance was merged"},
                    "400": {"description": "Invalid body or failed commit"},
                },
            },
            "delete": {
                "tags": [name],
                "summary": f"Delete an instance of {name}",
                "operationId": f"delete_{name}",
                "parameters": parameters + openapi_parameters(write=True),
                "responses": {
                    "204": {"description": "The instance was deleted"},
                    "404": {"description": "No such instance"},
                },
            },
        }

        paths[f"/services/{name}/{instance}/apply"] = {
            "post": {
                "tags": [name],
                "summary": f"Apply an instance of {name}",
                "description": "Runs the service scripts of the instance and "
                "returns what they change.",
                "operationId": f"apply_{name}",
                "parameters": parameters
                + [openapi_parameter("diff"), openapi_parameter("timeout")],
                "responses": {
                    "200": {"description": "The diff of the applied service"},
                    "400": {"description": "The service failed to apply"},
                },
            }
        }

    tags = [
        {"name": "controller", "description": "Controller wide resources"},
        {"name": "devices", "description": "The devices of the controller"},
    ]

    for name in sorted(services):
        tags.append(
            {
                "name": name,
                "description": services[name].description
                or f"The {name} service, {services[name].module}",
            }
        )

    return {
        "openapi": "3.0.3",
        "info": {
            "title": "Clixon controller services",
            "version": __version__,
            "description": "REST API rendered from the service YANG modules "
            f"served by the clixon backend on {sockpath}.",
        },
        "servers": [{"url": prefix or "/"}],
        "tags": tags,
        "paths": paths,
        "components": {"schemas": schemas},
    }


SWAGGER_HTML = """<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Clixon controller services</title>
    <link rel="stylesheet" href="{ui}/swagger-ui.css">
  </head>
  <body>
    <div id="swagger-ui"></div>
    <script src="{ui}/swagger-ui-bundle.js"></script>
    <script>
      window.ui = SwaggerUIBundle({{
        url: "{openapi}",
        dom_id: "#swagger-ui",
        deepLinking: true,
        tryItOutEnabled: true
      }});
    </script>
  </body>
</html>
"""


class RestHandler(BaseHTTPRequestHandler):
    """
    Handler of the REST API requests.
    """

    server_version = f"clixon_rest/{__version__}"
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt: str, *args: object) -> None:
        """
        Log through the clixon logger instead of stderr.
        """

        logger.info(f"{self.address_string()} {fmt % args}")

    def log_error(self, fmt: str, *args: object) -> None:
        logger.error(f"{self.address_string()} {fmt % args}")

    def address_string(self) -> str:
        """
        Return the address of the client, the one NGINX forwards if any.
        """

        forwarded = self.headers.get("X-Forwarded-For")

        if forwarded:
            return forwarded.split(",")[0].strip()

        if isinstance(self.client_address, tuple):
            return self.client_address[0]

        return "unix"

    @property
    def user(self) -> str:
        """
        Return the user of the NETCONF session. The user authenticated by the
        web server is used if it forwards one.
        """

        user = self.headers.get(self.server.args.user_header)

        if user:
            return re.sub(r"[^\w.@-]", "", user)[:64]

        return self.server.args.user

    def do_GET(self) -> None:
        self.__handle("GET")

    def do_POST(self) -> None:
        self.__handle("POST")

    def do_PUT(self) -> None:
        self.__handle("PUT")

    def do_PATCH(self) -> None:
        self.__handle("PATCH")

    def do_DELETE(self) -> None:
        self.__handle("DELETE")

    def __handle(self, method: str) -> None:
        """
        Route a request and send the response.
        """

        try:
            self.__route(method)
        except RestError as e:
            self.__send_error(e.status, e.message)
        except RPCError as e:
            self.__send_error(HTTPStatus.BAD_REQUEST, str(e))
        except TimeoutException as e:
            self.__send_error(HTTPStatus.GATEWAY_TIMEOUT, str(e))
        except (BrokenPipeError, ConnectionResetError):
            logger.debug(f"The client went away during {method} {self.path}")
        except (SocketClosedError, ConnectionError, OSError) as e:
            self.__send_error(
                HTTPStatus.BAD_GATEWAY, f"Backend communication failed: {e}"
            )
        except Exception as e:
            logger.exception(f"Request {method} {self.path} failed: {e}")
            self.__send_error(HTTPStatus.INTERNAL_SERVER_ERROR, str(e))

    def __route(self, method: str) -> None:
        """
        Route a request to its handler.
        """

        url = urlparse(self.path)
        prefix = self.server.args.prefix.rstrip("/")
        path = url.path

        # NGINX may or may not strip the prefix, both are accepted.
        if prefix and path.startswith(prefix):
            path = path[len(prefix) :]

        path = path.rstrip("/")
        query = parse_qs(url.query)
        parts = [p for p in path.split("/") if p != ""]

        # Kept for the handlers which open a session without taking the query
        # apart themselves, see __connect.
        self.query = query

        if not parts:
            self.__index()
            return

        if parts == ["health"]:
            self.__require(method, "GET")
            self.__health()
            return

        if parts == ["openapi.json"]:
            self.__require(method, "GET")
            self.__openapi()
            return

        if parts == ["docs"]:
            self.__require(method, "GET")
            self.__docs()
            return

        if parts == ["push"]:
            self.__require(method, "POST")
            self.__push()
            return

        if parts == ["commit"]:
            self.__require(method, "POST")
            self.__commit_datastore(query)
            return

        if parts == ["rollback"]:
            self.__require(method, "POST")
            self.__rollback()
            return

        if parts == ["compare"]:
            self.__require(method, "GET")
            self.__compare()
            return

        if parts == ["schemas"]:
            self.__require(method, "GET")
            self.__schemas()
            return

        if parts == ["transactions"]:
            self.__require(method, "GET")
            self.__transactions()
            return

        if len(parts) == 2 and parts[0] == "transactions":
            self.__require(method, "GET")
            self.__transactions(parts[1])
            return

        if parts == ["config"]:
            if method == "GET":
                self.__get_config(query)
            elif method == "PATCH":
                self.__edit_config(query)
            else:
                self.__require(method, "GET", "PATCH")
            return

        if parts[0] == "devices":
            if len(parts) == 1:
                self.__require(method, "GET")
                self.__devices()
                return

            if parts == ["devices", "diff"]:
                self.__require(method, "GET")
                self.__devices_diff(query)
                return

            if parts == ["devices", "pull"]:
                self.__require(method, "POST")
                self.__pull()
                return

            if parts == ["devices", "connect"]:
                self.__require(method, "POST")
                self.__connection_open()
                return

            if parts == ["devices", "rpc"]:
                self.__require(method, "POST")
                self.__device_rpc()
                return

            if parts == ["devices", "template"]:
                self.__require(method, "POST")
                self.__apply_template(query)
                return

        if parts[0] == "yang":
            self.__require(method, "GET")

            if len(parts) != 2:
                raise RestError(HTTPStatus.NOT_FOUND, "Expected /yang/{module}")

            self.__yang(unquote(parts[1]))
            return

        if parts[0] == "services":
            if len(parts) == 1:
                self.__require(method, "GET")
                self.__services()
                return

            service = self.server.registry.service(unquote(parts[1]))

            if len(parts) == 2:
                if method == "GET":
                    self.__get_instances(service, query)
                elif method == "POST":
                    self.__create(service, query)
                else:
                    self.__require(method, "GET", "POST")
                return

            if len(parts) == 3:
                instance = parts[2]

                if method == "GET":
                    self.__get_instance(service, instance, query)
                elif method in ["PUT", "PATCH"]:
                    self.__write(service, instance, query, method)
                elif method == "DELETE":
                    self.__delete(service, instance, query)
                else:
                    self.__require(method, "GET", "PUT", "PATCH", "DELETE")
                return

            if len(parts) == 4 and parts[3] == "apply":
                self.__require(method, "POST")
                self.__apply_service(service, parts[2], query)
                return

        raise RestError(HTTPStatus.NOT_FOUND, f"No such resource: {url.path}")

    def __require(self, method: str, *allowed: str) -> None:
        """
        Raise unless the method is allowed on the resource.
        """

        if method not in allowed:
            raise RestError(
                HTTPStatus.METHOD_NOT_ALLOWED,
                f"{method} is not allowed here, use {', '.join(allowed)}",
            )

    def __writable(self) -> None:
        """
        Raise if the server is read only.
        """

        if self.server.args.read_only:
            raise RestError(
                HTTPStatus.FORBIDDEN, "The server is running in read only mode"
            )

    def __read_body(self, required: Optional[bool] = True) -> str:
        """
        Read the body of the request.
        """

        try:
            length = int(self.headers.get("Content-Length", 0))
        except ValueError:
            raise RestError(HTTPStatus.BAD_REQUEST, "Invalid Content-Length")

        if length <= 0:
            if required:
                raise RestError(HTTPStatus.BAD_REQUEST, "Expected a body")

            return ""

        if length > MAX_BODY:
            raise RestError(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, "Body too large")

        try:
            return self.rfile.read(length).decode()
        except UnicodeDecodeError as e:
            raise RestError(HTTPStatus.BAD_REQUEST, f"Invalid body: {e}")

    def __body(self, required: Optional[bool] = True) -> dict:
        """
        Read and parse the JSON body of the request.
        """

        body = self.__read_body(required=required)

        if not body:
            return {}

        try:
            parsed = json.loads(body)
        except json.JSONDecodeError as e:
            raise RestError(HTTPStatus.BAD_REQUEST, f"Invalid JSON body: {e}")

        if not isinstance(parsed, dict):
            raise RestError(HTTPStatus.BAD_REQUEST, "Expected a JSON object")

        return parsed

    def __xml_body(self) -> Element:
        """
        Read and parse the XML body of the request.
        """

        body = self.__read_body()

        try:
            root = parse_string(body)
        except Exception as e:
            raise RestError(HTTPStatus.BAD_REQUEST, f"Invalid XML body: {e}")

        if not root.get_elements():
            raise RestError(HTTPStatus.BAD_REQUEST, "Expected an XML body")

        return root

    def __flag(self, query: dict, name: str, default: bool) -> bool:
        """
        Return a boolean query parameter.
        """

        if name not in query:
            return default

        value = query[name][0].lower()

        if value in ["true", "1", "yes"]:
            return True

        if value in ["false", "0", "no"]:
            return False

        raise RestError(
            HTTPStatus.BAD_REQUEST, f"The {name} parameter must be true or false"
        )

    def __source(self, query: dict) -> str:
        """
        Return the datastore to read from.
        """

        source = query.get("source", ["running"])[0]

        if source not in ["running", "candidate", "actions"]:
            raise RestError(
                HTTPStatus.BAD_REQUEST,
                "The source parameter must be running, candidate or actions",
            )

        return source

    def __connect(self, **kwargs: object) -> Connection:
        """
        Open a NETCONF session to the backend.
        """

        timeout = self.server.args.timeout
        given = self.query.get("timeout", [None])[0]

        if given is not None:
            if not given.isdigit() or not 1 <= int(given) <= MAX_TIMEOUT:
                raise RestError(
                    HTTPStatus.BAD_REQUEST,
                    f"The timeout parameter must be a number of seconds, "
                    f"at most {MAX_TIMEOUT}",
                )

            timeout = int(given)

        return connect(self.server.args.sockpath, self.user, timeout=timeout, **kwargs)

    def __commit(self, clx: object, query: dict) -> dict:
        """
        Commit the candidate datastore, as asked for by the query.

        Committing with a push runs the services, which is the only way the
        controller runs them. Committing without a push is a local commit, the
        services are left alone, see the description of the push parameter.
        """

        result = {"committed": False, "pushed": False}

        if not self.__flag(query, "commit", True):
            return result

        if self.__flag(query, "push", True):
            clx.commit_services(push=True)

            result["committed"] = True
            result["pushed"] = True

            return result

        clx.commit()
        result["committed"] = True

        return result

    def __lock(self, clx: object, query: dict) -> Locked:
        """
        Lock the candidate datastore for the rest of the request, if the query
        asks for it.
        """

        return Locked(clx, self.__flag(query, "lock", False))

    def __device(self, body: dict) -> dict:
        """
        Return the device and the device-group of a request body.
        """

        device = body.get("device")
        group = body.get("device-group")

        if device and group:
            raise RestError(
                HTTPStatus.BAD_REQUEST,
                "device and device-group are mutually exclusive",
            )

        return {"device": device, "device-group": group}

    def __template(self, body: dict) -> dict:
        """
        Return the template arguments of a request body.
        """

        template = body.get("template")

        if not template:
            raise RestError(HTTPStatus.BAD_REQUEST, "Expected a template")

        variables = body.get("variables", {})

        if not isinstance(variables, dict):
            raise RestError(HTTPStatus.BAD_REQUEST, "Expected an object of variables")

        return {
            "template": template,
            "variables": {k: str(v) for k, v in variables.items()},
            "inline": bool(body.get("inline", False)),
        }

    def __index(self) -> None:
        """
        Send an index of the API.
        """

        prefix = self.__prefix()

        self.__send_json(
            HTTPStatus.OK,
            {
                "name": "clixon controller services",
                "version": __version__,
                "endpoints": {
                    "commit": f"{prefix}/commit",
                    "compare": f"{prefix}/compare",
                    "config": f"{prefix}/config",
                    "devices": f"{prefix}/devices",
                    "docs": f"{prefix}/docs",
                    "health": f"{prefix}/health",
                    "openapi": f"{prefix}/openapi.json",
                    "push": f"{prefix}/push",
                    "rollback": f"{prefix}/rollback",
                    "schemas": f"{prefix}/schemas",
                    "services": f"{prefix}/services",
                    "transactions": f"{prefix}/transactions",
                },
            },
        )

    def __health(self) -> None:
        """
        Send the health of the backend connection.
        """

        with self.__connect() as clx:
            schemas = clx.get_schemas()

        self.__send_json(
            HTTPStatus.OK,
            {
                "status": "ok",
                "sockpath": self.server.args.sockpath,
                "schemas": len(schemas),
                "services": sorted(self.server.registry.services),
            },
        )

    def __services(self) -> None:
        """
        Send the list of services.
        """

        services = self.server.registry.services
        prefix = self.__prefix()

        self.__send_json(
            HTTPStatus.OK,
            [
                {
                    "name": name,
                    "description": services[name].description,
                    "module": services[name].module,
                    "revision": services[name].revision,
                    "namespace": services[name].namespace,
                    "keys": services[name].keys,
                    "url": f"{prefix}/services/{name}",
                    "yang": f"{prefix}/yang/{services[name].module}",
                }
                for name in sorted(services)
            ],
        )

    def __yang(self, module: str) -> None:
        """
        Send the YANG of a module. The service modules are cached, the other
        modules the backend serves are fetched when asked for.
        """

        modules = self.server.registry.modules

        if module in modules:
            self.__send(HTTPStatus.OK, modules[module].encode(), "text/plain")
            return

        if not re.match(r"^[\w.-]+$", module):
            raise RestError(HTTPStatus.BAD_REQUEST, f"Invalid module name: {module}")

        with self.__connect() as clx:
            try:
                text = clx.get_service_yang(module)
            except (RPCError, ValueError):
                raise RestError(HTTPStatus.NOT_FOUND, f"No such module: {module}")

        self.__send(HTTPStatus.OK, text.encode(), "text/plain")

    def __schemas(self) -> None:
        """
        Send the YANG schemas the backend serves.
        """

        with self.__connect() as clx:
            schemas = clx.get_schemas()

        self.__send_json(HTTPStatus.OK, schemas)

    def __openapi(self) -> None:
        """
        Send the OpenAPI description.
        """

        spec = openapi(
            self.server.registry.services,
            self.__prefix(),
            self.server.args.sockpath,
        )

        self.__send_json(HTTPStatus.OK, spec)

    def __docs(self) -> None:
        """
        Send the Swagger UI page.
        """

        html = SWAGGER_HTML.format(
            ui=self.server.args.swagger_ui.rstrip("/"),
            openapi=f"{self.__prefix()}/openapi.json",
        )

        self.__send(HTTPStatus.OK, html.encode(), "text/html; charset=utf-8")

    def __push(self) -> None:
        """
        Push the committed configuration to the devices.
        """

        self.__writable()

        with self.__connect(read_only=False) as clx:
            try:
                clx.push()
            except RPCError as e:
                # The devices are already up to date, which is not an error
                # worth a failed request.
                if "No changes to push" not in str(e):
                    raise

                self.__send_json(HTTPStatus.OK, {"pushed": False, "detail": str(e)})

                return

        self.__send_json(HTTPStatus.OK, {"pushed": True})

    def __commit_datastore(self, query: dict) -> None:
        """
        Commit the candidate datastore.
        """

        self.__writable()

        with self.__connect(read_only=False) as clx:
            with self.__lock(clx, query):
                result = self.__commit(clx, {**query, "commit": ["true"]})

        self.__send_json(HTTPStatus.OK, result)

    def __rollback(self) -> None:
        """
        Discard the changes of the candidate datastore.
        """

        self.__writable()

        with self.__connect(read_only=False) as clx:
            clx.rollback()

        self.__send_json(HTTPStatus.OK, {"rolled-back": True})

    def __compare(self) -> None:
        """
        Send the difference between the running and the candidate datastore.
        """

        with self.__connect() as clx:
            diff = clx.show_compare()

        self.__send_json(HTTPStatus.OK, {"diff": diff})

    def __transactions(self, tid: Optional[str] = None) -> None:
        """
        Send the transactions of the backend.
        """

        if tid is not None and not tid.isdigit():
            raise RestError(
                HTTPStatus.BAD_REQUEST, "The transaction id must be a number"
            )

        with self.__connect() as clx:
            data = clx.show_transactions(tid=int(tid) if tid else None)

        transactions = elements_to_json(data, "transaction")

        if tid is not None:
            if not transactions:
                raise RestError(HTTPStatus.NOT_FOUND, f"No such transaction: {tid}")

            self.__send_json(HTTPStatus.OK, transactions[0])
            return

        self.__send_json(HTTPStatus.OK, transactions)

    def __devices(self) -> None:
        """
        Send the devices, their connection state and their log message.
        """

        with self.__connect() as clx:
            data = clx.show_devices()

        self.__send_json(HTTPStatus.OK, elements_to_json(data, "device"))

    def __devices_diff(self, query: dict) -> None:
        """
        Send the difference between the devices and the controller. The
        devices are pulled transiently to make the comparison.
        """

        device = query.get("device", ["*"])[0]

        with self.__connect(read_only=False) as clx:
            diff = clx.show_devices_diff(device=device, dict_format=True)

        self.__send_json(HTTPStatus.OK, diff or {})

    def __pull(self) -> None:
        """
        Pull the configuration of the devices.
        """

        self.__writable()

        body = self.__body(required=False)
        device = body.get("device", "*")
        transient = bool(body.get("transient", False))

        with self.__connect(read_only=False) as clx:
            clx.pull(device=device, transient=transient)

        self.__send_json(
            HTTPStatus.OK, {"pulled": True, "device": device, "transient": transient}
        )

    def __connection_open(self) -> None:
        """
        Open the connection to the devices.
        """

        self.__writable()

        body = self.__body(required=False)
        device = body.get("device", "*")

        with self.__connect(read_only=False) as clx:
            data = clx.connection_open(devname=device)

        if data is None:
            raise RestError(
                HTTPStatus.BAD_GATEWAY, f"Could not open the connection to {device}"
            )

        self.__send_json(HTTPStatus.OK, {"opened": True, "device": device})

    def __device_rpc(self) -> None:
        """
        Apply a RPC template to the devices.
        """

        self.__writable()

        body = self.__body()
        device = self.__device(body)
        template = self.__template(body)

        with self.__connect(read_only=False) as clx:
            try:
                devices = clx.device_rpc(
                    devname=device["device"],
                    groupname=device["device-group"],
                    **template,
                )
            except ValueError as e:
                raise RestError(HTTPStatus.BAD_REQUEST, str(e))

        self.__send_json(HTTPStatus.OK, element_to_dict(devices))

    def __apply_template(self, query: dict) -> None:
        """
        Apply a configuration template to the devices.
        """

        self.__writable()

        body = self.__body()
        device = self.__device(body)
        template = self.__template(body)
        push = self.__flag(query, "push", True)

        with self.__connect(read_only=False, push=push) as clx:
            with self.__lock(clx, query):
                try:
                    clx.apply_template(
                        devname=device["device"],
                        groupname=device["device-group"],
                        **template,
                    )
                except ValueError as e:
                    raise RestError(HTTPStatus.BAD_REQUEST, str(e))

                result = self.__commit(clx, query)

        result["applied"] = True

        self.__send_json(HTTPStatus.OK, result)

    def __apply_service(self, service: Service, instance: str, query: dict) -> None:
        """
        Apply a service instance, which runs its service scripts.
        """

        self.__writable()

        # Applying with a diff only leaves the datastores untouched, applying
        # for real commits and pushes.
        diff = self.__flag(query, "diff", True)

        with self.__connect(read_only=diff) as clx:
            try:
                result = clx.apply_service(service.name, unquote(instance), diff=diff)
            except ValueError as e:
                raise RestError(HTTPStatus.BAD_REQUEST, str(e))

        self.__send_json(HTTPStatus.OK, {"applied": not diff, "diff": result})

    def __get_config(self, query: dict) -> None:
        """
        Send a part of the configuration, selected by an xpath.
        """

        xpath = query.get("xpath", ["/"])[0]
        namespaces = {}

        for namespace in query.get("namespace", []):
            if ":" not in namespace:
                raise RestError(
                    HTTPStatus.BAD_REQUEST,
                    "A namespace must be given as prefix:uri",
                )

            prefix, uri = namespace.split(":", 1)
            namespaces[prefix] = uri

        with self.__connect(source=self.__source(query)) as clx:
            root = clx.get_root(xpath=xpath, namespaces=namespaces or None)

        if query.get("format", ["json"])[0] == "xml":
            self.__send(
                HTTPStatus.OK,
                (root.dumps() if root else "").encode(),
                "application/xml",
            )
            return

        self.__send_json(HTTPStatus.OK, element_to_dict(root))

    def __edit_config(self, query: dict) -> None:
        """
        Merge a piece of XML configuration into the candidate datastore.
        """

        self.__writable()

        push = self.__flag(query, "push", True)
        root = self.__xml_body()

        with self.__connect(read_only=False, push=push) as clx:
            with self.__lock(clx, query):
                clx.set_root(root)
                result = self.__commit(clx, query)

        self.__send_json(HTTPStatus.OK, result)

    def __get_instances(self, service: Service, query: dict) -> None:
        """
        Send all instances of a service.
        """

        with self.__connect(source=self.__source(query)) as clx:
            elements = instances(clx, service)

            self.__send_json(
                HTTPStatus.OK,
                [element_to_json(service.node, e) for e in elements],
            )

    def __get_instance(self, service: Service, instance: str, query: dict) -> None:
        """
        Send one instance of a service.
        """

        with self.__connect(source=self.__source(query)) as clx:
            elements = instances(clx, service, instance)

            if not elements:
                raise RestError(
                    HTTPStatus.NOT_FOUND,
                    f"No such instance of {service.name}: {instance}",
                )

            self.__send_json(HTTPStatus.OK, element_to_json(service.node, elements[0]))

    def __create(self, service: Service, query: dict) -> None:
        """
        Create an instance of a service.
        """

        self.__writable()

        body = self.__body()
        push = self.__flag(query, "push", True)
        root = instance_element(service, body, operation="create")

        with self.__connect(read_only=False, push=push) as clx:
            with self.__lock(clx, query):
                try:
                    clx.set_root(root)
                except RPCError as e:
                    if "exists" in str(e).lower():
                        raise RestError(HTTPStatus.CONFLICT, str(e))
                    raise RestError(HTTPStatus.BAD_REQUEST, str(e))

                result = self.__commit(clx, query)

        keys = ",".join(str(body[key]) for key in service.keys)
        result["url"] = f"{self.__prefix()}/services/{service.name}/{keys}"

        self.__send_json(HTTPStatus.CREATED, result)

    def __write(
        self, service: Service, instance: str, query: dict, method: str
    ) -> None:
        """
        Replace or merge an instance of a service.
        """

        self.__writable()

        body = self.__body()
        values = service.key_values(instance)

        for key, value in zip(service.keys, values):
            if key in body and str(body[key]) != value:
                raise RestError(
                    HTTPStatus.BAD_REQUEST,
                    f"The key {key} of the body does not match the URL",
                )

            body[key] = value

        operation = "replace" if method == "PUT" else "merge"
        push = self.__flag(query, "push", True)
        root = instance_element(service, body, operation=operation)

        with self.__connect(read_only=False, push=push) as clx:
            with self.__lock(clx, query):
                clx.set_root(root)
                result = self.__commit(clx, query)

        self.__send_json(HTTPStatus.OK, result)

    def __delete(self, service: Service, instance: str, query: dict) -> None:
        """
        Delete an instance of a service.
        """

        self.__writable()

        push = self.__flag(query, "push", True)
        data = dict(zip(service.keys, service.key_values(instance)))
        root = instance_element(service, data, operation="delete")

        with self.__connect(read_only=False, push=push) as clx:
            with self.__lock(clx, query):
                try:
                    clx.set_root(root)
                except RPCError as e:
                    if "data-missing" in str(e) or "does not exist" in str(e):
                        raise RestError(
                            HTTPStatus.NOT_FOUND,
                            f"No such instance of {service.name}: {instance}",
                        )
                    raise

                self.__commit(clx, query)

        self.__send(HTTPStatus.NO_CONTENT, b"", "application/json")

    def __prefix(self) -> str:
        """
        Return the path prefix the client sees, which is the one NGINX
        forwards if it forwards one.
        """

        forwarded = self.headers.get("X-Forwarded-Prefix")

        if forwarded:
            return "/" + forwarded.strip().strip("/")

        return self.server.args.prefix.rstrip("/")

    def __send(self, status: HTTPStatus, body: bytes, content_type: str) -> None:
        """
        Send a response.
        """

        self.send_response(status)

        if status != HTTPStatus.NO_CONTENT:
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))

        self.send_header("Cache-Control", "no-store")
        self.end_headers()

        if body:
            self.wfile.write(body)

    def __send_json(self, status: HTTPStatus, body: object) -> None:
        """
        Send a JSON response.
        """

        self.__send(
            status,
            json.dumps(body, indent=2).encode() + b"\n",
            "application/json",
        )

    def __send_error(self, status: HTTPStatus, message: str) -> None:
        """
        Send a JSON error response.
        """

        logger.warning(f"{self.command} {self.path}: {status.value} {message}")

        self.__send_json(
            status,
            {"error": {"status": status.value, "message": message}},
        )


class RestServer(ThreadingHTTPServer):
    """
    HTTP server serving the REST API on a TCP port.
    """

    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, address: tuple, args: object, registry: Registry) -> None:
        self.args = args
        self.registry = registry

        super().__init__(address, RestHandler)


class UnixRestServer(ThreadingMixIn, UnixStreamServer):
    """
    HTTP server serving the REST API on a UNIX socket, which is what NGINX
    connects to when proxy_pass points at a socket.
    """

    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, path: str, args: object, registry: Registry) -> None:
        self.args = args
        self.registry = registry
        self.server_name = "localhost"
        self.server_port = 0

        if os.path.exists(path):
            os.unlink(path)

        super().__init__(path, RestHandler)

        os.chmod(path, 0o660)

    def get_request(self) -> tuple:
        """
        Return a client address the HTTP handler accepts, UNIX sockets have
        none of their own.
        """

        request, _ = super().get_request()

        return request, ("unix", 0)


def create_server(args: argparse.Namespace, registry: Registry) -> object:
    """
    Create the HTTP server.

    :param args: Parsed arguments
    :type args: argparse.Namespace
    :param registry: Registry of services
    :type registry: Registry
    :return: Server
    :rtype: socketserver.BaseServer

    """

    if args.unix_socket:
        server = UnixRestServer(args.unix_socket, args, registry)
        logger.info(f"Listening on the UNIX socket {args.unix_socket}")
    else:
        server = RestServer((args.address, args.port), args, registry)
        logger.info(f"Listening on {args.address}:{args.port}")

    return server


def main() -> None:
    """
    Main function for clixon_rest.
    """

    if ARGS.version:
        print(__version__)
        sys.exit(0)

    if not ARGS.unix_socket and not os.path.exists(ARGS.sockpath):
        logger.error(f"No such clixon socket: {ARGS.sockpath}")
        sys.exit(1)

    registry = Registry(ARGS.sockpath, ARGS.user)

    try:
        registry.load()
    except (OSError, socket.error, RestError, RPCError) as e:
        logger.error(f"Could not load the service YANG from the backend: {e}")
        sys.exit(1)

    server = create_server(ARGS, registry)

    def __reload(*_: object) -> None:
        """
        Reload the service YANG on SIGHUP.
        """

        logger.info("Reloading the service YANG")

        try:
            registry.load()
        except Exception as e:
            logger.error(f"Could not reload the service YANG: {e}")

    def __stop(*_: object) -> None:
        """
        Stop the server on SIGTERM. serve_forever runs in this thread, so the
        shutdown has to be done from another one.
        """

        logger.info("Shutting down")
        threading.Thread(target=server.shutdown, daemon=True).start()

    signal.signal(signal.SIGHUP, __reload)
    signal.signal(signal.SIGTERM, __stop)

    logger.info(f"Serving the API on {ARGS.prefix}, Swagger UI on {ARGS.prefix}/docs")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("\nGoodbye.")
    finally:
        server.server_close()

        if ARGS.unix_socket and os.path.exists(ARGS.unix_socket):
            os.unlink(ARGS.unix_socket)


if __name__ == "__main__":
    main()
