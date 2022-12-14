import socket
import struct
import sys

HDRLEN = 8


def connect(sockpath):
    """
    Connect socket either by using a Clixon configuration file
    or with the socket path directly.
    """

    try:
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.connect(sockpath)
    except socket.error as e:
        print(f"Failed to create and connect socket: {e}")
        sys.exit(-1)

    return sock


def send(sock, data):
    """
    Send data over socket. Will pack the data to fit Clixons dataframe which
    is used to communicate over the UNIX socket.

    struct clicon_msg {
        uint32_t    op_len;     /* length of message. network byte order. */
        uint32_t    op_id;      /* session-id. network byte order. */
        char        op_body[0]; /* rest of message, actual data */
    };

    op_len is the length of the NETCONF message + the size of the header
    (8 bytes) defined as HDRLEN above.

    """
    datalen = len(data)
    opid = 42

    if type(data) != bytes:
        data = str.encode(data)

    frame = struct.pack("!II", datalen + HDRLEN, opid)

    try:
        sock.sendall(frame + data)
    except socket.errno as e:
        print(f"Failed to send data to socket: {e}")
        return None

    return datalen + HDRLEN


def read(sock):
    """
    Read from the socket. Will pick up the header first and figure out
    the number of bytes of NETCONF message to read from the socket.
    """
    try:
        data = sock.recv(HDRLEN)
        datalen, _ = struct.unpack("!II", data)
        data = sock.recv(datalen)
        data = data.decode()[:-1]
    except socket.error as e:
        print(f"Failed to receive data from socket: {e}")
        return None

    return data
