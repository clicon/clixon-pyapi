import json
import os
import socket
import threading

from http.client import HTTPConnection
from unittest.mock import patch

import pytest

import clixon.args
import clixon_rest

from clixon.exceptions import RPCError, TimeoutException
from clixon.parser import parse_string
from tests.test_yang import MODULES

CONFIG = (
    '<data><services xmlns="http://clicon.org/controller">'
    '<test-service xmlns="http://clicon.org/test-service">'
    "<service-name>test</service-name><enabled>false</enabled>"
    "<peer><name>p1</name><port>830</port></peer>"
    "</test-service>"
    '<test-service xmlns="http://clicon.org/test-service">'
    "<service-name>other</service-name></test-service>"
    "</services></data>"
)

DEVICES = (
    '<rpc-reply xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"><data>'
    '<devices xmlns="http://clicon.org/controller">'
    "<device><name>r1</name><conn-state>OPEN</conn-state></device>"
    "</devices></data></rpc-reply>"
)

TRANSACTIONS = (
    '<rpc-reply xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"><data>'
    '<transactions xmlns="http://clicon.org/controller">'
    "<transaction><tid>1</tid><result>SUCCESS</result></transaction>"
    "</transactions></data></rpc-reply>"
)

SCHEMAS = [
    {
        "identifier": "test-service",
        "version": "2024-01-01",
        "format": "yang",
        "namespace": "http://clicon.org/test-service",
    },
    {
        "identifier": "ietf-inet-types",
        "version": "2021-02-22",
        "format": "yang",
        "namespace": "urn:ietf:params:xml:ns:yang:ietf-inet-types",
    },
]


class StubClixon:
    """
    A Clixon object which answers from canned data and records what it is
    asked to do.
    """

    calls = []
    errors = {}

    def __init__(self, **kwargs):
        self.kwargs = kwargs

        StubClixon.calls.append(("init", (), kwargs))

    def __record(self, name, *args, **kwargs):
        StubClixon.calls.append((name, args, kwargs))

        error = StubClixon.errors.get(name)

        if error:
            raise error

    def close_session(self):
        self.__record("close_session")

    def get_schemas(self):
        self.__record("get_schemas")

        return SCHEMAS

    def get_service_yang(self, name, revision=None, format="yang"):
        self.__record("get_service_yang", name)

        if name not in MODULES:
            raise RPCError(f"No such module: {name}")

        return MODULES[name]

    def get_root(self, path=None, xpath="/", namespaces=None):
        self.__record("get_root", xpath, namespaces)

        root = parse_string(CONFIG).data

        if "service-name='test'" in xpath:
            for element in root.services.get_elements("test-service"):
                if element.service_name != "test":
                    root.services.delete(element)
        elif "service-name=" in xpath:
            return parse_string("<data/>").data

        return root

    def set_root(self, root):
        self.__record("set_root", root.dumps())

    def commit(self):
        self.__record("commit")

    def commit_services(self, push=None, device="*"):
        self.__record("commit_services", push, device)

    def push(self):
        self.__record("push")

    def rollback(self):
        self.__record("rollback")

    def lock(self, target="candidate"):
        self.__record("lock", target)

    def unlock(self, target="candidate"):
        self.__record("unlock", target)

    def pull(self, device="*", transient=False):
        self.__record("pull", device, transient)

    def connection_open(self, devname="*"):
        self.__record("connection_open", devname)

        return "<ok/>"

    def show_compare(self):
        self.__record("show_compare")

        return "+ hostname foo"

    def show_transactions(self, tid=None):
        self.__record("show_transactions", tid)

        return TRANSACTIONS

    def show_devices(self):
        self.__record("show_devices")

        return DEVICES

    def show_devices_diff(self, device="*", dict_format=False):
        self.__record("show_devices_diff", device)

        return {"r1": "- a\n+ b\n"}

    def device_rpc(self, devname=None, groupname=None, **kwargs):
        self.__record("device_rpc", devname, groupname, kwargs)

        return parse_string(
            "<devices><device><name>r1</name></device></devices>"
        ).devices

    def apply_template(self, devname=None, groupname=None, **kwargs):
        self.__record("apply_template", devname, groupname, kwargs)

        return True

    def apply_service(self, service, instance, diff=True):
        self.__record("apply_service", service, instance, diff)

        return "+ hostname foo"


