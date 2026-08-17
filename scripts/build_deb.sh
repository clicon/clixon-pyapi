#!/bin/sh

set -e

#
# This script is used to build Debian packages for Clixon.
#

# Make sure the script is started from the cligen directory
if [ ! -f scripts/version.sh ]; then
    echo "This script must be run from the clixon directory."
    exit 1
fi

VERSION=$(./scripts/version.sh)

if [ $? -ne 0 ]; then
    echo "Failed to determine the version of Clixon."
    exit 1
fi

# Create the build/ directory
if [ ! -d build ]; then
    mkdir build
fi

# Copy the Debian files to the build directory
cp -r debian build/

# Update the change log. The body of the commit message is indented and its
# empty lines dropped, a change entry with a line of its own in the first
# column is not a valid changelog.
{
    echo "clixon-pyapi (${VERSION}) stable; urgency=medium"
    echo

    git --no-pager log --no-walk --encoding=utf-8 --expand-tabs=4 \
        --pretty=format:"%B" |
        sed -e 's/[[:space:]]*$//' -e '/./!d' -e 's/^/    /' -e '1s/^    /  * /'

    echo
    git --no-pager log --no-walk --encoding=utf-8 \
        --pretty=format:" -- %an <%ae>  %aD%n"
} > build/debian/changelog

if [ $? -ne 0 ]; then
    echo "Failed to update the change log."
    exit 1
fi

# Populate the build directory
cp README.md build/
cp -r clixon build/
cp clixon_server.py build/
cp clixon_rest.py build/
cp pyproject.toml build/

# Build the Debian package
(cd build && dpkg-buildpackage -us -uc)
