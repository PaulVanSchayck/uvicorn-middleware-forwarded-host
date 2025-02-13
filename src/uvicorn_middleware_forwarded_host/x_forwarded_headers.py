import urllib.parse

from uvicorn._types import ASGIReceiveCallable
from uvicorn._types import ASGISendCallable
from uvicorn._types import Scope
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware


class ForwardedHostAndPrefixMiddleware(ProxyHeadersMiddleware):
    """Middleware for handling the non-standard X-Forwarded-Host and X-Forwarded-Prefix header.

    This middleware can be used when a known proxy is fronting the application,
    and is trusted to be properly setting the `X-Forwarded-Host` and
    `X-Forwarded-Prefix` headers with the host and path where the proxy is hosting the application.

    Modifies the `root_path` (and related variables) and `Host` header information so that they reference
    the location where the API is hosted by the proxy, rather than where it is directly hosted.

    IMPORTANT: This middleware replaces ProxyHeadersMiddleware, and makes use of the same trusted_hosts implementation.
    When using it, you need to disable ProxyHeadersMiddleware in uvicorn by setting `proxy_headers` to false.
    """

    async def __call__(self, scope: Scope, receive: ASGIReceiveCallable, send: ASGISendCallable) -> None:
        if scope["type"] == "lifespan":
            return await self.app(scope, receive, send)

        # Perform the trusted_host check (--forwarded_allow_ips). Same as in ProxyHeadersMiddleware
        client_addr = scope.get("client")
        client_host = client_addr[0] if client_addr else None
        if client_host not in self.trusted_hosts:
            return await self.app(scope, receive, send)

        headers: dict[bytes, bytes] = dict(scope["headers"])

        if b"x-forwarded-prefix" in headers:
            prefix = headers[b"x-forwarded-prefix"].decode("ascii").strip()

            # Prevent malicious input, while still allowing slashes
            prefix = urllib.parse.quote(prefix, safe="/")

            # This mimics how uvicorn is setting the root_path
            # https://github.com/encode/uvicorn/blob/6ffaaf7c2f78274889da1572832dd307a8b117d3/uvicorn/protocols/http/httptools_impl.py#L250
            scope["root_path"] = prefix
            scope["path"] = prefix + scope["path"]
            scope["raw_path"] = prefix.encode("ascii") + scope["raw_path"]

        if b"x-forwarded-host" in headers:
            forwarded_host = headers[b"x-forwarded-host"].decode("ascii").strip()

            # Prevent malicious input
            forwarded_host = urllib.parse.quote(forwarded_host)

            # Replace the Host header with the value of the X-Forwarded-Host header
            scope["headers"] = [
                (k, forwarded_host.encode("ascii")) if k == b"host" else (k, v) for k, v in scope["headers"]
            ]

        # Calling the parent ProxyHeadersMiddleware **after** replacing these headers, as ProxyHeadersMiddleware
        # will replace the client address if X-Forwarded-For has been set
        return await super().__call__(scope, receive, send)
