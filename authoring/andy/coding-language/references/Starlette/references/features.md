# Features: Configuration, Lifespan, WebSockets, Static Files, Templates, Auth, Background Tasks

## Table of Contents

- Configuration
- Lifespan
- WebSockets
- Static files
- Templates
- Authentication
- Background tasks

## Configuration

### Config from .env Files

```python
from starlette.config import Config
from starlette.datastructures import CommaSeparatedStrings, Secret

config = Config(".env")

DEBUG = config("DEBUG", cast=bool, default=False)
DATABASE_URL = config("DATABASE_URL")
SECRET_KEY = config("SECRET_KEY", cast=Secret)
ALLOWED_HOSTS = config("ALLOWED_HOSTS", cast=CommaSeparatedStrings)
```

```shell
# .env
DEBUG=True
DATABASE_URL=postgresql://user:password@localhost:5432/mydb
SECRET_KEY=change-me
ALLOWED_HOSTS=127.0.0.1, localhost
```

**Precedence**: environment variable > .env file > default > raises KeyError.

### Secret (Hidden in Tracebacks)

```python
secret = Secret("my-api-key")
repr(secret)   # Secret('**********')  -- safe in logs/tracebacks
str(secret)    # "my-api-key"          -- explicit str() to reveal
bool(secret)   # True                  -- empty string is False
```

### Prefixed Environment Variables

```python
import os
os.environ["MYAPP_DEBUG"] = "yes"

config = Config(env_prefix="MYAPP_")
debug = config("DEBUG")  # reads MYAPP_DEBUG -> "yes"
```

### Custom .env Encoding

```python
config = Config(".env", encoding="latin-1")
```

### Environment Protection (for Testing)

```python
from starlette.config import environ

# Must set BEFORE any config reads occur
environ["DEBUG"] = "TRUE"
environ["TESTING"] = "1"
# After a key is read by Config, writing to it raises EnvironError
```

---

## Lifespan (Startup / Shutdown)

### Basic Lifespan

```python
import contextlib
from starlette.applications import Starlette

@contextlib.asynccontextmanager
async def lifespan(app):
    # Startup: runs before the first request is served
    print("Starting up...")
    yield
    # Shutdown: runs after all connections close and background tasks complete
    print("Shutting down...")

app = Starlette(routes=routes, lifespan=lifespan)
```

### Typed Lifespan State (Share Resources with Requests)

```python
import contextlib
from typing import AsyncIterator, TypedDict

import httpx
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import PlainTextResponse
from starlette.routing import Route


class AppState(TypedDict):
    http_client: httpx.AsyncClient


@contextlib.asynccontextmanager
async def lifespan(app: Starlette) -> AsyncIterator[AppState]:
    async with httpx.AsyncClient() as client:
        yield {"http_client": client}


async def proxy(request: Request) -> PlainTextResponse:
    # Attribute-style access
    client = request.state.http_client
    # Dict-style access (type-safe when using Request[AppState])
    client = request.state["http_client"]
    resp = await client.get("https://httpbin.org/get")
    return PlainTextResponse(resp.text)


app = Starlette(routes=[Route("/proxy", proxy)], lifespan=lifespan)
```

**Shallow copy semantics**: state is shallow-copied per request. Mutable objects
(lists, dicts) are shared across concurrent requests; immutable values are isolated.

### Testing with Lifespan

```python
from starlette.testclient import TestClient

def test_with_lifespan():
    with TestClient(app) as client:  # triggers startup
        response = client.get("/proxy")
        assert response.status_code == 200
    # shutdown runs when context manager exits
```

---

## WebSockets

### Function-Based Handler

```python
from starlette.websockets import WebSocket, WebSocketDisconnect


async def websocket_handler(websocket: WebSocket) -> None:
    await websocket.accept()
    try:
        while True:
            text = await websocket.receive_text()
            await websocket.send_text(f"Echo: {text}")
    except WebSocketDisconnect:
        print("Client disconnected")
```

