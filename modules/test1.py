from pyapi.clixon import rpc


@rpc("/usr/local/var/controller.sock")
def setup(root):
    root.services.vrf.service_name.set_cdata("XXX")
