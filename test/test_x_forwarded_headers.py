from fastapi import APIRouter
from fastapi import FastAPI
from fastapi.requests import Request
from fastapi.testclient import TestClient
from starlette.responses import PlainTextResponse
from uvicorn_middleware_forwarded_host import ForwardedHostAndPrefixMiddleware


def sample_endpoint(request: Request):
    return PlainTextResponse(str(request.base_url))


def minimal_fastapi_with_middleware(trusted_hosts):
    app = FastAPI()

    app.add_middleware(ForwardedHostAndPrefixMiddleware, trusted_hosts=trusted_hosts)

    router = APIRouter()
    router.get(path="/sample")(sample_endpoint)
    app.include_router(router)
    client = TestClient(app)

    return app, client


def test_x_forwarded_proto():
    app, client = minimal_fastapi_with_middleware(trusted_hosts="*")

    resp = client.get("/sample", headers={"X-Forwarded-Proto": "https"})

    assert resp.status_code == 200
    assert resp.text == "https://testserver/"


def test_x_forwarded_host():
    app, client = minimal_fastapi_with_middleware(trusted_hosts="*")

    resp = client.get("/sample", headers={"X-Forwarded-Host": "example.com"})

    assert resp.status_code == 200
    assert resp.text == "http://example.com/"


def test_x_forwarded_prefix():
    app, client = minimal_fastapi_with_middleware(trusted_hosts="*")

    resp = client.get("/sample", headers={"x-forwarded-prefix": "/root"})

    assert resp.status_code == 200
    assert resp.text == "http://testserver/root/"


def test_trailing_slash_redirect():
    app, client = minimal_fastapi_with_middleware(trusted_hosts="*")

    resp = client.get(
        "/sample/",
        follow_redirects=False,
        headers={"X-Forwarded-Proto": "https", "X-Forwarded-Host": "example.com", "x-forwarded-prefix": "/root"},
    )
    assert resp.status_code == 307
    assert resp.headers["location"] == "https://example.com/root/sample"


def test_trusted_hosts_disallowed():
    app, client = minimal_fastapi_with_middleware(trusted_hosts="127.0.0.42")

    resp = client.get("/sample", headers={"X-Forwarded-Host": "example.com", "x-forwarded-prefix": "/root"})

    assert resp.status_code == 200
    assert resp.text == "http://testserver/"


def test_trusted_hosts_allowed():
    # Basic test with the hardcoded `testclient` host name.  Could be extended to real IP addresses with
    # https://stackoverflow.com/questions/70131415/how-to-mock-client-ip-on-fastapi-testclient-testclient
    app, client = minimal_fastapi_with_middleware(trusted_hosts="testclient")

    resp = client.get("/sample", headers={"X-Forwarded-Host": "example.com", "x-forwarded-prefix": "/root"})

    assert resp.status_code == 200
    assert resp.text == "http://example.com/root/"


def test_trusted_hosts_forwarded_for():
    # Basic test with the hardcoded `testclient` host name.  Could be extended to real IP addresses with
    # https://stackoverflow.com/questions/70131415/how-to-mock-client-ip-on-fastapi-testclient-testclient
    app, client = minimal_fastapi_with_middleware(trusted_hosts="testclient")

    # We are also passing X-Forwarded-For. This should not replace the client,
    # until **after** ForwardedHostAndPrefixMiddleware. This tests for that
    resp = client.get(
        "/sample", headers={"X-Forwarded-For": "foo", "X-Forwarded-Host": "example.com", "x-forwarded-prefix": "/root"}
    )

    assert resp.status_code == 200
    assert resp.text == "http://example.com/root/"


def test_root_path_in_docs():
    app, client = minimal_fastapi_with_middleware(trusted_hosts="*")

    resp = client.get("/openapi.json", headers={"x-forwarded-prefix": "/root"})

    assert resp.status_code == 200
    assert resp.json()["servers"][0]["url"] == "/root"


def test_x_forwarded_prefix_with_trailing_space():
    app, client = minimal_fastapi_with_middleware(trusted_hosts="*")

    resp = client.get("/sample", headers={"x-forwarded-prefix": "/root ", "X-Forwarded-Host": " example.com"})

    assert resp.status_code == 200
    assert resp.text == "http://example.com/root/"
