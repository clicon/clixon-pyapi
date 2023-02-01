from pyapi.clixon import rpc


@rpc()
def setup(root, log):
    services = root.services

    serivce_name = root.services.service.name

    if serivce_name == "vrf":
        for device in root.devices.device:
            log.info(
                f"Setting descriptio on {device.addr} to {services.vrf.service_id}")
            device.description = services.vrf.service_id