### Send and Receive Methods

```python
await websocket.send_text("hello")
await websocket.send_bytes(b"\x00\x01")
await websocket.send_json({"key": "value"})             # text frame (default)
await websocket.send_json({"key": "value"}, mode="binary")  # binary frame

text: str = await websocket.receive_text()
data: bytes = await websocket.receive_bytes()
obj: Any = await websocket.receive_json()
obj: Any = await websocket.receive_json(mode="binary")
```

### Async Iterators (Auto-Handle Disconnect)

```python
async def echo(websocket: WebSocket) -> None:
    await websocket.accept()
    async for message in websocket.iter_text():
        await websocket.send_text(f"Echo: {message}")
    # Loop exits cleanly on WebSocketDisconnect

# Also: websocket.iter_bytes(), websocket.iter_json()
```

### Subprotocol and Accept Headers

```python
await websocket.accept(
    subprotocol="graphql-ws",
    headers=[(b"x-request-id", b"abc123")],
)
```

### Rejection (Denial Response)

```python
from starlette.responses import JSONResponse

async def auth_ws(websocket: WebSocket) -> None:
    token = websocket.query_params.get("token")
    if not valid_token(token):
        await websocket.send_denial_response(
            JSONResponse({"error": "unauthorized"}, status_code=401)
        )
        return
    await websocket.accept()
    ...
```

### WebSocket Properties

Same as Request: `websocket.url`, `websocket.headers`, `websocket.query_params`,
`websocket.path_params`, `websocket.client`, `websocket.cookies`, `websocket.state`.

---

## Static Files

```python
from starlette.routing import Mount
from starlette.staticfiles import StaticFiles

routes = [
    Mount("/static", app=StaticFiles(directory="static"), name="static"),
]
```

### HTML Mode (SPA / Directory Index)

```python
Mount("/", app=StaticFiles(directory="public", html=True))
```

### Package Static Files

```python
StaticFiles(packages=["bootstrap4"])                      # "statics" subdir (default)
StaticFiles(packages=[("bootstrap4", "static")])          # custom subdir
StaticFiles(directory="static", packages=["bootstrap4"])  # combine
```

### All Options

```python
StaticFiles(
    directory="static",
    packages=None,
    html=False,            # serve index.html for directories
    check_dir=True,        # validate directory exists on startup
    follow_symlink=False,  # follow symbolic links
)
```

Handles ETag, If-None-Match (304), If-Modified-Since, Content-Type detection, path traversal prevention.

---

## Templates

```python
from starlette.requests import Request
from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates

templates = Jinja2Templates(directory="templates")


async def homepage(request: Request):
    return templates.TemplateResponse(request, "index.html", {"title": "Home"})


routes = [
    Route("/", homepage),
    Mount("/static", StaticFiles(directory="static"), name="static"),
]
```

**Requires**: `uv add jinja2`

### url_for in Templates

```html
<link href="{{ url_for('static', path='/css/style.css') }}" rel="stylesheet" />
<a href="{{ url_for('user_detail', username='tom') }}">Profile</a>
```

### Custom Filters

```python
templates = Jinja2Templates(directory="templates")
templates.env.filters["markdown"] = lambda text: markdown.markdown(text)
```

### Context Processors

```python
def global_context(request: Request) -> dict:
    return {"app_name": "MyApp", "current_user": request.user}

templates = Jinja2Templates(
    directory="templates",
    context_processors=[global_context],  # sync only, not async
)
```

### Custom Jinja2 Environment

```python
import jinja2

env = jinja2.Environment(loader=jinja2.FileSystemLoader("templates"), autoescape=True)
templates = Jinja2Templates(env=env)
```

When using `directory=`, autoescape is enabled by default for `.html`, `.htm`, `.xml`.

### Testing Templates

```python
def test_homepage():
    client = TestClient(app)
    response = client.get("/")
    assert response.template.name == "index.html"
    assert "title" in response.context
```

