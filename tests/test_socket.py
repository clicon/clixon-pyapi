from unittest.mock import patch, MagicMock
from clixon.sock import create_socket, read, send
import socket


@patch('socket.socket')
def test_create_socket(mock_socket):
    """
    Test that create_socket returns a socket instance.
    """

    mock_socket_instance = MagicMock()
    mock_socket.return_value = mock_socket_instance
    sockpath = "test_socket_path"
    socket = create_socket(sockpath)

    assert socket == mock_socket_instance

    mock_socket_instance.setblocking.assert_called_with(False)
    mock_socket_instance.connect.assert_called_with(sockpath)


@patch('select.select')
@patch('socket.socket')
def test_read(mock_socket, mock_select):
    """
    Test that read returns the data from the socket.
    """

    mock_socket_instance = MagicMock()
    mock_socket.return_value = mock_socket_instance
    mock_socket_instance.recv.return_value = b'\n#20\n<test><data/></test>\n##\n'
    mock_select.return_value = ([mock_socket_instance], [], [])
    sock = mock_socket()
    data = read(sock)

    assert data == "\n#20\n<test><data/></test>\n##\n"
    mock_select.assert_called()


@patch('select.select')
@patch('socket.socket')
def test_send(mock_socket, mock_select):
    """
    Test that send sends the data to the socket.
    """

    mock_socket_instance = socket.socket()
    mock_socket.return_value = mock_socket_instance
    mock_select.return_value = ([], [mock_socket_instance], [])
    sock = mock_socket()
    send(sock, "\n#20\n<test><data/></test>\n##\n")
    mock_socket_instance.send.assert_called()
    mock_select.assert_called()


def test_send_read_roundtrip_large_message():
    """
    Test that a message much larger than the socket buffer survives send and
    read, including partial sends.
    """

    import socket
    import threading

    from clixon.sock import read, send

    a, b = socket.socketpair()
    payload = "<rpc>" + "<x>é</x>" * 600000 + "</rpc>"
    received = []

    reader = threading.Thread(target=lambda: received.append(read(b)))
    reader.start()

    send(a, payload)
    reader.join(timeout=30)

    a.close()
    b.close()

    assert received == [payload]


def _roundtrip_with_logging(monkeypatch, caplog, xml):
    """
    Send and read a message with debug logging, with or without --xml.
    """

    import logging
    import socket

    import clixon.sock as sock_module

    monkeypatch.setattr(sock_module, "get_arg", lambda opt: xml if opt == "xml" else None)
    monkeypatch.setattr(sock_module.logger, "level", logging.DEBUG)
    caplog.set_level(logging.DEBUG, logger=sock_module.logger.name)

    a, b = socket.socketpair()

    try:
        send(a, "<hello-xml-marker/>")
        assert read(b) == "<hello-xml-marker/>"
    finally:
        a.close()
        b.close()

    return caplog.text


def test_debug_log_without_xml(monkeypatch, caplog):
    """
    Test that debug logs show lengths but not the XML without --xml.
    """

    text = _roundtrip_with_logging(monkeypatch, caplog, xml=False)

    assert "len=" in text
    assert "hello-xml-marker" not in text


def test_debug_log_with_xml(monkeypatch, caplog):
    """
    Test that debug logs show the XML sent and read with --xml.
    """

    text = _roundtrip_with_logging(monkeypatch, caplog, xml=True)

    assert "len=" in text
    assert text.count("<hello-xml-marker/>") == 2