class UnixHTTPConnection(HTTPConnection):
    """
    A HTTP connection over a UNIX socket, the way NGINX connects.
    """

    def __init__(self, path):
        super().__init__("localhost", timeout=10)

        self.path = path

    def connect(self):
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.settimeout(10)
        self.sock.connect(self.path)


def start_server(read_only=False):
    """
    Start a server with a stubbed backend, return it and its port.
    """

    args = clixon_rest.parse_args(["-s", "/tmp/test.sock"])
    args.read_only = read_only

    registry = clixon_rest.Registry(args.sockpath)
    registry.load()

    server = clixon_rest.RestServer(("127.0.0.1", 0), args, registry)

    threading.Thread(target=server.serve_forever, daemon=True).start()

    return server, server.server_address[1]


@pytest.fixture(scope="module")
def stub():
    """
    Patch the Clixon object of the server for the whole module.
    """

    with patch.object(clixon_rest, "Clixon", StubClixon):
        yield StubClixon


@pytest.fixture(scope="module")
def server(stub):
    """
    A running server, and a read only one.
    """

    server, port = start_server()
    read_only, read_only_port = start_server(read_only=True)

    yield port, read_only_port

    server.shutdown()
    server.server_close()
    read_only.shutdown()
    read_only.server_close()


@pytest.fixture(autouse=True)
def clean_calls():
    """
    Forget the calls and the errors of the stub between the tests.
    """

    StubClixon.calls = []
    StubClixon.errors = {}

    yield

    StubClixon.calls = []
    StubClixon.errors = {}


def request(port, method, path, body=None, headers=None, raw=False):
    """
    Make a request and return the status and the parsed body.
    """

    connection = HTTPConnection("127.0.0.1", port, timeout=10)

    if body is not None and not raw:
        body = json.dumps(body)

    connection.request(method, path, body=body, headers=headers or {})
    response = connection.getresponse()
    data = response.read().decode()
    connection.close()

    if response.getheader("Content-Type", "").startswith("application/json"):
        return response.status, json.loads(data) if data else None

    return response.status, data


def called(name):
    """
    Return the calls of a given name made to the stub.
    """

    return [c for c in StubClixon.calls if c[0] == name]


def test_index(server):
    """
    Test that the index lists the endpoints.
    """

    port, _ = server
    status, body = request(port, "GET", "/api/v1/")

    assert status == 200
    assert body["endpoints"]["docs"] == "/api/v1/docs"


def test_health(server):
    """
    Test that the health tells about the backend.
    """

    port, _ = server
    status, body = request(port, "GET", "/api/v1/health")

    assert status == 200
    assert body["status"] == "ok"
    assert body["schemas"] == len(SCHEMAS)
    assert body["services"] == ["test-service"]


def test_services(server):
    """
    Test that the services found in the YANG are listed.
    """

    port, _ = server
    status, body = request(port, "GET", "/api/v1/services")

    assert status == 200
    assert body[0]["name"] == "test-service"
    assert body[0]["keys"] == ["service-name"]
    assert body[0]["module"] == "test-service"


def test_get_instances(server):
    """
    Test that the instances of a service are returned as JSON.
    """

    port, _ = server
    status, body = request(port, "GET", "/api/v1/services/test-service")

    assert status == 200
    assert body == [
        {
            "service-name": "test",
            "enabled": False,
            "peer": [{"name": "p1", "port": 830}],
        },
        {"service-name": "other"},
    ]


def test_get_instance(server):
    """
    Test that one instance is returned.
    """

    port, _ = server
    status, body = request(port, "GET", "/api/v1/services/test-service/test")

    assert status == 200
    assert body["service-name"] == "test"
    assert called("get_root")[0][1][0] == (
        "/ctrl:services/svc:test-service[svc:service-name='test']"
    )


def test_get_instance_missing(server):
    """
    Test that an unknown instance is a 404.
    """

    port, _ = server
    status, body = request(port, "GET", "/api/v1/services/test-service/nosuch")

    assert status == 404
    assert "No such instance" in body["error"]["message"]


def test_get_instance_source(server):
    """
    Test that the datastore to read from is passed on.
    """

    port, _ = server
    status, _ = request(port, "GET", "/api/v1/services/test-service?source=candidate")

    assert status == 200


