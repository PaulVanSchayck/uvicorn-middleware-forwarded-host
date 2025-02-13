# Uvicorn Middleware Forwarded Host

<p>
  <a href="https://github.com/knmi/uvicorn-middleware-forwarded-host/actions?query=workflow%3ACI" target="_blank">
      <img src="https://github.com/knmi/uvicorn-middleware-forwarded-host/workflows/CI/badge.svg" alt="Test">
  </a>
  <a href="https://codecov.io/gh/knmi/uvicorn-middleware-forwarded-host" target="_blank">
      <img src="https://codecov.io/gh/knmi/uvicorn-middleware-forwarded-host/branch/master/graph/badge.svg" alt="Coverage">
  </a>
  <a href="https://pypi.org/project/uvicorn-middleware-forwarded-host" target="_blank">
      <img src="https://img.shields.io/pypi/v/uvicorn-middleware-forwarded-host?color=%2334D058&label=pypi%20package" alt="Package version">
  </a>
  <a href="https://pypistats.org/packages/uvicorn-middleware-forwarded-host" target="_blank">
      <img src="https://img.shields.io/pypi/dm/uvicorn-middleware-forwarded-host.svg" alt="Downloads">
  </a>
  <a href="https://github.com/knmi/uvicorn-middleware-forwarded-host/blob/master/LICENSE" target="_blank">
      <img src="https://img.shields.io/github/license/knmi/uvicorn-middleware-forwarded-host.svg" alt="License">
  </a>
</p>

Uvicorn (ASGI, FastAPI) middleware for handling the non-standard `X-Forwarded-Host` and `X-Forwarded-Prefix` header.

This middleware can be used when a known and trusted proxy is fronting the application,
and is trusted to be setting the `X-Forwarded-Host` and
`X-Forwarded-Prefix` headers with the host and path where the proxy is hosting the application.

Modifies the `root_path` (and related variables) and `Host` header information so that they reference
the location where the application is hosted by the proxy, rather than where it is directly hosted.

See the examples for more information.
## Install
```shell
pip install uvicorn-middleware-forwarded-host
```

Or you can install directly from source:

```shell
pip install git+https://github.com/KNMI/uvicorn-middleware-forwarded-host.git
```

## Usage

```python
from uvicorn_middleware_forwarded_host import ForwardedHostAndPrefixMiddleware
from fastapi import FastAPI
import os

app = FastAPI()
app.add_middleware(ForwardedHostAndPrefixMiddleware, trusted_hosts=os.environ.get("TRUSTED_PROXIES", "127.0.0.1"))
```

## IMPORTANT: Caveats and security concerns

You need to disable the Uvicorn `proxy_headers` option. This will disable the `ProxyHeadersMiddleware()`. Instead, this original middleware will be called from `ForwardedHostAndPrefixMiddleware()`. This is needed because the order of these middlewares matters. We first need to set the `host` and `root_path` before replacing the client IP. You can do this by setting `proxy_headers=False` in `uvicorn.run()`. Or, when using gunicorn, by using a custom uvicorn worker class and setting `CONFIG_KWARGS` (see `example.py`).

You need to set the proxies you trust using the `trusted_hosts` option. This is typically an IP address or CIDR IP range. There is no need to set `forwarded_allow_ips` uvicorn option. The value for `trusted_hosts` will be used for `ProxyHeadersMiddleware()`.

When using gunicorn on top of uvicorn, do **not** use the `FORWARDED_ALLOW_IPS` environment variable or gunicorn's `--forwarded-allow-ips` setting. For one gunicorn does not understand network ranges. More importantly, gunicorn should leave the `X-Forwarded-*` headers untouched.

**IMPORTANT:** Make sure you really **trust** your proxy. It should **always** set the extra headers, and remove any set by the client! Most proxies will do this by default with `X-Forwarded-For`, but won't do this with `X-Forwarded-Host` or `X-Forwarded-Prefix`. Wrong configuration would allow an outsider to set these values to something malicious.

## Example

Start a simple FastAPI application, served by uvicorn:
```bash
$ pip install -e '.[test]'
...
$ python3 example.py
INFO:     Started server process [35623]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

The `request.base_url` and `scope.root_path` have been set correctly:
```bash
$ curl -H "X-Forwarded-Host: example.com" -H "X-Forwarded-Prefix: /root" http://localhost:8000/app
{
  "message": "Hello World",
  "client": ["127.0.0.1", 44142],
  "root_path": "/root",
  "base_url": "http://example.com/root/"
}
```
Redirecting, for example in response to a trailing slash request, will also use the proxied host and prefix:
```bash
$ curl -v -H "X-Forwarded-Host: example.com" -H "X-Forwarded-Prefix: /root" http://localhost:8000/app/
...
< location: http://example.com/root/app
```
The root path has been added to the OpenAPI path in FastAPI's `/docs` endpoint:
```bash
$ curl -H "X-Forwarded-Host: example.com" -H "X-Forwarded-Prefix: /root" http://localhost:8000/docs
...
        url: '/root/openapi.json',
...
```
The root path itself is not directly accessible (as it should):
```bash
$ curl -H "X-Forwarded-Host: example.com" -H "X-Forwarded-Prefix: /root" http://localhost:8000/root/app
{"detail":"Not Found"}
```
The `X-Forwarded-For` header is also processed:
```bash
$ curl -H "X-Forwarded-For: 1.1.1.1" -H "X-Forwarded-Host: example.com" -H "X-Forwarded-Prefix: /root" http://localhost:8000/app
{
  "message": "Hello World",
  "client": ["1.1.1.1", 0],
  "root_path": "/root",
  "base_url": "http://example.com/root/"
}
```

## Contributing

Make an editable installation from within the repository root

```shell
pip install -e '.[test]'
```

### Running tests

```shell
pytest tests/
```

### Linting and typing

Linting and typing (mypy) is done using [pre-commit](https://pre-commit.com) hooks.

```shell
pip install pre-commit
pre-commit install
pre-commit run
```

## License

Apache License, Version 2.0
