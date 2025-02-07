import re
import signal

from clixon.element import Element
from clixon.exceptions import TimeoutException
from typing import Iterable
from typing import List
from typing import Optional


def timeout(seconds=10):
    def decorator(func):
        def __handle_timeout__(signum, frame):
            raise TimeoutException(
                "%s timed out after %d seconds" % (func.__name__, seconds)
            )

        def wrapper(*args, **kwargs):
            signal.signal(signal.SIGALRM, __handle_timeout__)
            signal.alarm(seconds)

            try:
                ret = func(*args, **kwargs)
            finally:
                signal.alarm(0)

            return ret

        return wrapper

    return decorator


def get_service_instance(root: Element, service_name: str, **kwargs: dict) -> Element:
    """
    Returns the service instance.

    :param root: Root element
    :type root: Element
    :param service_name: Service name
    :type service_name: str
    :param kwargs: Keyword arguments
    :type kwargs: dict
    :return: Service instance
    :rtype: Element
    """
    if "instance" not in kwargs:
        return None

    try:
        services = root.services.get_elements(service_name)

        for service in services:
            if service.get_elements("service-name"):
                if str(service.service_name) == kwargs["instance"]:
                    return service
            elif service.get_elements("instance"):
                if str(service.instance) == kwargs["instance"]:
                    return service
            else:
                continue
    except AttributeError:
        return None

    return None