def test_get_instance_bad_source(server):
    """
    Test that an unknown datastore is refused.
    """

    port, _ = server
    status, body = request(port, "GET", "/api/v1/services/test-service?source=foo")

    assert status == 400
    assert "running, candidate or actions" in body["error"]["message"]


def test_unknown_service(server):
    """
    Test that an unknown service is a 404.
    """

    port, _ = server
    status, _ = request(port, "GET", "/api/v1/services/nosuch")

    assert status == 404


def test_unknown_resource(server):
    """
    Test that an unknown resource is a 404.
    """

    port, _ = server
    status, _ = request(port, "GET", "/api/v1/nosuch")

    assert status == 404


def test_method_not_allowed(server):
    """
    Test that a method which is not served is a 405.
    """

    port, _ = server
    status, body = request(port, "DELETE", "/api/v1/services")

    assert status == 405
    assert "not allowed" in body["error"]["message"]


def test_create_runs_the_services(server):
    """
    Test that a write commits with the services, which is the only way the
    controller runs them.
    """

    port, _ = server
    status, body = request(
        port,
        "PUT",
        "/api/v1/services/test-service/test",
        {"enabled": True},
    )

    assert status == 200
    assert body == {"committed": True, "pushed": True}
    assert called("commit_services")[0][1] == (True, "*")
    assert called("commit") == []


def test_write_without_push_commits_locally(server):
    """
    Test that a write without a push is a local commit.
    """

    port, _ = server
    status, body = request(
        port,
        "PATCH",
        "/api/v1/services/test-service/test?push=false",
        {"enabled": True},
    )

    assert status == 200
    assert body == {"committed": True, "pushed": False}
    assert called("commit")
    assert called("commit_services") == []


def test_commit_endpoint_runs_the_services(server):
    """
    Test that the commit resource runs the services as well.
    """

    port, _ = server
    status, body = request(port, "POST", "/api/v1/commit")

    assert status == 200
    assert body == {"committed": True, "pushed": True}
    assert called("commit_services")[0][1] == (True, "*")


def test_push_without_changes(server):
    """
    Test that a push with nothing to push is not an error.
    """

    StubClixon.errors["push"] = RPCError("No changes to push")

    port, _ = server
    status, body = request(port, "POST", "/api/v1/push")

    assert status == 200
    assert body["pushed"] is False
    assert "No changes to push" in body["detail"]


def test_push_error(server):
    """
    Test that a push which fails for another reason is an error.
    """

    StubClixon.errors["push"] = RPCError("Device r1 is closed")

    port, _ = server
    status, _ = request(port, "POST", "/api/v1/push")

    assert status == 400


def test_create(server):
    """
    Test that an instance is created and committed.
    """

    port, _ = server
    status, body = request(
        port,
        "POST",
        "/api/v1/services/test-service",
        {"service-name": "new", "enabled": True},
    )

    assert status == 201
    assert body["committed"] is True
    assert body["url"] == "/api/v1/services/test-service/new"

    xml = called("set_root")[0][1][0]

    assert 'nc:operation="create"' in xml
    assert "<service-name>new</service-name>" in xml
    assert "<enabled>true</enabled>" in xml
    assert called("commit_services")


def test_create_without_commit(server):
    """
    Test that a create can be left in the candidate datastore.
    """

    port, _ = server
    status, body = request(
        port,
        "POST",
        "/api/v1/services/test-service?commit=false",
        {"service-name": "new"},
    )

    assert status == 201
    assert body["committed"] is False
    assert called("commit_services") == []


def test_create_with_lock(server):
    """
    Test that the candidate datastore can be locked for the request.
    """

    port, _ = server
    status, _ = request(
        port,
        "POST",
        "/api/v1/services/test-service?lock=true",
        {"service-name": "new"},
    )

    assert status == 201
    assert called("lock") and called("unlock")


def test_create_conflict(server):
    """
    Test that an instance which exists is a conflict.
    """

    StubClixon.errors["set_root"] = RPCError("Data already exists")

    port, _ = server
    status, _ = request(
        port, "POST", "/api/v1/services/test-service", {"service-name": "test"}
    )

    assert status == 409


