# HTTP Core: Routing, Requests, Responses, Endpoints, Exceptions

## Table of Contents

- ASGI toolkit mode
- Routing
- Requests
- Responses
- Endpoints
- Exception handling

## ASGI Toolkit Mode

Starlette can be used as a full framework or as a toolkit of reusable ASGI
components.

```python
from starlette.requests import Request
from starlette.responses import PlainTextResponse


async def app(scope, receive, send):
    assert scope["type"] == "http"
    request = Request(scope, receive)
    response = PlainTextResponse(f"{request.method} {request.url.path}")
    await response(scope, receive, send)
```

Use this pattern when:

- working inside FastAPI internals or custom middleware
- building a tiny ASGI app without `Starlette(...)`
- reusing `Request`, `Response`, `Headers`, `URL`, or other Starlette primitives directly

## Routing

### HTTP Routes with Path Parameters

```python
from starlette.requests import Request
from starlette.responses import PlainTextResponse
from starlette.routing import Route


async def user_detail(request: Request) -> PlainTextResponse:
    user_id = request.path_params["user_id"]
    return PlainTextResponse(f"User {user_id}")


routes = [
    Route("/", homepage),
    Route("/users/{user_id:int}", user_detail, methods=["GET"]),
    Route("/files/{filepath:path}", serve_file),
    Route("/items/{item_id:uuid}", item_detail),
    Route("/price/{amount:float}", show_price),
]
```

**Built-in path convertors**: `str` (default -- any non-slash chars), `int`, `float`, `uuid`, `path` (any chars including slashes).

### Custom Path Convertor

```python
from datetime import datetime
from starlette.convertors import Convertor, register_url_convertor


class DateTimeConvertor(Convertor[datetime]):
    regex = r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}"

    def convert(self, value: str) -> datetime:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%S")

    def to_string(self, value: datetime) -> str:
        return value.strftime("%Y-%m-%dT%H:%M:%S")


register_url_convertor("datetime", DateTimeConvertor())
# Usage: Route("/events/{when:datetime}", event_handler)
```

### Nested Routes (Mount)

```python
from starlette.routing import Mount, Route

routes = [
    Route("/", homepage),
    Mount("/users", routes=[
        Route("/", users_list, methods=["GET", "POST"]),
        Route("/{username}", user_detail),
    ]),
    Mount("/api/v1", routes=[
        Route("/items", items_list),
    ]),
]
```

### Mount Sub-Applications

```python
routes = [
    Mount("/static", app=StaticFiles(directory="static"), name="static"),
    Mount("/admin", app=admin_app),  # any ASGI app
]
```

### Host-Based Routing

```python
from starlette.routing import Host

routes = [
    Host("api.example.org", app=api_app, name="api"),
    Host("{subdomain}.example.org", app=subdomain_app, name="subdomain"),
]
```

Port is stripped for matching. Host patterns support path-style parameters.

### Reverse URL Lookups

```python
# From request (returns full URL with scheme and host)
url = request.url_for("user_detail", username="tom")

# Nested mount names use colon separator
url = request.url_for("users:user_detail", username="tom")

# Static file URL
url = request.url_for("static", path="/css/style.css")

# Without request context (returns URLPath -- path only, no host/scheme)
path = app.url_path_for("user_detail", username="tom")

# Convert URLPath to absolute URL
absolute = path.make_absolute_url(base_url="https://example.com")
```

### Route Priority

First match wins. Place specific routes before parameterized ones:

```python
routes = [
    Route("/users/me", current_user),       # specific -- checked first
    Route("/users/{username}", user_detail), # parameterized -- checked second
]
```

### Router (Lightweight, Without App Middleware)

```python
from starlette.routing import Router

router = Router(
    routes=[Route("/", homepage)],
    redirect_slashes=True,  # /users/ redirects to /users
)
```

---

## Requests

### Properties

