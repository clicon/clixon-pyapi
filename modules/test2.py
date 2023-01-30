from pyapi.clixon import rpc


@rpc("/usr/local/var/controller.sock")
def setup(root):
    print("Test2, got tree")
