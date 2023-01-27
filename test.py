from pyapi.clixon import rpc

sockpath = "/usr/local/var/example/example.sock"


@rpc(sockpath)
def test(root):
    root.table.parameter.name.set_cdata("XXX")


if __name__ == "__main__":
    test()
