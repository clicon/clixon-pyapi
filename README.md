# clixon-pyapi

[![Build Status](https://github.com/clicon/clixon-pyapi/actions/workflows/ci.yml/badge.svg)](https://github.com/clicon/clixon-pyapi/actions/workflows/ci.yml)

Clixon python API layer using internal NETCONF

## Install

```
$ pip3 install -r requirements.txt
$ python3 -m build
$ sudo python3 -m pip3 install dist/<wheel file>
```

**Note**: `sudo` installs _clixon_server_ script under _/usr/local/bin/_ directory.

Currently `clixon-controller` expects a _clixon_server.py_, in order to support this do

```
sudo ln -s $(which clixon_server) /usr/local/bin/clixon_server.py
```

## Develop

```
python3 -m venv venv
source venv/bin/activate
python3 -m pip install -r requirements.txt
python3 -m pip install -e .
```

---

For more info, see [user guide](https://clixon-controller-docs.readthedocs.io/en/latest/)
