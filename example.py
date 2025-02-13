import os

import uvicorn
from fastapi import FastAPI
from fastapi.requests import Request
from uvicorn.workers import UvicornWorker
from uvicorn_middleware_forwarded_host import ForwardedHostAndPrefixMiddleware


class MyUvicornWorker(UvicornWorker):
    # This worker class is **only** needed when using gunicorn. See `gunicorn.sh`
    CONFIG_KWARGS = {
        # This disables the default ProxyHeadersMiddleware. We will call this
        # middleware from ForwardedHostAndPrefixMiddleware
        "proxy_headers": False,
    }


app = FastAPI()
app.add_middleware(ForwardedHostAndPrefixMiddleware, trusted_hosts=os.environ.get("TRUSTED_PROXIES", "127.0.0.0/8"))


@app.get("/app")
def read_main(request: Request):
    return {
        "message": "Hello World",
        "client": request.scope.get("client"),
        "root_path": request.scope.get("root_path"),
        "base_url": str(request.base_url),
    }


if __name__ == "__main__":
    uvicorn.run("example:app", host="0.0.0.0", log_level="info", proxy_headers=False)