```python
from starlette.requests import Request

async def handler(request: Request):
    request["path"]             # mapping interface onto ASGI scope
    request.scope               # raw ASGI scope dict
    request.method              # "GET", "POST", etc.
    request.url                 # URL object (str-like): "https://example.com/path?q=1"
    request.url.path            # "/path"
    request.url.scheme          # "https"
    request.url.port            # 443
    request.base_url            # URL for the app root (scheme + host + root_path)
    request.headers             # Headers -- case-insensitive, immutable multi-dict
    request.headers["content-type"]
    request.headers.getlist("x-forwarded-for")
    request.query_params        # QueryParams -- immutable multi-dict
    request.query_params["q"]
    request.query_params.getlist("tag")
    request.path_params         # dict[str, Any] from route convertors
    request.cookies             # dict[str, str]
    request.client              # Address(host, port) or None
    request.app                 # the Starlette/Router instance
    request.state               # State object for per-request data
    request.session             # dict -- requires SessionMiddleware
    request.user                # BaseUser -- requires AuthenticationMiddleware
    request.auth                # AuthCredentials -- requires AuthenticationMiddleware
```

### Body Access

```python
# Full body as bytes (cached after first call)
body: bytes = await request.body()

# JSON (cached after first call)
data: Any = await request.json()

# Streaming body (for large payloads -- cannot use body()/json() after)
async for chunk in request.stream():
    process(chunk)

# Form data -- usable as EITHER await OR async context manager
# As context manager (recommended -- auto-closes upload files):
async with request.form() as form:
    username = form["username"]        # str field
    upload = form["file"]              # UploadFile
    contents = await upload.read()

# As awaitable (caller must close):
form = await request.form()
try:
    username = form["username"]
finally:
    await request.close()

# Form with custom limits
async with request.form(
    max_files=100,              # default 1000
    max_fields=500,             # default 1000
    max_part_size=5*1024*1024,  # default 1MB
) as form:
    ...
```

**Requires**: `uv add python-multipart` for `request.form()`.

### UploadFile

```python
async with request.form() as form:
    upload = form["file"]

    # Properties
    upload.filename       # str | None -- "photo.jpg"
    upload.content_type   # str | None -- "image/jpeg" (from Content-Type header)
    upload.size           # int | None -- file size in bytes
    upload.headers        # Headers -- all headers for this part

    # Async I/O methods
    content = await upload.read(size=-1)  # read all or N bytes
    await upload.seek(0)                  # rewind
    await upload.write(b"data")           # write (for in-memory modification)
    await upload.close()                  # explicit close
```

### Request State

```python
import time

# Middleware sets state
request.state.start_time = time.time()

# Endpoint reads it
elapsed = time.time() - request.state.start_time

# Dict-style access works too
request.state["key"] = "value"
val = request.state["key"]
```

### Disconnect Detection

```python
import asyncio

async def long_poll(request: Request):
    while not await request.is_disconnected():
        await asyncio.sleep(1)
    return Response("Client left")
```

### Server Push (HTTP/2 -- requires server support)

```python
async def homepage(request: Request):
    await request.send_push_promise("/static/style.css")  # no-op if unsupported
    return HTMLResponse('<html><head><link rel="stylesheet" href="/static/style.css"/></head></html>')
```

---

## Responses

### Response Types

```python
from starlette.responses import (
    Response, PlainTextResponse, HTMLResponse,
    JSONResponse, RedirectResponse, StreamingResponse, FileResponse,
)

# Plain text
PlainTextResponse("Hello")

# HTML
HTMLResponse("<h1>Hello</h1>")

# JSON
JSONResponse({"key": "value"})
JSONResponse({"error": "not found"}, status_code=404)

# Generic (specify media_type)
Response(b"\x89PNG...", media_type="image/png")

# Redirect (default 307 Temporary Redirect)
RedirectResponse(url="/new-location")
RedirectResponse(url="/permanent", status_code=301)

# Empty (no body, no content-type)
Response(status_code=204)
```

### Custom JSON Serialization

```python
import orjson
from starlette.responses import JSONResponse


class OrjsonResponse(JSONResponse):
    media_type = "application/json"

    def render(self, content) -> bytes:
        return orjson.dumps(content)
```

### Custom Response Type

```python
from starlette.responses import Response


class XMLResponse(Response):
    media_type = "application/xml"
    charset = "utf-8"
```

### Streaming Response

```python
import asyncio
from starlette.responses import StreamingResponse


async def number_stream():
    for i in range(100):
        yield f"data: {i}\n"
        await asyncio.sleep(0.1)


async def stream_endpoint(request: Request):
    return StreamingResponse(number_stream(), media_type="text/plain")
```

Both sync iterables and async iterables/generators work.

### File Response (with Range Request Support)

