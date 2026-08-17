from http import HTTPStatus

import pytest

import clixon_rest

from clixon import yang
from clixon.exceptions import RPCError
from clixon.parser import parse_string
from tests.test_yang import MODULE, loader


def service():
    """
    Return the test service.
    """

    context = yang.Context(loader=loader)
    module = context.add(MODULE)
    node = yang.service_nodes(context, module)[0]

    return clixon_rest.Service(node, module)


INSTANCE = {
    "service-name": "test",
    "enabled": False,
    "load": 42,
    "mode": "fast",
    "tag": ["a", "b"],
    "limits": {"max": 10},
    "peer": [{"name": "p1", "address": "1.2.3.4", "port": 830}],
}


def test_service():
    """
    Test that a service is described by its YANG.
    """

    svc = service()

    assert svc.name == "test-service"
    assert svc.keys == ["service-name"]
    assert svc.module == "test-service"
    assert svc.namespace == "http://clicon.org/test-service"
    assert svc.revision == "2024-01-01"
    assert svc.description == "A test service"


def test_xpath():
    """
    Test that the xpath of a service and of an instance are built.
    """

    svc = service()

    assert svc.xpath() == "/ctrl:services/svc:test-service"
    assert svc.xpath("foo") == "/ctrl:services/svc:test-service[svc:service-name='foo']"


def test_key_values():
    """
    Test that invalid instance keys are rejected.
    """

    svc = service()

    assert svc.key_values("foo%20bar") == ["foo bar"]

    with pytest.raises(clixon_rest.RestError):
        svc.key_values("foo,bar")

    with pytest.raises(clixon_rest.RestError):
        svc.key_values("foo'bar")


def test_instance_element():
    """
    Test that an instance is rendered as an edit-config body.
    """

    svc = service()
    root = clixon_rest.instance_element(svc, INSTANCE, operation="create")

    xmlstr = (
        '<services xmlns="http://clicon.org/controller">'
        '<test-service xmlns="http://clicon.org/test-service" nc:operation="create">'
        "<service-name>test</service-name>"
        "<enabled>false</enabled>"
        "<load>42</load>"
        "<mode>fast</mode>"
        "<tag>a</tag><tag>b</tag>"
        "<limits><max>10</max></limits>"
        "<peer><name>p1</name><address>1.2.3.4</address><port>830</port></peer>"
        "</test-service></services>"
    )

    assert root.dumps() == xmlstr


def test_instance_element_delete():
    """
    Test that a delete only holds the keys.
    """

    svc = service()
    root = clixon_rest.instance_element(
        svc, {"service-name": "test"}, operation="delete"
    )

    assert 'nc:operation="delete"' in root.dumps()
    assert "<service-name>test</service-name>" in root.dumps()


def test_instance_element_escapes():
    """
    Test that values are escaped.
    """

    svc = service()
    root = clixon_rest.instance_element(svc, {"service-name": "a<b&c"})

    assert "<service-name>a&lt;b&amp;c</service-name>" in root.dumps()


def test_instance_element_errors():
    """
    Test that invalid bodies are rejected.
    """

    svc = service()

    with pytest.raises(clixon_rest.RestError):
        clixon_rest.instance_element(svc, {"nosuch": "field"})

    with pytest.raises(clixon_rest.RestError):
        clixon_rest.instance_element(svc, {"enabled": True})

    with pytest.raises(clixon_rest.RestError):
        clixon_rest.instance_element(svc, {"service-name": "test", "tag": "a"})

    with pytest.raises(clixon_rest.RestError):
        clixon_rest.instance_element(
            svc, {"service-name": "test", "limits": {"max": 1, "nosuch": 2}}
        )


def test_element_to_json():
    """
    Test that an instance read from the backend is converted to JSON.
    """

    svc = service()
    xmlstr = (
        '<services xmlns="http://clicon.org/controller">'
        '<test-service xmlns="http://clicon.org/test-service">'
        "<service-name>test</service-name>"
        "<enabled>false</enabled>"
        "<load>42</load>"
        "<tag>a</tag><tag>b</tag>"
        "<limits><max>10</max></limits>"
        "<peer><name>p1</name><port>830</port></peer>"
        "<nosuchleaf>dropped</nosuchleaf>"
        "</test-service></services>"
    )

    element = parse_string(xmlstr).services.get_elements("test-service")[0]

    assert clixon_rest.element_to_json(svc.node, element) == {
        "service-name": "test",
        "enabled": False,
        "load": 42,
        "tag": ["a", "b"],
        "limits": {"max": 10},
        "peer": [{"name": "p1", "port": 830}],
    }