def test_create_invalid_body(server):
    """
    Test that a body which is not JSON is refused.
    """

    port, _ = server
    status, body = request(
        port, "POST", "/api/v1/services/test-service", "not json", raw=True
    )

    assert status == 400
    assert "Invalid JSON" in body["error"]["message"]


def test_create_without_body(server):
    """
    Test that a create without a body is refused.
    """

    port, _ = server
    status, _ = request(port, "POST", "/api/v1/services/test-service")

    assert status == 400


def test_create_unknown_field(server):
    """
    Test that a field which is not in the YANG is refused.
    """

    port, _ = server
    status, body = request(
        port,
        "POST",
        "/api/v1/services/test-service",
        {"service-name": "new", "nosuch": 1},
    )

    assert status == 400
    assert "Unknown fields" in body["error"]["message"]


def test_replace(server):
    """
    Test that an instance is replaced.
    """

    port, _ = server
    status, _ = request(
        port, "PUT", "/api/v1/services/test-service/test", {"enabled": True}
    )

    assert status == 200
    assert 'nc:operation="replace"' in called("set_root")[0][1][0]


def test_merge(server):
    """
    Test that an instance is merged.
    """

    port, _ = server
    status, _ = request(
        port, "PATCH", "/api/v1/services/test-service/test", {"enabled": True}
    )

    assert status == 200
    assert 'nc:operation="merge"' in called("set_root")[0][1][0]


def test_write_key_mismatch(server):
    """
    Test that a key in the body which is not the one of the URL is refused.
    """

    port, _ = server
    status, _ = request(
        port,
        "PUT",
        "/api/v1/services/test-service/test",
        {"service-name": "other"},
    )

    assert status == 400


def test_delete(server):
    """
    Test that an instance is deleted.
    """

    port, _ = server
    status, body = request(port, "DELETE", "/api/v1/services/test-service/test")

    assert status == 204
    assert body in [None, ""]

    xml = called("set_root")[0][1][0]

    assert 'nc:operation="delete"' in xml
    assert "<service-name>test</service-name>" in xml


def test_delete_missing(server):
    """
    Test that deleting what is not there is a 404.
    """

    StubClixon.errors["set_root"] = RPCError("data-missing")

    port, _ = server
    status, _ = request(port, "DELETE", "/api/v1/services/test-service/nosuch")

    assert status == 404


def test_apply_service(server):
    """
    Test that a service instance is applied.
    """

    port, _ = server
    status, body = request(port, "POST", "/api/v1/services/test-service/test/apply")

    assert status == 200
    assert body == {"applied": False, "diff": "+ hostname foo"}
    assert called("apply_service")[0][1] == ("test-service", "test", True)


def test_apply_service_for_real(server):
    """
    Test that a service instance can be applied for real.
    """

    port, _ = server
    status, body = request(
        port, "POST", "/api/v1/services/test-service/test/apply?diff=false"
    )

    assert status == 200
    assert body["applied"] is True
    assert called("apply_service")[0][1][2] is False


def test_get_config(server):
    """
    Test that any part of the configuration can be read.
    """

    port, _ = server
    status, body = request(
        port,
        "GET",
        "/api/v1/config?xpath=/ctrl:services&namespace=l2c:http://example.com",
    )

    assert status == 200
    assert body["services"]["test-service"][0]["service-name"] == "test"
    assert called("get_root")[0][1] == (
        "/ctrl:services",
        {"l2c": "http://example.com"},
    )


def test_get_config_xml(server):
    """
    Test that the configuration can be read as XML.
    """

    port, _ = server
    status, body = request(port, "GET", "/api/v1/config?format=xml")

    assert status == 200
    assert body.startswith("<services")


def test_get_config_bad_namespace(server):
    """
    Test that a namespace which is not prefix:uri is refused.
    """

    port, _ = server
    status, _ = request(port, "GET", "/api/v1/config?namespace=broken")

    assert status == 400


def test_edit_config(server):
    """
    Test that XML configuration is merged into the candidate datastore.
    """

    port, _ = server
    status, body = request(
        port,
        "PATCH",
        "/api/v1/config",
        "<services><foo/></services>",
        headers={"Content-Type": "application/xml"},
        raw=True,
    )

    assert status == 200
    assert body["committed"] is True
    assert "<foo/>" in called("set_root")[0][1][0]