### Async Template Rendering Guidance

Jinja2 can render templates asynchronously, but keep templates free of I/O-heavy
logic whenever possible.

- Do database queries, API calls, and other I/O in the endpoint first.
- Pass fully prepared values into the template context.
- Use async rendering only when you deliberately need async template features,
  not as a substitute for endpoint logic.

---

## Authentication

### Backend Implementation

```python
import base64
import binascii

from starlette.authentication import (
    AuthCredentials, AuthenticationBackend, AuthenticationError, SimpleUser,
)
from starlette.middleware import Middleware
from starlette.middleware.authentication import AuthenticationMiddleware
from starlette.requests import Request


class BasicAuthBackend(AuthenticationBackend):
    async def authenticate(self, conn):
        if "Authorization" not in conn.headers:
            return None  # unauthenticated -- sets UnauthenticatedUser

        auth = conn.headers["Authorization"]
        try:
            scheme, credentials = auth.split()
            if scheme.lower() != "basic":
                return None
            decoded = base64.b64decode(credentials).decode("ascii")
        except (ValueError, UnicodeDecodeError, binascii.Error):
            raise AuthenticationError("Invalid basic auth credentials")

        username, _, password = decoded.partition(":")
        return AuthCredentials(["authenticated", "admin"]), SimpleUser(username)


middleware = [
    Middleware(AuthenticationMiddleware, backend=BasicAuthBackend()),
]
```

### Using Auth in Endpoints

```python
async def homepage(request: Request):
    if request.user.is_authenticated:
        return PlainTextResponse(f"Hello, {request.user.display_name}")
    return PlainTextResponse("Hello, anonymous")
```

### Checking Scopes Programmatically

```python
from starlette.authentication import has_required_scope

async def handler(request: Request):
    if has_required_scope(request, ["admin"]):
        ...
```

### @requires Decorator

```python
from starlette.authentication import requires

@requires("authenticated")
async def dashboard(request: Request):
    ...

@requires(["authenticated", "admin"])
async def admin_panel(request: Request):
    ...

@requires("authenticated", status_code=404)   # hide existence of page
async def hidden_page(request: Request):
    ...

@requires("authenticated", redirect="login")  # preserves ?next= for return URL
async def protected(request: Request):
    ...

# On class-based endpoints
class Dashboard(HTTPEndpoint):
    @requires("authenticated")
    async def get(self, request: Request):
        ...
```

For WebSockets, `@requires(..., status_code=404)` is not supported. Starlette
always uses `403 Forbidden` for denied WebSocket permissions. If you need a
custom rejection body for WebSockets, perform the check manually and use
`websocket.send_denial_response(...)`.

### Custom Auth Error Handler

```python
from starlette.responses import JSONResponse

def on_auth_error(request, exc):
    return JSONResponse({"error": str(exc)}, status_code=401)

Middleware(AuthenticationMiddleware, backend=BasicAuthBackend(), on_error=on_auth_error)
```

---

## Background Tasks

### Single Task

```python
from starlette.background import BackgroundTask
from starlette.responses import JSONResponse


async def send_welcome_email(to_address: str) -> None:
    ...


async def signup(request: Request) -> JSONResponse:
    data = await request.json()
    task = BackgroundTask(send_welcome_email, to_address=data["email"])
    return JSONResponse({"status": "ok"}, background=task)
```

### Multiple Tasks

```python
from starlette.background import BackgroundTasks


async def signup(request: Request) -> JSONResponse:
    data = await request.json()
    tasks = BackgroundTasks()
    tasks.add_task(send_welcome_email, to_address=data["email"])
    tasks.add_task(send_admin_notification, username=data["username"])
    tasks.add_task(log_signup, data=data)  # sync functions work too (run in threadpool)
    return JSONResponse({"status": "ok"}, background=tasks)
```

Tasks execute sequentially in order. If one raises an exception, subsequent tasks are skipped.
