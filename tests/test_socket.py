from unittest.mock import patch, MagicMock
from clixon.sock import create_socket, read, send
import socket


@patch('socket.socket')
def test_create_socket(mock_socket):
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
    mock_socket_instance = MagicMock()
    mock_socket.return_value = mock_socket_instance
    mock_socket_instance.recv.side_effect = [
        b'\x00\x00\x00\x14\x00\x00\x00\x00', b'<test><data/></test>\x00']
    mock_select.return_value = ([mock_socket_instance], [], [])
    sock = mock_socket()
    data = read(sock)
    assert data == "<test><data/></test>"
    mock_select.assert_called()


@patch('select.select')
@patch('socket.socket')
def test_send(mock_socket, mock_select):
    mock_socket_instance = socket.socket()
    mock_socket.return_value = mock_socket_instance
    mock_select.return_value = ([], [mock_socket_instance], [])
    sock = mock_socket()
    send(sock, "<test><data/></test>")
    mock_socket_instance.send.assert_called()
    mock_select.assert_called()
