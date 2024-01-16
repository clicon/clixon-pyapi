import re
from clixon.element import Element
from typing import List, Optional, Iterable


def get_service_instance(root, service_name, **kwargs):
    """
    Returns the service instance.
    """
    if "instance" not in kwargs:
        return None

    try:
        services = root.services.get_elements(service_name)

        for service in services:
            if str(service.service_name) == kwargs["instance"]:
                return service
    except AttributeError:
        return None

    return None


def get_devices_from_group(root: Element, device_group_name: str) -> List[str]:
    """
    Returns a list of devices in a device group.
    """
    devices = []

    try:
        device_groups = root.devices.device_group
        for group in device_groups:
            if group.name != device_group_name:
                continue
            return group.device_name
    except AttributeError:
        devices = []

    return devices


def get_openconfig_interface_address(root: Element, interface_name: str,
                                     interface_unit: str,
                                     device_name: str,
                                     family: Optional[str] = "") -> str:
    """
    Returns the IP address of an interface.
    """
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
        return ""

    return str(address)


def get_devices(root: Element) -> Iterable[Element]:
    """
    Returns an iterable of devices.
    """
    try:
        for device in root.devices.device:
            yield device
    except AttributeError:
        return None


def get_device(root: Element, name: str) -> Element:
    """
    Returns a device.
    """
    try:
        for device in root.devices.device:
            if name == str(device.name):
                return device
    except AttributeError:
        return None

    return None


def get_devices_configuration(root: Element,
                              name: Optional[str] = "") -> Iterable[Element]:
    """
    Returns an iterable of devices configuration.
    """
    try:
        for device in root.devices.device:
            if name != "" and name != device.name:
                continue

            return device.config
    except AttributeError:
        return None


def get_properties(root: Element, name: str) -> dict:
    """
    Returns a dict of the property values.
    """
    properties = {}

    try:
        for prop in root.services.properties.get_elements(name):
            for item in prop.get_elements():
                name = item.get_name()
                properties[name] = str(item)

                name = name.replace("_", "-")
                properties[name] = str(item)

    except AttributeError:
        return None

    return properties


def is_juniper(device: Element) -> bool:
    """
    Returns True if the device is a Juniper device.
    """
    try:
        if device.config.configuration.get_attributes("xmlns") == \
           "http://yang.juniper.net/junos/conf/root":
            return True
    except AttributeError:
        return False

    return False


def get_path(root: Element, path: str) -> Optional[Element]:
    """
    Returns the element at the path. Porr mans xpath.

    Examples:
        get_path(root, "devices/device[0]")
        get_path(root, "devices/device[name='r1']/config")
        get_path(root, "services/bgp-peer[name='bgp-test']")
    """
    if path.startswith("/"):
        path = path[1:]

    new_root = None

    for node in path.split("/"):
        index = None
        parameter = None
        value = None

        arg = re.search(r'\[(.*?)\]', node)

        if arg:
            if arg.group(1).isdigit():
                index = int(arg.group(1))
                node = node.replace(f"[{index}]", "")

            else:
                match = re.match(r"(\S+)='(\S+)'", arg.group(1))

                try:
                    parameter = match.group(1)
                    parameter = parameter.replace("-", "_")
                    value = match.group(2)

                    node = node.replace(
                        f"[{match.group(1)}='{match.group(2)}']", "")
                    node = node.replace("-", "_")

                except AttributeError:
                    return None

        node = node.replace("-", "_")

        try:
            if not new_root:
                new_root = getattr(root, node)
            else:
                new_root = getattr(new_root, node)
        except AttributeError:
            return None

        if not isinstance(new_root, list):
            if parameter and value:
                if getattr(new_root, parameter) != value:
                    return None
            if index is not None and index != 0:
                try:
                    new_root = new_root[index]
                except IndexError:
                    return None

            continue
        else:
            if index is not None:
                try:
                    new_root = new_root[index]
                except IndexError:
                    return None

        if parameter and value:
            for item in new_root:
                param_node = getattr(item, parameter)
                if str(param_node) == value:
                    new_root = item
                    break
            else:
                return None

    new_root.clixon_path = path

    return new_root


def get_value(element: Element, val: str, required: Optional[bool] = False,
              default: Optional[str] = "") -> str:
    """
    Returns the value of an element.

    Examples:
        device_name = get_value(device, "name", required=True)
        device_name = get_value(exchange_point, "md5-sum", required=False)
    """
    if element.get_elements(val) == []:
        if required:
            raise Exception(f"Value {val} must be configured")

        if default != "":
            return default

        return None

    return str(element.get_elements(val)[0])


def get_service_instances(root, service_name):
    """
    Returns a list of service instances.
    """
    instances = []
    services = get_path(root, f"/services/{service_name}")

    if not services:
        return instances

    for service in services:
        instances.append(service)

    return instances


def set_creator_attributes(root: Element, service_name: str,
                           instance_name: Optional[str] = "",
                           operation: Optional[str] = "create",
                           *args, **kwargs):
    """
    Sets the creator attributes.
    """

    if "instance_name" in kwargs:
        instance_name = kwargs["instance_name"]

    if isinstance(instance_name, dict):
        instance_name = instance_name["instance_name"]

    creator_attr = {
        "cl:creator": f"{service_name}[service-name='{instance_name}']",
        "nc:operation": operation,
        "xmlns:cl": "http://clicon.org/lib"
    }

    if not isinstance(root, Element):
        raise Exception("Root must be an Element")

    root.update_attributes(creator_attr)