def test_element_to_json_unescapes():
    """
    Test that escaped values are unescaped.
    """

    svc = service()
    xmlstr = (
        '<test-service xmlns="http://clicon.org/test-service">'
        "<service-name>a&lt;b&amp;c</service-name>"
        "</test-service>"
    )

    element = parse_string(xmlstr).get_elements("test-service")[0]

    assert clixon_rest.element_to_json(svc.node, element) == {"service-name": "a<b&c"}


def test_json_roundtrip():
    """
    Test that an instance survives a round trip through XML.
    """

    svc = service()
    root = clixon_rest.instance_element(svc, INSTANCE)
    element = parse_string(root.dumps()).services.get_elements("test-service")[0]

    assert clixon_rest.element_to_json(svc.node, element) == INSTANCE


def test_openapi_schema():
    """
    Test that the OpenAPI schema of a service is rendered from its YANG.
    """

    schema = clixon_rest.openapi_schema(service().node)
    properties = schema["properties"]

    assert schema["required"] == ["service-name"]
    assert properties["service-name"]["type"] == "string"
    assert properties["enabled"] == {
        "type": "boolean",
        "default": True,
        "x-yang-type": "boolean",
    }
    assert properties["load"]["type"] == "integer"
    assert properties["mode"]["enum"] == ["fast", "slow"]
    assert properties["tag"] == {
        "type": "array",
        "items": {"type": "string", "x-yang-type": "string"},
    }
    assert properties["limits"]["properties"]["max"]["format"] == "int32"
    assert properties["peer"]["items"]["required"] == ["name"]
    assert "created" in properties


def test_openapi_request_schema():
    """
    Test that hidden nodes are left out of the request schema.
    """

    schema = clixon_rest.openapi_schema(service().node, writable=True)

    assert "created" not in schema["properties"]
    assert "service-name" in schema["properties"]


def test_openapi():
    """
    Test that the OpenAPI description holds the paths of a service.
    """

    svc = service()
    spec = clixon_rest.openapi({svc.name: svc}, "/api/v1", "/tmp/sock")

    assert spec["openapi"] == "3.0.3"
    assert spec["servers"] == [{"url": "/api/v1"}]

    paths = spec["paths"]

    assert sorted(paths["/services/test-service"]) == ["get", "post"]
    assert sorted(paths["/services/test-service/{service-name}"]) == [
        "delete",
        "get",
        "patch",
        "put",
    ]

    operation = paths["/services/test-service/{service-name}"]["put"]

    assert operation["parameters"][0]["name"] == "service-name"
    assert [p["name"] for p in operation["parameters"][1:]] == [
        "commit",
        "push",
        "lock",
        "timeout",
    ]
    assert (
        operation["requestBody"]["content"]["application/json"]["schema"]["$ref"]
        == "#/components/schemas/test-service.request"
    )

    assert "test-service" in spec["components"]["schemas"]
    assert "test-service.request" in spec["components"]["schemas"]


def test_openapi_without_services():
    """
    Test that the controller resources are described even without services.
    """

    spec = clixon_rest.openapi({}, "/api/v1", "/tmp/sock")

    assert "/health" in spec["paths"]
    assert "/devices" in spec["paths"]
    assert [p for p in spec["paths"] if p.startswith("/services/")] == []
    assert spec["components"]["schemas"] == {}


def test_parse_args():
    """
    Test that the arguments of the server are parsed.
    """

    args = clixon_rest.parse_args([])

    assert args.sockpath == clixon_rest.DEFAULT_SOCKPATH
    assert args.port == clixon_rest.DEFAULT_PORT
    assert args.prefix == clixon_rest.DEFAULT_PREFIX
    assert args.read_only is False

    args = clixon_rest.parse_args(
        ["-s", "/tmp/sock", "-p", "9000", "-x", "/services", "-r"]
    )

    assert args.sockpath == "/tmp/sock"
    assert args.port == 9000
    assert args.prefix == "/services"
    assert args.read_only is True


DEVICES = (
    '<rpc-reply xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"><data>'
    '<devices xmlns="http://clicon.org/controller">'
    "<device><name>r1</name><conn-state>OPEN</conn-state>"
    "<logmsg>a &lt; b</logmsg></device>"
    "<device><name>r2</name><conn-state>CLOSED</conn-state></device>"
    "</devices></data></rpc-reply>"
)


