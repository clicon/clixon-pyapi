from pyapi.clixon import rpc


@rpc()
def setup(root, log):
    log.info("Test2")
