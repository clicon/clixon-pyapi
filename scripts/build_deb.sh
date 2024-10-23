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

# Update the change log
echo -n "clixon-pyapi (${VERSION}) " > build/debian/changelog

git --no-pager log --no-walk --encoding=utf-8 --expand-tabs=4 --pretty=format:"${VERSION} stable; urgency=medium%n%n * %w(,,2)%B%w()%n -- %an <%ae>  %aD%n" >> build/debian/changelog

if [ $? -ne 0 ]; then
    echo "Failed to update the change log."
    exit 1
fi

cp README.md build/
cp -r clixon build/
cp clixon_server.py build/
cp setup.py build/

# Set the version in version.py
echo "__version__ = \"${VERSION}\"" > build/clixon/version.py

# Build the Debian package
(cd build && dpkg-buildpackage -us -uc)