def test_edit_config_invalid(server):
    """
    Test that a body which is not XML is refused.
    """

    port, _ = server
    status, _ = request(port, "PATCH", "/api/v1/config", "not xml at all", raw=True)

    assert status == 400


def test_commit(server):
    """
    Test that the candidate datastore is committed.
    """

    port, _ = server
    status, body = request(port, "POST", "/api/v1/commit")

    assert status == 200
    assert body == {"committed": True, "pushed": True}
    assert called("commit_services")


def test_push(server):
    """
    Test that the configuration is pushed.
    """

    port, _ = server
    status, body = request(port, "POST", "/api/v1/push")

    assert status == 200
    assert body == {"pushed": True}
    assert called("push")


def test_rollback(server):
    """
    Test that the changes are discarded.
    """

    port, _ = server
    status, body = request(port, "POST", "/api/v1/rollback")

    assert status == 200
    assert body == {"rolled-back": True}
    assert called("rollback")


def test_compare(server):
    """
    Test that the compare is returned.
    """

    port, _ = server
    status, body = request(port, "GET", "/api/v1/compare")

    assert status == 200
    assert body == {"diff": "+ hostname foo"}


def test_transactions(server):
    """
    Test that the transactions are returned.
    """

    port, _ = server
    status, body = request(port, "GET", "/api/v1/transactions")

    assert status == 200
    assert body == [{"tid": "1", "result": "SUCCESS"}]


def test_transaction(server):
    """
    Test that one transaction is returned.
    """

    port, _ = server
    status, body = request(port, "GET", "/api/v1/transactions/1")

    assert status == 200
    assert body["tid"] == "1"
    assert called("show_transactions")[0][1] == (1,)


def test_transaction_invalid(server):
    """
    Test that a transaction id which is not a number is refused.
    """

    port, _ = server
    status, _ = request(port, "GET", "/api/v1/transactions/abc")

    assert status == 400


def test_devices(server):
    """
    Test that the devices are returned.
    """

    port, _ = server
    status, body = request(port, "GET", "/api/v1/devices")

    assert status == 200
    assert body == [{"name": "r1", "conn-state": "OPEN"}]


def test_devices_diff(server):
    """
    Test that the difference against the devices is returned.
    """

    port, _ = server
    status, body = request(port, "GET", "/api/v1/devices/diff?device=r1")

    assert status == 200
    assert body == {"r1": "- a\n+ b\n"}
    assert called("show_devices_diff")[0][1] == ("r1",)


def test_pull(server):
    """
    Test that the devices are pulled.
    """

    port, _ = server
    status, body = request(
        port, "POST", "/api/v1/devices/pull", {"device": "r1", "transient": True}
    )

    assert status == 200
    assert body["device"] == "r1"
    assert called("pull")[0][1] == ("r1", True)


def test_pull_without_body(server):
    """
    Test that a pull without a body pulls all devices.
    """

    port, _ = server
    status, _ = request(port, "POST", "/api/v1/devices/pull")

    assert status == 200
    assert called("pull")[0][1] == ("*", False)


def test_connect(server):
    """
    Test that the connection to a device is opened.
    """

    port, _ = server
    status, body = request(port, "POST", "/api/v1/devices/connect", {"device": "r1"})

    assert status == 200
    assert body["opened"] is True
    assert called("connection_open")[0][1] == ("r1",)


def test_device_rpc(server):
    """
    Test that a RPC template is applied to a device.
    """

    port, _ = server
    status, body = request(
        port,
        "POST",
        "/api/v1/devices/rpc",
        {"device": "r1", "template": "get-config", "variables": {"a": 1}},
    )

    assert status == 200
    assert body == {"device": {"name": "r1"}}

    _, args, _ = called("device_rpc")[0]

    assert args[0] == "r1"
    assert args[2]["variables"] == {"a": "1"}


def test_device_rpc_without_template(server):
    """
    Test that a RPC without a template is refused.
    """

    port, _ = server
    status, _ = request(port, "POST", "/api/v1/devices/rpc", {"device": "r1"})

    assert status == 400


def test_device_rpc_both_targets(server):
    """
    Test that a device and a device group at once is refused.
    """

    port, _ = server
    status, _ = request(
        port,
        "POST",
        "/api/v1/devices/rpc",
        {"device": "r1", "device-group": "g1", "template": "t"},
    )

    assert status == 400


