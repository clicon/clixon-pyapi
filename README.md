# Clixon Python API
<div align="center">
  <img src="https://www.clicon.org/Clixon_logga_liggande_med-ikon.png" width="400">
</div>

[![Build Status](https://github.com/clicon/clixon-pyapi/actions/workflows/ci.yml/badge.svg)](https://github.com/clicon/clixon-pyapi/actions/workflows/ci.yml)

Clixon Python API is a network services API for [Clixon controller](https://github.com/clicon/clixon-controller).

See [User guide](https://clixon-controller-docs.readthedocs.io/en/latest/) and [Clixon controller FAQ](https://github.com/clicon/clixon-controller/blob/main/FAQ.md).

## Installation
To install first install the dependencies either using Pip or, if you are using Ubuntu or Debian, use the requirements-apt.sh script.

Pip:

```
$ pip3 install -r requirements.txt
```

Ubuntu or Debian:

```
$ ./requirements-apt.sh
```

Then install the Clixon Python API:

```
./install.sh
```

## REST API

`clixon_rest.py` is a HTTP server which serves the controller services as a
REST API. It is meant to run behind NGINX, which terminates TLS and
authenticates the clients.

The endpoints are not written by hand. At startup the service YANG modules
are fetched from the backend over NETCONF, using get-schema, and the
resources, the JSON bodies and the OpenAPI description are rendered from that
YANG. A service defined as:

```
augment "/ctrl:services" {
    list ssh-users {
        key service-name;
        ...
    }
}
```

is served as:

```
GET    /api/v1/services/ssh-users
POST   /api/v1/services/ssh-users
GET    /api/v1/services/ssh-users/{service-name}
PUT    /api/v1/services/ssh-users/{service-name}
PATCH  /api/v1/services/ssh-users/{service-name}
DELETE /api/v1/services/ssh-users/{service-name}
POST   /api/v1/services/ssh-users/{service-name}/apply
```

The rest of the Python API is served as well, one resource per method of the
Clixon class:

```
GET    /api/v1/health              Health of the API and of the backend connection
GET    /api/v1/services            The services the backend serves YANG for
GET    /api/v1/schemas             get_schemas, the YANG schemas of the backend
GET    /api/v1/yang/{module}       get_service_yang, the YANG of a module
GET    /api/v1/config              get_root, any part of the configuration by xpath
PATCH  /api/v1/config              set_root, with a NETCONF XML body
POST   /api/v1/commit              commit
POST   /api/v1/push                push
POST   /api/v1/rollback            rollback
GET    /api/v1/compare             show_compare, running against candidate
GET    /api/v1/transactions        show_transactions
GET    /api/v1/transactions/{tid}  show_transactions of one transaction
GET    /api/v1/devices             show_devices
GET    /api/v1/devices/diff        show_devices_diff
POST   /api/v1/devices/pull        pull
POST   /api/v1/devices/connect     connection_open
POST   /api/v1/devices/rpc         device_rpc
POST   /api/v1/devices/template    apply_template
GET    /api/v1/openapi.json        OpenAPI description of all of the above
GET    /api/v1/docs                Swagger UI
```

`lock` and `unlock` have no resources of their own: a NETCONF lock lives as
long as the session it was taken in, and every request has a session of its
own. Pass `?lock=true` to a write request instead, which locks the candidate
datastore while that request is handled. `close_session` and `get_logger` are
internal to a session and are not served.

Start the server:

```
$ clixon_rest.py -f /usr/local/etc/clixon/controller.xml -p 8088
```

The write requests edit the candidate datastore and commit, which runs the
service scripts. The query parameters `commit` and `push`, both true by
default, control that: `?commit=false` leaves the change in the candidate
datastore and `?push=false` does not push it to the devices. Read requests
take a `source` parameter, one of running, candidate or actions. Run the
server with `-r` to refuse all write requests.

The requests which wait for the devices, such as a pull or a push, are bound
by the timeout of the backend session, 30 seconds by default. Use `-t` for
another default and `?timeout=` for a single request.

Create a service instance:

```
$ curl -X POST http://localhost:8088/api/v1/services/ssh-users \
    -H "Content-Type: application/json" \
    -d '{"service-name": "test", "username": [{"name": "alice", "role": "admin"}]}'
```

Send SIGHUP to reload the service YANG after installing a new service module.

Example NGINX configuration:

```
location /api/v1/ {
    proxy_pass http://127.0.0.1:8088/api/v1/;
    proxy_set_header X-Forwarded-Prefix /api/v1;
    proxy_set_header X-Remote-User $remote_user;
}
```

The user NGINX authenticated is taken from the `X-Remote-User` header, see
`-H`, and used as the user of the NETCONF sessions to the backend. The server
can also listen on a UNIX socket instead of a port, see `-U`, and `-S` points
Swagger UI at a locally hosted copy of its assets instead of the default CDN.

## License

License The Clixon controller Python API is open-source Apache
License, Version 2.0, see
[LICENSE](https://github.com/clicon/clixon-pyapi/blob/main/LICENSE).

The controller has a main branch continuously tested with CI.

Clixon controller Python API is sponsored by [SUNET](https://www.sunet.se)
