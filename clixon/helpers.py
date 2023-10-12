from clixon.clixon import Clixon
from clixon.args import get_logger
from clixon.element import Element
from typing import List, Optional

log = get_logger()


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


if __name__ == "__main__":
    c = Clixon()
    root = c.get_root()
    print(get_openconfig_interface_address(
        root, "lo0", "0", "juniper1", "inet"))