def test_apply_template(server):
    """
    Test that a configuration template is applied.
    """

    port, _ = server
    status, body = request(
        port,
        "POST",
        "/api/v1/devices/template?push=false",
        {"device-group": "g1", "template": "t", "inline": True},
    )

    assert status == 200
    assert body["applied"] is True
    assert called("apply_template")[0][1][1] == "g1"


def test_schemas(server):
    """
    Test that the schemas of the backend are listed.
    """

    port, _ = server
    status, body = request(port, "GET", "/api/v1/schemas")

    assert status == 200
    assert body == SCHEMAS


def test_yang(server):
    """
    Test that the YANG of a service module is served.
    """

    port, _ = server
    status, body = request(port, "GET", "/api/v1/yang/test-service")

    assert status == 200
    assert body.startswith("\nmodule test-service {")


def test_yang_other_module(server):
    """
    Test that a module which is not a service is fetched when asked for.
    """

    port, _ = server
    status, body = request(port, "GET", "/api/v1/yang/ietf-inet-types")

    assert status == 200
    assert "ip-address" in body


def test_yang_unknown(server):
    """
    Test that a module the backend does not have is a 404.
    """

    port, _ = server
    status, _ = request(port, "GET", "/api/v1/yang/nosuch")

    assert status == 404


def test_yang_invalid_name(server):
    """
    Test that a module name which is not a name is refused.
    """

    port, _ = server
    status, _ = request(port, "GET", "/api/v1/yang/not%20a%20name")

    assert status == 400


def test_openapi(server):
    """
    Test that the OpenAPI description is served.
    """

    port, _ = server
    status, body = request(port, "GET", "/api/v1/openapi.json")

    assert status == 200
    assert body["openapi"] == "3.0.3"
    assert "/services/test-service" in body["paths"]


def test_docs(server):
    """
    Test that the Swagger UI page is served.
    """

    port, _ = server
    status, body = request(port, "GET", "/api/v1/docs")

    assert status == 200
    assert "swagger-ui" in body
    assert "/api/v1/openapi.json" in body


def test_forwarded_prefix(server):
    """
    Test that the prefix NGINX forwards is used in the answers.
    """

    port, _ = server
    status, body = request(
        port, "GET", "/api/v1/", headers={"X-Forwarded-Prefix": "/controller/api"}
    )

    assert status == 200
    assert body["endpoints"]["docs"] == "/controller/api/docs"


def test_stripped_prefix(server):
    """
    Test that a request without the prefix is served as well, NGINX may have
    stripped it.
    """

    port, _ = server
    status, _ = request(port, "GET", "/services")

    assert status == 200


def test_forwarded_user(server):
    """
    Test that the user NGINX authenticated is used for the backend session.
    """

    port, _ = server
    request(
        port,
        "GET",
        "/api/v1/services/test-service",
        headers={"X-Remote-User": "alice"},
    )

    assert called("init")[0][2]["user"] == "alice"


def test_forwarded_user_sanitized(server):
    """
    Test that a user from the web server can not be anything at all.
    """

    port, _ = server
    request(
        port,
        "GET",
        "/api/v1/services/test-service",
        headers={"X-Remote-User": "alice; rm -rf /"},
    )

    assert called("init")[0][2]["user"] == "alicerm-rf"


def test_timeout_of_the_session(server):
    """
    Test that the timeout of a request reaches the backend session.
    """

    port, _ = server
    request(port, "GET", "/api/v1/devices?timeout=17")

    assert called("init")[0][2]["timeout"] == 17


def test_read_only(server):
    """
    Test that a read only server refuses the writes but serves the reads.
    """

    _, port = server

    assert request(port, "GET", "/api/v1/services")[0] == 200

    status, body = request(
        port, "POST", "/api/v1/services/test-service", {"service-name": "new"}
    )

    assert status == 403
    assert "read only" in body["error"]["message"]

    for method, path in [
        ("POST", "/api/v1/commit"),
        ("POST", "/api/v1/push"),
        ("POST", "/api/v1/rollback"),
        ("PATCH", "/api/v1/config"),
        ("DELETE", "/api/v1/services/test-service/test"),
    ]:
        assert request(port, method, path)[0] == 403


