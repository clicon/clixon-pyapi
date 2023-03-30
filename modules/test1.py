from clixon.clixon import rpc


@rpc()
def setup(root, log):
    for device in root.devices.device:
        device.root.delete("table")
        device.root.create("table", attributes={"xmlns": "urn:example:clixon"})

        for service in root.services.test:
            parameter = service.table.parameter

            device.root.table.add(parameter)

        print(device.dumps())


if __name__ == "__main__":
    setup()
