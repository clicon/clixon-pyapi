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
    mock_socket_instance.recv.side_effect = [
        b'\n#20\n<test><data/></test>\n##\n'
    ]
    mock_select.return_value = ([mock_socket_instance], [], [])
    sock = mock_socket()
    data = read(sock)

    assert data == "\n#20\n<test><data/></test>\n"
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