def test_backend_timeout(server):
    """
    Test that a backend which does not answer in time is a gateway timeout.
    """

    StubClixon.errors["show_devices"] = TimeoutException("timed out")

    port, _ = server
    status, body = request(port, "GET", "/api/v1/devices")

    assert status == 504
    assert "timed out" in body["error"]["message"]


def test_backend_error(server):
    """
    Test that an error from the backend is passed on to the client.
    """

    StubClixon.errors["show_compare"] = RPCError("backend says no")

    port, _ = server
    status, body = request(port, "GET", "/api/v1/compare")

    assert status == 400
    assert body["error"]["message"] == "backend says no"


def test_invalid_timeout(server):
    """
    Test that a timeout which is not a number of seconds is refused.
    """

    port, _ = server

    assert request(port, "GET", "/api/v1/devices?timeout=abc")[0] == 400
    assert request(port, "GET", "/api/v1/devices?timeout=0")[0] == 400
    assert request(port, "GET", "/api/v1/devices?timeout=99999")[0] == 400
    assert request(port, "GET", "/api/v1/devices?timeout=60")[0] == 200


def test_invalid_flag(server):
    """
    Test that a boolean parameter which is not a boolean is refused.
    """

    port, _ = server
    status, body = request(port, "POST", "/api/v1/commit?push=maybe")

    assert status == 400
    assert "true or false" in body["error"]["message"]


def test_unix_socket_server(stub, tmp_path):
    """
    Test that the server serves over a UNIX socket, which is what NGINX
    connects to.
    """

    path = str(tmp_path / "rest.sock")
    args = clixon_rest.parse_args(["-U", path])

    registry = clixon_rest.Registry(args.sockpath)
    registry.load()

    server = clixon_rest.create_server(args, registry)

    threading.Thread(target=server.serve_forever, daemon=True).start()

    try:
        connection = UnixHTTPConnection(path)
        connection.request("GET", "/api/v1/services")
        response = connection.getresponse()
        body = json.loads(response.read().decode())
        connection.close()

        assert response.status == 200
        assert body[0]["name"] == "test-service"
    finally:
        server.shutdown()
        server.server_close()


def test_unix_socket_replaces_a_stale_socket(stub, tmp_path):
    """
    Test that a socket left behind by an earlier run is replaced.
    """

    path = tmp_path / "stale.sock"
    path.write_text("not a socket")

    args = clixon_rest.parse_args(["-U", str(path)])
    registry = clixon_rest.Registry(args.sockpath)
    server = clixon_rest.UnixRestServer(str(path), args, registry)

    try:
        assert os.path.exists(path)
    finally:
        server.server_close()


def test_create_server_tcp(stub):
    """
    Test that a TCP server is created.
    """

    args = clixon_rest.parse_args(["-a", "127.0.0.1", "-p", "0"])
    server = clixon_rest.create_server(args, clixon_rest.Registry("/tmp/sock"))

    try:
        assert server.server_address[0] == "127.0.0.1"
    finally:
        server.server_close()


def test_registry_skips_what_it_can_not_use(stub):
    """
    Test that modules which are not services, or not YANG, are skipped.
    """

    schemas = [
        {"identifier": "ietf-inet-types", "format": "yang"},
        {"identifier": "clixon-controller", "format": "yang"},
        {"identifier": "test-service", "format": "yin"},
        {"identifier": "", "format": "yang"},
    ]

    with patch.object(StubClixon, "get_schemas", lambda self: schemas):
        registry = clixon_rest.Registry("/tmp/sock")

        assert registry.load() == {}


def test_registry_skips_a_module_it_can_not_fetch(stub):
    """
    Test that a module the backend does not hand out is skipped.
    """

    schemas = [{"identifier": "nosuch-module", "format": "yang"}]

    with patch.object(StubClixon, "get_schemas", lambda self: schemas):
        registry = clixon_rest.Registry("/tmp/sock")

        assert registry.load() == {}


def test_registry_skips_a_module_it_can_not_parse(stub):
    """
    Test that a module which does not parse is skipped.
    """

    schemas = [{"identifier": "broken", "format": "yang"}]
    broken = 'augment "/ctrl:services" { this is not yang'

    with patch.object(StubClixon, "get_schemas", lambda self: schemas), patch.object(
        StubClixon, "get_service_yang", lambda self, name, **kwargs: broken
    ):
        registry = clixon_rest.Registry("/tmp/sock")

        assert registry.load() == {}


