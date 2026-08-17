# AGENT.md

Notes for coding agents working in this repository. Read this before changing
code, most of it is the kind of thing that is only learned by breaking it.

## What this is

The Python API of the [Clixon controller](https://github.com/clicon/clixon-controller).
It talks NETCONF over a UNIX socket to the clixon backend. Two programs are
shipped:

- `clixon_server.py` — the service daemon. It listens for `services-commit`
  notifications from the backend and runs the service modules which render the
  device configuration.
- `clixon_rest.py` — a REST/Swagger HTTP server, meant to run behind NGINX. It
  fetches the service YANG from the backend and renders its endpoints from it.

The `clixon` package is also imported directly by service modules, which get a
`Clixon` object and an element tree to work on.

## Layout

| Path | What it is |
| --- | --- |
| `clixon/clixon.py` | The `Clixon` class, one NETCONF session, one method per controller operation |
| `clixon/netconf.py` | `rpc_*` functions building RPC element trees. No I/O |
| `clixon/element.py` | `Element`, the XML tree used everywhere |
| `clixon/parser.py` | `parse_string`/`parse_file`, XML to `Element` |
| `clixon/sock.py` | Framed NETCONF read/write over the UNIX socket |
| `clixon/args.py` | Command line and configuration file arguments |
| `clixon/client.py` | The notification read loop of `clixon_server.py` |
| `clixon/modules.py` | Finding, loading and running service modules |
| `clixon/yang.py` | A small YANG parser, used to render the REST API |
| `clixon/helpers.py` | Helpers for service modules, client side tree navigation |
| `clixon_rest.py` | The REST server |
| `tests/` | The test suite, `pytest` |

## Running the tests

```
$ pytest
```

That is all. `pytest.ini` pins `testpaths = tests` and `python_files =
test_*.py`, which keeps scratch files in the root of the repository (they tend
to be named `test.py` or `apply_test.py` and to open a backend session at
import) out of the collection. Coverage of `clixon` and `clixon_rest` is
reported by default; it is at 95%, do not regress it.

The suite needs no backend. Everything is either a pure function, a patched
`clixon.clixon.send`/`read`, or a stubbed `Clixon` object:

- `tests/test_clixon.py` has a `clixon(read_values, **kwargs)` helper which
  patches the socket and feeds canned replies. Add a reply for every read the
  method under test makes, in order.
- `tests/test_rest_server.py` starts a real `RestServer` on an ephemeral port
  with `StubClixon` patched in. Add methods to `StubClixon` when the server
  starts calling something new.
- `tests/test_yang.py` holds `MODULE`/`MODULES`, a service YANG module used by
  the YANG and REST tests. Reuse it rather than writing another one.

## Style

- `black` with its defaults. Run `black` on the files you touch, but **only**
  on those: several files predate it and reformatting them buries the real
  change in noise. `clixon/clixon.py`, `clixon/event.py`, `clixon/exceptions.py`
  and a few test files are known to be unformatted; leave them be.
- Sphinx style docstrings (`:param x:`, `:type x:`, `:return:`, `:rtype:`) on
  public functions. Every test has a one line docstring, the `conftest.py`
  prints it as the test name.
- All imports at the top of the file.
- Module level `__private` functions are used as a convention for internal
  helpers.
- New RPC builders are named `rpc_<thing>_<verb>`: `rpc_config_get`,
  `rpc_devices_get`, `rpc_schema_get`, `rpc_schemas_get`. Keep it consistent.
- No new dependencies. The package installs with `pyyaml` and `xmltodict` and
  nothing else, and it has to keep working on a plain Debian box with the
  distribution packages (`requirements-apt.sh`). Python 3.11 is the floor.

## Traps

These have all cost time at least once.

**`clixon.args` sniffs `sys.argv` at import.** `clixon/clixon.py` calls
`get_arg()` at module level, so importing the package from a program with its
own command line makes clixon try to parse those arguments. It is defensive
about it now (unknown arguments and `-h`/`-V` are ignored quietly, see
`get_arg`), but a program with its own arguments should still seed
`clixon.args.global_args` before doing anything, the way `clixon_rest.init_args`
does. `NO_CLIXON_ARGS=1` in the environment turns the whole mechanism off.

**The XML parser escapes cdata.** `clixon/parser.py` re-escapes `&`, `<` and
`>` when it reads character data, and strips a leading and a trailing newline
per chunk. Values read out of an `Element` therefore need `xml.sax.saxutils.
unescape` before they are handed to a client, and anything whitespace
sensitive (a YANG module, a diff) must be pulled out of the raw reply string
with a regexp instead of going through `parse_string`. `Clixon.get_service_yang`
is the example to copy.

**`rpc_error_get` matches on substrings of the whole reply.** A reply which
merely contains the text `error-message` or `rpc-error` is treated as an error,
which a YANG module or a device configuration can easily do. Guard the call
with `if "<rpc-error" in data:` when the payload is free text.

**Signals only work in the main thread.** `clixon.helpers.timeout` uses
`SIGALRM`. It is fine in `clixon_server.py`, but anything threaded, such as the
REST server, must not depend on it. `clixon.sock.read` takes a `timeout` and
raises `TimeoutException` instead; that is what `Clixon.__wait_for_notification`
uses. If you add a method which waits for the backend, bound it the same way —
an unbounded `read` hangs the worker for ever.

**Datastores.** Writes go to `candidate` and become real on `commit`. `running`
is the committed configuration, and `actions` is the controller's scratch
datastore for service scripts: it holds leftovers from failed transactions and
is refilled from candidate on the next one, so do not be alarmed by what is in
there. `discard-changes` (`Clixon.rollback`) only touches candidate.

**The controller namespace prefix is `ctrl`.** `CONTROLLER_NS_PREFIX` in
`clixon/netconf.py`. It was `clixon-controller` until commit `ea7df58`; if a
test expects the old prefix, the test is stale.

**A lock lives as long as its session.** Each REST request opens its own
NETCONF session, which is why the REST API has no lock resource, only
`?lock=true` on the write requests.

## Working against a live backend

There is usually a controller running on the development machine:

```
/usr/local/var/run/controller/controller.sock   backend socket
/usr/local/etc/clixon/controller.xml            configuration
/usr/local/share/controller/modules/            service modules
/usr/local/share/controller/main/               controller YANG
```

Membership of the `clicon` group is needed to reach the socket. A quick probe:

```
$ NO_CLIXON_ARGS=1 python3 -c "
from clixon.clixon import Clixon
c = Clixon(sockpath='/usr/local/var/run/controller/controller.sock', read_only=True)
print(c.get_schemas())
c.close_session()"
```

Reads are free. **Writes are not**: a commit runs the service scripts and
changes the running configuration of the machine, and a push reaches the
devices. Test writes with `commit=false` and roll back afterwards, and ask
before committing or pushing for real.

Starting the REST server against it:

```
$ ./clixon_rest.py -f /usr/local/etc/clixon/controller.xml -p 8088
$ curl -s http://127.0.0.1:8088/api/v1/services
```

Note that the controller also has a C rest-api plugin of its own on port 8087
(`/api/v1/cli`, `/api/v1/jobs`), which is a different thing.

## Packaging

The metadata lives in `pyproject.toml` (PEP 621, setuptools backend), there is
no `setup.py`. The version is read from `clixon/version.py`, so that is the
only place to bump it. `CHANGELOG.md` is written per release.

```
$ python3 -m build          # wheel and sdist in dist/
$ ./install.sh              # scripts to /usr/local/bin, package with pip
$ ./scripts/build_deb.sh    # Debian package, needs a git checkout
```

The two programs are installed under their own names, `clixon_server.py` and
`clixon_rest.py`, through `script-files` in `pyproject.toml`. Entry points in
`[project.scripts]` would drop the `.py`, which the controller and the
packaging expect, so leave them as they are.

**A new program has to be added in four places**: `script-files` in
`pyproject.toml`, `install.sh`, `debian/install` and the list of files
`scripts/build_deb.sh` copies into `build/`. Forgetting the last one breaks the
Debian build only, which is easy to miss.

The Debian package is built by `dh` with pybuild, which picks the PEP 517 path
through `pybuild-plugin-pyproject`; that package, `python3-setuptools` and
`python3-wheel` are in `Build-Depends` for it.

The binary package is `python3-clixon-pyapi`. **Do not rename it back to
`python-clixon-pyapi`**: `dh_python3` skips every package whose name starts
with `python-`, that being the Python 2 prefix (`PKG_NAME_TPLS` in
`/usr/share/dh-python/dhpython/__init__.py`, applied at `debhelper.py:148`
before any other check, so `-p` cannot override it). A skipped package gets no
`${python3:Depends}`, no byte-compilation and its modules are left in the
version specific `/usr/lib/python3.11/dist-packages`. It keeps
`Provides`/`Replaces`/`Conflicts` on the old name so an upgrade removes it.

Check the result with `lintian python3-clixon-pyapi_*.deb`. Three errors are
expected and deliberate: the programs are also installed in `/usr/local/bin`,
which Policy 9.1.2 forbids, because the controller's YANG defaults
`CONTROLLER_ACTION_COMMAND` to `/usr/local/bin/clixon_server.py`. The empty
`override_dh_usrlocal` in `debian/rules` is what allows it. They are installed
in `/usr/bin` as well, from the wheel.

CI is `.github/workflows/ci.yml`, which runs `pytest` on Python 3.11 with the
dependencies from `requirements.txt`.
