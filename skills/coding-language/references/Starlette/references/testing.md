# Testing

## TestClient (Synchronous, Built on httpx)

### Constructor Surface

```python
from starlette.testclient import TestClient

client = TestClient(
    app,
    base_url="http://testserver",
    raise_server_exceptions=True,
    root_path="",
    backend="asyncio",                # or "trio"
    backend_options=None,
    cookies={"session": "abc"},
    headers={"X-Test": "1"},
    follow_redirects=True,
    client=("testclient", 50000),     # remote address in request.client
)
```

Useful options:

- `raise_server_exceptions=False` to inspect 500 responses.
- `headers=` and `cookies=` for default request context.
- `follow_redirects=False` when asserting redirects.
- `client=(host, port)` when application logic depends on `request.client`.
- `backend="trio"` or `backend_options={"use_uvloop": True}` for backend-specific tests.

```python
from starlette.testclient import TestClient

client = TestClient(app)

# HTTP methods
response = client.get("/")
response = client.post("/users", json={"name": "Alice"})
response = client.put("/users/1", json={"name": "Bob"})
response = client.patch("/users/1", json={"name": "Charlie"})
response = client.delete("/users/1")

# Assertions
assert response.status_code == 200
assert response.json() == {"hello": "world"}
assert response.headers["content-type"] == "application/json"

# Form data
response = client.post("/form", data={"field": "value"})

# File uploads
with open("test.txt", "rb") as f:
    response = client.post("/upload", files={"file": f})

# Custom headers
response = client.get("/", headers={"Authorization": "Bearer token123"})

# Disable redirect following
response = client.get("/redirect", follow_redirects=False)

# Test 500 responses (default raises the exception in test)
client = TestClient(app, raise_server_exceptions=False)
response = client.get("/error")
assert response.status_code == 500
```

**Requires**: `uv add httpx`

## Lifespan Testing

```python
def test_with_lifespan():
    with TestClient(app) as client:  # triggers startup
        response = client.get("/")
        assert response.status_code == 200
    # shutdown runs on exit
```

## WebSocket Testing

```python
def test_websocket():
    client = TestClient(app)
    with client.websocket_connect("/ws") as ws:
        ws.send_text("hello")
        data = ws.receive_text()
        assert data == "Echo: hello"

    # With subprotocols
    with client.websocket_connect("/ws", subprotocols=["graphql-ws"]) as ws:
        ws.send_json({"type": "connection_init"})
        msg = ws.receive_json()
        ws.close(code=1000)
```

## Async Testing (with httpx directly)

```python
from httpx import ASGITransport, AsyncClient


async def test_async():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/")
        assert response.status_code == 200
```

## Backend Selection

```python
with TestClient(app, backend="trio") as client:       # use trio instead of asyncio
    ...
with TestClient(app, backend_options={"use_uvloop": True}) as client:
    ...
```