def test_registry_unknown_service_reloads(stub):
    """
    Test that an unknown service reloads the YANG before giving up.
    """

    registry = clixon_rest.Registry("/tmp/sock")
    registry.load()

    with pytest.raises(clixon_rest.RestError) as error:
        registry.service("nosuch")

    assert error.value.status == 404
    assert registry.service("test-service").name == "test-service"


def test_connection_failure():
    """
    Test that a backend which can not be reached is a bad gateway.
    """

    def fail(**kwargs):
        raise OSError("no such socket")

    with patch.object(clixon_rest, "Clixon", fail):
        with pytest.raises(clixon_rest.RestError) as error:
            with clixon_rest.connect("/tmp/nosuch.sock"):
                pass

    assert error.value.status == 502


def test_connection_closes_quietly():
    """
    Test that a session which can not be closed is not an error.
    """

    class Failing(StubClixon):
        def close_session(self):
            raise OSError("gone")

    with patch.object(clixon_rest, "Clixon", Failing):
        with clixon_rest.connect("/tmp/test.sock") as clx:
            assert clx is not None


def test_get_sockpath(tmp_path):
    """
    Test that the socket path is read from a clixon configuration file.
    """

    config = tmp_path / "controller.xml"
    config.write_text(
        '<clixon-config xmlns="http://clicon.org/config">'
        "<CLICON_SOCK>/test/sock</CLICON_SOCK></clixon-config>"
    )

    assert clixon_rest.get_sockpath(str(config)) == "/test/sock"
    assert clixon_rest.parse_args(["-f", str(config)]).sockpath == "/test/sock"


def test_get_sockpath_broken(tmp_path, capsys):
    """
    Test that a configuration file without a socket stops the program.
    """

    config = tmp_path / "broken.xml"
    config.write_text("<clixon-config/>")

    with pytest.raises(SystemExit):
        clixon_rest.get_sockpath(str(config))

    assert "Could not parse" in capsys.readouterr().out


def test_init_args():
    """
    Test that the arguments are handed over to the clixon package.
    """

    args = clixon_rest.init_args(["-s", "/test/sock", "-d", "-l", "s"])

    assert args.sockpath == "/test/sock"
    assert clixon.args.global_args["sockpath"] == "/test/sock"
    assert clixon.args.global_args["debug"] is True
    assert clixon.args.global_args["configfile"] is None

    clixon_rest.init_args([])


def test_main_without_socket(stub, capsys):
    """
    Test that a missing clixon socket stops the program.
    """

    args = clixon_rest.parse_args(["-s", "/nosuch/socket"])

    with patch.object(clixon_rest, "ARGS", args):
        with pytest.raises(SystemExit):
            clixon_rest.main()


def test_main_version(capsys):
    """
    Test that the version is printed.
    """

    args = clixon_rest.parse_args([])
    args.version = True

    with patch.object(clixon_rest, "ARGS", args):
        with pytest.raises(SystemExit):
            clixon_rest.main()

    assert capsys.readouterr().out.strip() == clixon_rest.__version__


def test_main_backend_down(stub, tmp_path):
    """
    Test that a backend which is down stops the program.
    """

    sock = tmp_path / "clixon.sock"
    sock.write_text("")

    args = clixon_rest.parse_args(["-s", str(sock)])

    def fail(**kwargs):
        raise OSError("backend is down")

    with patch.object(clixon_rest, "ARGS", args), patch.object(
        clixon_rest, "Clixon", fail
    ):
        with pytest.raises(SystemExit):
            clixon_rest.main()


def test_main_serves_and_stops(stub, tmp_path):
    """
    Test that the program loads the YANG, serves and shuts down.
    """

    sock = tmp_path / "clixon.sock"
    sock.write_text("")

    args = clixon_rest.parse_args(["-s", str(sock), "-p", "0"])
    served = []

    class FakeServer:
        def serve_forever(self):
            served.append(True)

            raise KeyboardInterrupt()

        def server_close(self):
            served.append("closed")

    with patch.object(clixon_rest, "ARGS", args), patch.object(
        clixon_rest, "create_server", return_value=FakeServer()
    ):
        clixon_rest.main()

    assert served == [True, "closed"]
