#!/bin/sh

set -e

sudo cp clixon_server.py clixon_rest.py /usr/local/bin/

# Debian and friends mark the system Python as externally managed, PEP 668,
# and pip refuses to install into it unless it is told to. Older versions of
# pip have neither the check nor the flag, hence the test rather than a
# fallback, which would print the whole PEP 668 error before succeeding.
if pip3 install --help 2>/dev/null | grep -q -- --break-system-packages; then
    sudo pip3 install --break-system-packages .
else
    sudo pip3 install .
fi
