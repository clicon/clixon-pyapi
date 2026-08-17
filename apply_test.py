from clixon.clixon import Clixon

with Clixon(source="running", target="candidate", push=False, commit=True) as clx:
    d = clx.apply_service("service-test", "asd", diff=False)
    print(d)
