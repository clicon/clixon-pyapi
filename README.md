# clixon-pyapi

[![Build Status](https://github.com/clicon/clixon-pyapi/actions/workflows/ci.yml/badge.svg)](https://github.com/clicon/clixon-pyapi/actions/workflows/ci.yml)

Clixon python API layer using internal NETCONF

To install:
```
$ pip3 install -r requirements.txt
$ python3 -m build
$ python3 -m pip3 install dist/<wheel file>
```

To develop:
```
python3 -m venv venv
source venv/bin/activate
python3 -m pip install -r requirements.txt
python3 -m pip install -e .
```

For more info, see [user guide](https://clixon-controller-docs.readthedocs.io/en/latest/)
