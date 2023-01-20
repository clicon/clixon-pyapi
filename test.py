from pyapi.clixon import rpc

sockpath = "/usr/local/var/example/example.sock"


@rpc(sockpath)
def test(root):
    root.table.parameter[0].name.set_cdata("parameter XXX")
    root.table.parameter[0].value.set_cdata("value XXX")


if __name__ == "__main__":
    test()
