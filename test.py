from pyapi.clixon import rpc

sockpath = "/usr/local/var/controller.sock"


@rpc(sockpath)
def test(root):
#    pref = root.services.vrf.routing_options.static_route.preference.get_cdata()
#    root.services.vrf.description.set_cdata(pref)
    root.devices.device.root.table.parameter.name.set_cdata("newname")
    root.devices.device.root.table.parameter.value.set_cdata("999")


if __name__ == "__main__":
    test()