def test_elements_to_json():
    """
    Test that the state elements of a reply are converted to JSON.
    """

    assert clixon_rest.elements_to_json(DEVICES, "device") == [
        {"name": "r1", "conn-state": "OPEN", "logmsg": "a < b"},
        {"name": "r2", "conn-state": "CLOSED"},
    ]
    assert clixon_rest.elements_to_json(DEVICES, "nosuch") == []


def test_elements_to_json_nested():
    """
    Test that a nested element is kept as an object.
    """

    xmlstr = (
        "<data><transaction><tid>1</tid>"
        "<devices><device>r1</device></devices></transaction></data>"
    )

    assert clixon_rest.elements_to_json(xmlstr, "transaction") == [
        {"tid": "1", "devices": {"device": "r1"}}
    ]


def test_element_to_dict():
    """
    Test that an element of an unknown schema is converted to JSON.
    """

    element = parse_string("<data><a><b>1</b></a></data>").data

    assert clixon_rest.element_to_dict(element) == {"a": {"b": "1"}}
    assert clixon_rest.element_to_dict(parse_string("<data/>").data) is None
    assert clixon_rest.element_to_dict(None) is None


class FakeClixon:
    """
    Clixon object recording the locks it is asked for.
    """

    def __init__(self, fail=False):
        self.calls = []
        self.fail = fail

    def lock(self, target):
        if self.fail:
            raise RPCError("locked by someone else")

        self.calls.append(("lock", target))

    def unlock(self, target):
        self.calls.append(("unlock", target))


def test_locked():
    """
    Test that the candidate datastore is locked and unlocked.
    """

    clx = FakeClixon()

    with clixon_rest.Locked(clx, True):
        assert clx.calls == [("lock", "candidate")]

    assert clx.calls == [("lock", "candidate"), ("unlock", "candidate")]


def test_locked_disabled():
    """
    Test that nothing is locked unless it is asked for.
    """

    clx = FakeClixon()

    with clixon_rest.Locked(clx, False):
        pass

    assert clx.calls == []


def test_locked_conflict():
    """
    Test that a datastore which is already locked is a conflict.
    """

    with pytest.raises(clixon_rest.RestError) as error:
        with clixon_rest.Locked(FakeClixon(fail=True), True):
            pass

    assert error.value.status == HTTPStatus.CONFLICT


def test_openapi_controller_paths():
    """
    Test that the Python API is described, not only the services.
    """

    svc = service()
    spec = clixon_rest.openapi({svc.name: svc}, "/api/v1", "/tmp/sock")
    paths = spec["paths"]

    assert sorted(p for p in paths if not p.startswith("/services/")) == [
        "/commit",
        "/compare",
        "/config",
        "/devices",
        "/devices/connect",
        "/devices/diff",
        "/devices/pull",
        "/devices/rpc",
        "/devices/template",
        "/health",
        "/push",
        "/rollback",
        "/schemas",
        "/services",
        "/transactions",
        "/transactions/{tid}",
        "/yang/{module}",
    ]

    assert sorted(paths["/config"]) == ["get", "patch"]
    assert "/services/test-service/{service-name}/apply" in paths
    assert {t["name"] for t in spec["tags"]} == {
        "controller",
        "devices",
        "test-service",
    }


def test_openapi_write_parameters():
    """
    Test that the write operations take the datastore parameters.
    """

    svc = service()
    spec = clixon_rest.openapi({svc.name: svc}, "/api/v1", "/tmp/sock")

    for path, method in [
        ("/config", "patch"),
        ("/devices/template", "post"),
        ("/services/test-service", "post"),
    ]:
        names = [p["name"] for p in spec["paths"][path][method]["parameters"]]

        assert names[-4:] == ["commit", "push", "lock", "timeout"]


def test_openapi_template_body():
    """
    Test that the template operations describe their body.
    """

    body = clixon_rest.openapi_template_body()
    schema = body["content"]["application/json"]["schema"]

    assert schema["required"] == ["template"]
    assert sorted(schema["properties"]) == [
        "device",
        "device-group",
        "inline",
        "template",
        "variables",
    ]


def test_parse_args_timeout():
    """
    Test that the timeout of the backend sessions is parsed.
    """

    assert clixon_rest.parse_args([]).timeout == clixon_rest.DEFAULT_TIMEOUT
    assert clixon_rest.parse_args(["-t", "120"]).timeout == 120