```python
from starlette.responses import FileResponse

# Download (Content-Disposition: attachment)
FileResponse("report.pdf")

# Inline display in browser
FileResponse("image.png", filename="photo.png", content_disposition_type="inline")

# Custom media type
FileResponse("data.bin", media_type="application/octet-stream")
```

Automatically handles: `Accept-Ranges`, single/multi-range requests (206),
`If-Range`/`If-None-Match` conditionals (304), ETag, Last-Modified, HEAD requests.

### Cookies

```python
response = JSONResponse({"ok": True})

response.set_cookie(
    key="session_id",
    value="abc123",
    max_age=3600,               # seconds until expiry
    expires=None,               # datetime | str | int | None
    path="/",                   # cookie path scope (None omits Path)
    domain=None,                # ".example.com"
    secure=True,                # HTTPS only
    httponly=True,               # no JavaScript access
    samesite="lax",             # "lax" | "strict" | "none" | None (omit attr)
    # partitioned=True,         # Python 3.14+ only -- CHIPS partitioned cookies
)

response.delete_cookie(key="session_id", path="/")
```

### Response Headers

```python
response = JSONResponse({"data": 1})
response.headers["X-Request-Id"] = "abc-123"
response.headers.append("X-Multi", "value1")
response.headers.append("X-Multi", "value2")
```

---

## Endpoints (Class-Based Views)

### HTTPEndpoint

```python
from starlette.endpoints import HTTPEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route


class UserEndpoint(HTTPEndpoint):
    async def get(self, request: Request) -> JSONResponse:
        return JSONResponse([{"name": "Alice"}, {"name": "Bob"}])

    async def post(self, request: Request) -> JSONResponse:
        data = await request.json()
        return JSONResponse(data, status_code=201)

    async def delete(self, request: Request) -> JSONResponse:
        return JSONResponse({"deleted": True})


# Pass the CLASS (not instance) to Route
routes = [Route("/users", UserEndpoint)]
```

Unhandled methods return 405 Method Not Allowed with `Allow` header.

### WebSocketEndpoint

```python
from starlette.endpoints import WebSocketEndpoint
from starlette.routing import WebSocketRoute
from starlette.websockets import WebSocket


class EchoEndpoint(WebSocketEndpoint):
    encoding = "text"  # "text" | "bytes" | "json" | None

    async def on_connect(self, websocket: WebSocket) -> None:
        await websocket.accept()

    async def on_receive(self, websocket: WebSocket, data: str) -> None:
        await websocket.send_text(f"Echo: {data}")

    async def on_disconnect(self, websocket: WebSocket, close_code: int) -> None:
        pass


routes = [WebSocketRoute("/ws", EchoEndpoint)]
```

---

## Exception Handling

### Registering Handlers

```python
from starlette.exceptions import HTTPException, WebSocketException
from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse
from starlette.websockets import WebSocket


async def not_found(request: Request, exc: HTTPException) -> HTMLResponse:
    return HTMLResponse("<h1>Page Not Found</h1>", status_code=404)


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(
        {"detail": exc.detail},
        status_code=exc.status_code,
        headers=exc.headers,
    )


async def ws_exception_handler(websocket: WebSocket, exc: WebSocketException) -> None:
    await websocket.close(code=1008)


async def global_error_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse({"detail": "Internal server error"}, status_code=500)


exception_handlers = {
    404: not_found,                         # by status code
    HTTPException: http_exception_handler,  # by exception class
    WebSocketException: ws_exception_handler,
    Exception: global_error_handler,        # catch-all for unhandled errors
}

app = Starlette(routes=routes, exception_handlers=exception_handlers)
```

### Raising Exceptions

```python
from starlette.exceptions import HTTPException, WebSocketException

# In endpoints or route handlers (not middleware):
raise HTTPException(status_code=404, detail="Item not found")
raise HTTPException(status_code=401, headers={"WWW-Authenticate": "Bearer"})

# In WebSocket handlers:
raise WebSocketException(code=1008, reason="Policy violation")
```

`HTTPException` raised in a WebSocket handler before `accept()` sends a proper
HTTP error response (not a WebSocket close frame).

### Middleware Stack and Errors

- **Handled exceptions** (`HTTPException`): caught by `ExceptionMiddleware`, converted to responses
- **Unhandled exceptions**: bubble up to `ServerErrorMiddleware`, which returns 500 or debug traceback
- `debug=True` overrides 500 handlers with interactive traceback pages
