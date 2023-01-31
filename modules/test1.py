from pyapi.clixon import rpc
from time import sleep


@rpc()
def setup(root, log):
    log.info("Sleeping")
    sleep(5)
    log.info("Good morning")