def get_devices_from_group(root: Element, device_group_name: str) -> List[str]:
    """
    Returns a list of devices in a device group.

    :param root: Root element
    :type root: Element
    :param device_group_name: Device group name
    :type device_group_name: str
    :return: List of devices
    :rtype: List[str]
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


def get_openconfig_interface_address(
    root: Element,
    interface_name: str,
    interface_unit: str,
    device_name: str,
    family: Optional[str] = "",
) -> str:
    """
    Returns the IP address of an interface.

    :param root: Root element
    :type root: Element
    :param interface_name: Interface name
    :type interface_name: str
    :param interface_unit: Interface unit
    :type interface_unit: str
    :param device_name: Device name
    :type device_name: str
    :param family: Address family
    :type family: str
    :return: IP address
    :rtype: str
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

    :param root: Root element
    :type root: Element
    :return: Iterable of devices
    :rtype: Iterable[Element]
    """
    try:
        for device in root.devices.device:
            yield device
    except AttributeError:
        return None


def get_device(root: Element, name: str) -> Element:
    """
    Returns a device.

    :param root: Root element
    :type root: Element
    :param name: Device name
    :type name: str
    :return: Device
    :rtype: Element
    """
    try:
        for device in root.devices.device:
            if name == str(device.name):
                return device
    except AttributeError:
        return None

    return None


def get_devices_configuration(
    root: Element, name: Optional[str] = ""
) -> Iterable[Element]:
    """
    Returns an iterable of devices configuration.

    :param root: Root element
    :type root: Element
    :param name: Device name
    :type name: str
    :return: Iterable of devices configuration
    :rtype: Iterable[Element]
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

    :param root: Root element
    :type root: Element
    :param name: Property name
    :type name: str
    :return: Dict of property values
    :rtype: dict
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

    :param device: Device
    :type device: Element
    :return: True if the device is a Juniper device
    :rtype: bool
    """
    try:
        if (
            device.config.configuration.get_attributes("xmlns")
            == "http://yang.juniper.net/junos/conf/root"
        ):
            return True
    except AttributeError:
        return False

    return False


def get_path(root: Element, path: str) -> Optional[Element]:
    """
    Returns the element at the path. Poor mans xpath.

    Examples:
        get_path(root, "devices/device[0]")
        get_path(root, "devices/device[name='r1']/config")
        get_path(root, "services/bgp-peer[name='bgp-test']")

    :param root: Root element
    :type root: Element
    :param path: Path
    :type path: str
    :return: Element
    :rtype: Element

    """
    if path.startswith("/"):
        path = path[1:]

    # Replace any [key="value"] with [key='value']
    path = re.sub(r'(\[.*?)"(.*?)"', r"\1'\2'", path)
    node_re = r"([^\/\[\]]+|\[[^\]]+\])+"

    new_root = None
    nodes = re.finditer(node_re, path)

    for m in nodes:
        node = m.group()
        index = None
        parameter = None
        value = None

        arg = re.search(r"\[(.*?)\]", node)

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
                    node = node.replace(f"[{match.group(1)}='{match.group(2)}']", "")
                    node = node.replace("-", "_")

                except AttributeError:
                    return None

        node = node.replace("-", "_")

        try:
            if new_root is None:
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

    return new_root


def get_value(
    element: Element,
    val: str,
    required: Optional[bool] = False,
    default: Optional[str] = "",
) -> str:
    """
    Returns the value of an element.

    Examples:
        device_name = get_value(device, "name", required=True)
        device_name = get_value(exchange_point, "md5-sum", required=False)

    :param element: Element
    :type element: Element
    :param val: Value
    :type val: str
    :param required: If the value is required
    :type required: bool
    :param default: Default value
    :type default: str
    :return: Value
    :rtype: str
    """
    if element.get_elements(val) == []:
        if required:
            raise Exception(f"Value {val} must be configured")

        if default != "":
            return default

        return None

    return str(element.get_elements(val)[0])


def get_data(
    element: Element,
    val: str,
    required: Optional[bool] = False,
    default: Optional[str] = "",
) -> str:
    return get_value(element, val, required, default)


def get_service_instances(root: Element, service_name: str) -> List[Element]:
    """
    Returns a list of service instances.

    :param root: Root element
    :type root: Element
    :param service_name: Service name
    :type service_name: str
    :return: List of service instances
    :rtype: List[Element]
    """
    instances = []
    services = get_path(root, f"/services/{service_name}")

    if not services:
        return instances

    for service in services:
        instances.append(service)

    return instances


def set_creator_attributes(
    root: Element,
    service_name: str,
    instance_name: Optional[str] = "",
    operation: Optional[str] = "create",
    *args,
    **kwargs,
):
    """
    Sets the creator attributes.

    :param root: Root element
    :type root: Element
    :param service_name: Service name
    :type service_name: str
    :param instance_name: Instance name
    :type instance_name: str
    :param operation: Operation
    :type operation: str
    :param args: Arguments
    :type args: list
    :param kwargs: Keyword arguments
    :type kwargs: dict
    :return: None
    :rtype: None
    """

    if "instance_name" in kwargs:
        instance_name = kwargs["instance_name"]

    if isinstance(instance_name, dict):
        instance_name = instance_name["instance_name"]

    creator_attr = {
        "cl:creator": f"{service_name}[service-name='{instance_name}']",
        "nc:operation": operation,
        "xmlns:cl": "http://clicon.org/lib",
    }

    if not isinstance(root, Element):
        raise Exception("Root must be an Element")

    root.update_attributes(creator_attr)


def get_junos_interface_address(
    root: Element,
    device: str,
    interface: str,
    unit: str,
    family: Optional[str] = "inet",
    primary: Optional[bool] = True,
):
    """
    Get the addresses of a Junos interface.

    :param root: XML root
    :type root: Element
    :param device: Device name
    :type device: str
    :param interface: Interface name
    :type interface: str
    :param unit: Unit number
    :type unit: str
    :param primary: Only return primary addresses
    :type primary: bool
    :return: List of addresses
    :rtype: List[str]
    """

    device_path = f"/devices/device[name='{device}']/config/configuration"
    interface_path = f"/interfaces/interface[name='{interface}']"
    unit_path = f"/unit[name='{unit}']"
    full_path = device_path + interface_path + unit_path
    unit_root = get_path(root, full_path)

    found_addresses = []

    if not unit_root:
        return None

    try:
        if family == "inet":
            addresses = unit_root.family.inet.get_elements("address")
        elif family == "inet6":
            addresses = unit_root.family.inet6.get_elements("address")
        else:
            return None

        for address in addresses:
            if primary:
                if not address.get_elements("primary"):
                    continue
            found_addresses.append(str(address.name))

    except AttributeError:
        return None

    return found_addresses
