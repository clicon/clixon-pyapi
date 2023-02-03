from pyapi.clixon import rpc


@rpc()
def setup(root, log):
    log.info("Test 2")
    log.debug("Test 2")
