from clixon.clixon import rpc


@rpc()
def setup(root, log):
    log.info("Test 1")
    log.debug("Test 1")
