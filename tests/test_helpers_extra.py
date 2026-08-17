import time

import pytest

from clixon.exceptions import TimeoutException
from clixon.helpers import (
    get_device,
    get_devices,
    get_devices_configuration,
    get_devices_from_group,
    get_junos_interface_address,
    get_openconfig_interface_address,
    get_path,
    get_properties,
    get_service_instance,
    get_service_instances,
    get_value,
    is_juniper,
    timeout,
)
from clixon.parser import parse_string

JUNIPER = """
<devices xmlns="http://clicon.org/controller">
<device><name>r1</name><config>
<configuration xmlns="http://yang.juniper.net/junos/conf/root">
<interfaces><interface><name>lo0</name>
<unit><name>0</name><family>
<inet><address><name>1.1.1.1/32</name><primary/></address>
<address><name>1.1.1.2/32</name></address></inet>
<inet6><address><name>dead::1/64</name><primary/></address></inet6>
</family></unit></interface></interfaces>
</configuration></config></device>
<device><name>r2</name><config><configuration
xmlns="http://openconfig.net/yang/root"/></config></device>
<device-group><name>group1</name><device-name>r1</device-name>
<device-name>r2</device-name></device-group>
</devices>
"""

EMPTY = "<nothing/>"


def juniper():
    """
    Return a parsed configuration with one Juniper device.
    """

    return parse_string(JUNIPER)


def empty():
    """
    Return a configuration without devices or services.
    """

    return parse_string(EMPTY)


def test_timeout_expires():
    """
    Test that the timeout decorator interrupts a function.
    """

    @timeout(1)
    def sleeper():
        time.sleep(3)

    with pytest.raises(TimeoutException):
        sleeper()


def test_timeout_returns():
    """
    Test that the timeout decorator returns the value of the function.
    """

    @timeout(5)
    def quick():
        return "done"

    assert quick() == "done"


def test_get_devices():
    """
    Test that the devices are returned.
    """

    assert [str(d.name) for d in get_devices(juniper())] == ["r1", "r2"]
    assert list(get_devices(empty())) == []


def test_get_device():
    """
    Test that one device is returned.
    """

    assert str(get_device(juniper(), "r1").name) == "r1"
    assert get_device(juniper(), "nosuch") is None
    assert get_device(empty(), "r1") is None


def test_get_devices_configuration():
    """
    Test that the configuration of a device is returned.
    """

    config = get_devices_configuration(juniper(), "r1")

    assert config.configuration is not None
    assert get_devices_configuration(empty(), "r1") is None


def test_get_devices_from_group():
    """
    Test that the devices of a group are returned.
    """

    devices = get_devices_from_group(juniper(), "group1")

    assert [str(d) for d in devices] == ["r1", "r2"]
    assert get_devices_from_group(juniper(), "nosuch") == []
    assert get_devices_from_group(empty(), "group1") == []


def test_is_juniper():
    """
    Test that a Juniper device is recognized.
    """

    root = juniper()

    assert is_juniper(get_device(root, "r1")) is True
    assert is_juniper(get_device(root, "r2")) is False
    assert is_juniper(empty()) is False


SINGLE = """
<devices xmlns="http://clicon.org/controller">
<device><name>r1</name><config>
<configuration xmlns="http://yang.juniper.net/junos/conf/root">
<interfaces><interface><name>lo0</name>
<unit><name>0</name><family>
<inet><address><name>1.1.1.1/32</name></address></inet>
<inet6><address><name>dead::1/64</name></address></inet6>
</family></unit></interface></interfaces>
</configuration></config></device></devices>
"""


def test_get_openconfig_interface_address():
    """
    Test that the address of an interface is returned.
    """

    root = parse_string(SINGLE)

    assert get_openconfig_interface_address(root, "lo0", "0", "r1") == "1.1.1.1/32"
    assert (
        get_openconfig_interface_address(root, "lo0", "0", "r1", family="inet")
        == "1.1.1.1/32"
    )
    assert (
        get_openconfig_interface_address(root, "lo0", "0", "r1", family="inet6")
        == "dead::1/64"
    )
    assert get_openconfig_interface_address(root, "lo0", "0", "") == "1.1.1.1/32"


def test_get_openconfig_interface_address_missing():
    """
    Test that an interface which is not there gives an empty address.
    """

    root = juniper()

    assert get_openconfig_interface_address(root, "lo1", "0", "r1") == ""
    assert get_openconfig_interface_address(root, "lo0", "1", "r1") == ""
    assert get_openconfig_interface_address(root, "lo0", "0", "nosuch") == ""
    assert get_openconfig_interface_address(empty(), "lo0", "0", "r1") == ""


def test_get_junos_interface_address():
    """
    Test that the addresses of a Junos interface are returned.
    """

    root = juniper()

    assert get_junos_interface_address(root, "r1", "lo0", "0") == ["1.1.1.1/32"]
    assert get_junos_interface_address(root, "r1", "lo0", "0", primary=False) == [
        "1.1.1.1/32",
        "1.1.1.2/32",
    ]
    assert get_junos_interface_address(root, "r1", "lo0", "0", family="inet6") == [
        "dead::1/64"
    ]


def test_get_junos_interface_address_missing():
    """
    Test that an unknown interface or family gives nothing.
    """

    root = juniper()

    assert get_junos_interface_address(root, "r1", "lo1", "0") is None
    assert get_junos_interface_address(root, "r1", "lo0", "0", family="foo") is None
    assert get_junos_interface_address(empty(), "r1", "lo0", "0") is None


def test_get_properties():
    """
    Test that the properties of a service are returned.
    """

    root = parse_string(
        "<services><properties><bgp><as_number>65000</as_number>"
        "</bgp></properties></services>"
    )

    assert get_properties(root, "bgp") == {
        "as_number": "65000",
        "as-number": "65000",
    }
    assert get_properties(empty(), "bgp") is None


def test_get_service_instance():
    """
    Test that a service instance is found by its name.
    """

    root = parse_string(
        "<services><ssh-users><service-name>test</service-name>"
        "</ssh-users><ssh-users><service-name>other</service-name>"
        "</ssh-users></services>"
    )

    instance = get_service_instance(root, "ssh-users", instance="other")

    assert str(instance.service_name) == "other"
    assert get_service_instance(root, "ssh-users", instance="nosuch") is None
    assert get_service_instance(root, "ssh-users") is None
    assert get_service_instance(empty(), "ssh-users", instance="test") is None


def test_get_service_instances():
    """
    Test that the instances of a service are returned.
    """

    root = parse_string(
        "<services><ssh-users><service-name>test</service-name>"
        "</ssh-users></services>"
    )

    assert len(get_service_instances(root, "ssh-users")) == 1
    assert get_service_instances(empty(), "ssh-users") == []


def test_get_value_required():
    """
    Test that a missing required value is an error.
    """

    element = parse_string("<device><name>r1</name></device>").device

    assert get_value(element, "name") == "r1"
    assert get_value(element, "nosuch") is None
    assert get_value(element, "nosuch", default="fallback") == "fallback"

    with pytest.raises(Exception):
        get_value(element, "nosuch", required=True)


def test_get_path_missing():
    """
    Test that a path which does not lead anywhere gives nothing.
    """

    root = juniper()

    assert get_path(root, "/devices/device[name='nosuch']") is None
    assert get_path(root, "/nosuch") is None
    assert get_path(root, "/devices/device[0]") is not None
