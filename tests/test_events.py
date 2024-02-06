from clixon.event import RPCEventHandler

e = RPCEventHandler()


@e.register("*")
def callback(ret):
    ret[0] = 0


@e.register("test*")
def callback1(ret):
    ret[0] = 1


@e.register("test2")
def callback2(ret):
    ret[0] = 2


def test_register_all():
    """
    Test that the callback is called when the event is emitted.
    """

    ret = [-1]

    e.emit("foobar", ret=ret)

    assert ret == [0]


def test_register():
    """
    Test that the callback is called when the event is emitted.
    """

    ret = [-1]

    e.emit("test", ret=ret)

    assert ret == [1]


def test_register2():
    """
    Test that the callback is called when the event is emitted.
    """

    ret = [-1]

    e.emit("test2", ret=ret)

    assert ret == [2]


def test_unregister():
    """
    Test that the callback is called when the event is emitted.
    """

    ret = [-1]

    e.unregister("*", callback)

    e.emit("foo", ret=ret)

    assert ret == [-1]


def test_unregister2():
    """
    Test that the callback is called when the event is emitted.
    """

    ret = [-1]

    e.unregister("test*", callback1)

    e.emit("test", ret=ret)

    assert ret == [-1]
