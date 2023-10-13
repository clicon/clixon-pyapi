from clixon.clixon import Clixon
from clixon.args import get_logger
from clixon.element import Element
from typing import List, Optional, Iterable

log = get_logger()


def get_service_instance(root, service_name, kwargs):
    if "instance" not in kwargs:
        return None

    try:
        services = root.services.get_elements(service_name)

        for service in services:
            if str(service.service_name) == kwargs["instance"]:
                return service
    except AttributeError:
        log.debug("No service with name %s", service_name)
        return None

    return None


def get_devices_from_group(root: Element, device_group_name: str) -> List[str]:
    """Returns a list of devices in a device group."""
    devices = []

    try:
        device_groups = root.devices.device_group
        for group in device_groups:
            if group.name != device_group_name:
                continue
            return group.device_name
    except AttributeError:
        log.debug("No device group with name %s", device_group_name)
        devices = []

    return devices


def get_openconfig_interface_address(root: Element, interface_name: str,
                                     interface_unit: str,
                                     device_name: str,
                                     family: Optional[str] = "") -> str:
    """Returns the IP address of an interface."""
    address = ""

    try:
        for device in root.devices.device:
            if device_name != "" and device_name != device.name:
                continue
            for interface in device.config.configuration.interfaces.interface:
                if interface.name != interface_name:
                    continue
                for unit in interface.unit:
                    if str(unit.name) != str(interface_unit):
                        continue
                    if family == "" or family == "inet":
                        address = unit.family.inet.address.name
                    elif family == "inet6":
                        address = unit.family.inet6.address.name
    except AttributeError:
        log.debug("No interface with name %s", interface_name)
        return ""

    return str(address)


def get_devices(root: Element) -> Iterable[Element]:
    """ Returns an iterable of devices. """
    try:
        for device in root.devices.device:
            yield device
    except AttributeError:
        log.debug("No devices")
        return None


def get_devices_configuration(root: Element,
                              name: Optional[str] = "") -> Iterable[Element]:
    """ Returns an iterable of devices configuration. """
    try:
        for device in root.devices.device:
            if name != "" and name != device.name:
                continue

            yield device.config
    except AttributeError:
        log.debug("No devices or missing config element")
        return None
