# Security Policy

## Supported Versions

The Clixon PyAPI `main` branch is continuously tested by CI. Releases
are cut from `main` (see [CHANGELOG.md](CHANGELOG.md) and
[Releases](https://github.com/clicon/clixon-pyapi/releases)). Security
fixes are made against `main` and included in the next release; only the
latest release and `main` are supported.

PyAPI is built on [Clixon](https://github.com/clicon/clixon) and is used by
[Clixon Controller](https://github.com/clicon/clixon-controller). Vulnerabilities
in those components may be reported the same way.

## Reporting a Vulnerability

Please report security vulnerabilities privately by email to
**info@clicon.org**, rather than filing a public GitHub issue.

Include, if possible:
- A description of the vulnerability and its potential impact.
- Steps to reproduce, or a minimal example (eg a NETCONF request, service
  script, or XML/JSON payload) that triggers it.
- The affected component (PyAPI server, services, Python library, NETCONF
  socket handling, etc.) and version or commit.

We will acknowledge your report, investigate, and work with you on a fix and
disclosure timeline before any public announcement.
