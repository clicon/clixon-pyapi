from clixon.helpers import get_service_instance, get_path
from clixon.parser import parse_template_config

SERVICE = "test"


def setup(root, log, **kwargs):
    instance = get_service_instance(root, SERVICE, kwargs)

    if not instance:
        return

    template_name = instance.template_name.get_data()
    template = parse_template_config(
        root, template_name,
        NAME="name",
        MEMBERS="1234:4321"
    ).policy_options

    for device_name in instance.devices:
        device_root = get_path(
            root, f"/devices/device[name='{device_name}']/config/configuration"
        )

        if not device_root:
            raise Exception("Device not found")

        device_root.add(template)

        as_number = get_path(
            device_root, "/routing-options/autonomous-system/as-number"
        )

        if not as_number:
            raise Exception("AS number not found")

        log.info("")
        log.info(f"AS number: {as_number.get_data()}")
        log.info("")
