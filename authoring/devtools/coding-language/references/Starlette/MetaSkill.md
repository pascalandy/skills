---
name: starlette
description: >
  Build, debug, and extend Starlette applications and Starlette-powered internals. Use this
  skill when the user mentions Starlette directly, needs routing/requests/responses,
  middleware, WebSockets, templates, static files, authentication, sessions, background
  tasks, testing, OpenAPI schemas, thread-pool behavior, or raw ASGI toolkit patterns built
  from Starlette primitives. Also use this skill when the user is working on FastAPI
  internals, because FastAPI is built on Starlette. Prefer more framework-specific skills
  only when the task is primarily about another framework's higher-level conventions.
---

# Starlette Reference + Agent Playbook

Starlette is a lightweight ASGI framework/toolkit for async web services in Python.
Requires Python `>=3.10`. Core dependency: `anyio` (supports both `asyncio` and `trio`).

This bundle is intended to help an AI agent handle both:

- Starlette as a full web framework.
- Starlette as a lower-level ASGI toolkit reused inside projects like FastAPI.

Version note:

- This skill was audited against the official `starlette.dev` docs and release notes on
  `2026-03-27`.
- Official release surfaces were not fully aligned at audit time: `starlette.dev`
  release notes listed `1.0.0rc1` on `February 23, 2026`, while stable 0.x releases were
  still documented in the same stream.
- Before relying on release-specific behavior, verify the installed Starlette version in the
  target project and check the release notes for that exact version.

### Bundled references

Read these when you need full parameter details, advanced patterns, or edge cases.

| File | When to read it |
|---|---|
| `references/http.md` | Routing details (path convertors, Mount, Host, reverse URLs), Request properties and body access, all Response types and cookies, class-based Endpoints, exception handling. |
| `references/middleware.md` | Built-in middleware (CORS, sessions, gzip, trusted host, HTTPS redirect) with all parameters. BaseHTTPMiddleware caveats. Pure ASGI middleware patterns. Route-level middleware. |
| `references/features.md` | Configuration (.env, Secret, prefix). Lifespan (typed state, shallow copy). WebSockets (send/receive, iterators, denial). Static files. Templates (Jinja2, filters, context processors). Authentication (backend, @requires, scopes). Background tasks. |
| `references/testing.md` | TestClient (HTTP, WebSocket, lifespan, error responses). Async testing with httpx. Backend selection (asyncio/trio). |
| `references/internals.md` | Data structures (URL, Headers, QueryParams, MultiDict, State, FormData, URLPath, Secret). Concurrency utilities. Status codes. API schemas (OpenAPI). WSGI compatibility. Common patterns (REST API, SSE, file upload, multi-tenant). |
| `references/ecosystem.md` | Third-party packages: auth, WebSocket, compression, monitoring, admin, deployment, and frameworks built on Starlette. |

---

## Start Here

Choose the smallest useful slice before reading the full bundle:

- Building or modifying HTTP routes, requests, responses, cookies, endpoints, or exception
  handlers: start with `references/http.md`.
- Working on middleware, FastAPI internals, request/response interception, or ASGI flow:
  start with `references/middleware.md`, then `references/http.md`.
- Building templates, sessions, auth, WebSockets, static files, background tasks, or
  lifespan-managed resources: start with `references/features.md`.
- Writing tests or debugging client behavior: start with `references/testing.md`.
- Debugging thread-pool behavior, schema generation, status codes, WSGI migration, or
  reusable Starlette data structures: start with `references/internals.md`.
- Choosing third-party packages or deployment adapters: start with
  `references/ecosystem.md`.

## Common Use Cases

Use these as starting patterns when the user asks for a project or feature:

- JSON API or admin backend: Quick Start, Application Scaffold, `references/http.md`,
  `references/testing.md`.
- HTML app with templates, static files, sessions, and login: Application Scaffold,
  `references/features.md`, `references/testing.md`.
- WebSocket notifications/chat/realtime dashboard: Application Scaffold,
  `references/features.md`, `references/testing.md`.
- FastAPI internals, middleware bugs, or raw request/response behavior:
  `references/middleware.md`, `references/http.md`, `references/internals.md`.
- Server-sent events, long polling, or streaming downloads: `references/http.md`,
  `references/internals.md`.
- Multi-tenant or host-based routing: `references/http.md`, `references/internals.md`.
- Serverless or adapter-based deployment: `references/ecosystem.md`.

## Version And Security Hygiene

When the task touches file serving, multipart parsing, uploads, or static files:

- Check the installed Starlette version before copying examples blindly.
- Prefer current defaults and documented safety limits such as `request.form(...)`
  bounds.
- Be cautious with `FileResponse`, `StaticFiles`, and multipart parsing in older versions,
  because Starlette has shipped recent security fixes in those areas.

---

## Quick Start

```bash
# Idempotent: only inits if pyproject.toml is missing
[ -f myapp/pyproject.toml ] || uv init myapp
cd myapp
uv add starlette uvicorn
```

Create `app.py`:

```python
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route


async def homepage(request: Request) -> JSONResponse:
    return JSONResponse({"hello": "world"})


app = Starlette(routes=[
    Route("/", homepage),
])
```

Run:

```bash
uv run uvicorn app:app --host 127.0.0.1 --port 8000 --reload
```

Both sync and async endpoint functions are supported. Sync functions automatically
run in a thread pool so they don't block the event loop:

```python
def sync_homepage(request: Request) -> JSONResponse:
    return JSONResponse({"sync": True})
```

---

## Application Scaffold

```python
import contextlib
from typing import AsyncIterator, TypedDict

import httpx
from starlette.applications import Starlette
from starlette.config import Config
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, PlainTextResponse
from starlette.routing import Mount, Route, WebSocketRoute
from starlette.staticfiles import StaticFiles
from starlette.websockets import WebSocket

config = Config(".env")
DEBUG = config("DEBUG", cast=bool, default=False)
SECRET_KEY = config("SECRET_KEY", default="change-me-in-production")


class AppState(TypedDict):
    http_client: httpx.AsyncClient


@contextlib.asynccontextmanager
async def lifespan(app: Starlette) -> AsyncIterator[AppState]:
    async with httpx.AsyncClient() as client:
        yield {"http_client": client}


async def homepage(request: Request) -> PlainTextResponse:
    return PlainTextResponse("Hello, world!")


async def user_detail(request: Request) -> PlainTextResponse:
    username = request.path_params["username"]
    return PlainTextResponse(f"Hello, {username}!")


async def websocket_endpoint(websocket: WebSocket) -> None:
    await websocket.accept()
    await websocket.send_text("Connected!")
    await websocket.close()


routes = [
    Route("/", homepage),
    Route("/users/{username}", user_detail),
    WebSocketRoute("/ws", websocket_endpoint),
    Mount("/static", StaticFiles(directory="static"), name="static"),
]

middleware = [
    Middleware(CORSMiddleware, allow_origins=["*"]),
    Middleware(SessionMiddleware, secret_key=SECRET_KEY),
]

app = Starlette(
    debug=DEBUG,
    routes=routes,
    middleware=middleware,
    lifespan=lifespan,
)
```

### Dynamic Registration

```python
app.add_middleware(CORSMiddleware, allow_origins=["*"])
app.add_route("/health", health_check, methods=["GET"])
app.add_exception_handler(404, custom_404_handler)
app.mount("/static", StaticFiles(directory="static"), name="static")
```

### Application State

```python
app.state.ADMIN_EMAIL = "admin@example.org"

async def homepage(request: Request) -> PlainTextResponse:
    admin = request.app.state.ADMIN_EMAIL
    return PlainTextResponse(f"Admin: {admin}")
```

---

## Quick Reference

Essential patterns for each feature area. For full details, parameter lists,
and edge cases, read the corresponding reference file.

### Routing -> `references/http.md`

```python
from starlette.routing import Route, Mount, WebSocketRoute, Host, Router

Route("/users/{user_id:int}", handler, methods=["GET", "POST"])
Mount("/api", routes=[...])
WebSocketRoute("/ws", ws_handler)
# Path convertors: str (default), int, float, uuid, path
# First match wins -- put specific routes before parameterized ones
url = request.url_for("user_detail", username="tom")
```

### Requests -> `references/http.md`

```python
request.method                        # "GET"
request.url.path                      # "/users/1"
request.headers["content-type"]       # case-insensitive
request.query_params.getlist("tag")   # multi-value
request.path_params["user_id"]        # from route convertor
request.cookies["session"]            # dict
body = await request.body()           # bytes
data = await request.json()           # parsed JSON
async with request.form() as form:    # requires: uv add python-multipart
    upload = form["file"]             # UploadFile
```

### Responses -> `references/http.md`

```python
from starlette.responses import (
    PlainTextResponse, HTMLResponse, JSONResponse,
    RedirectResponse, StreamingResponse, FileResponse,
)

JSONResponse({"key": "value"}, status_code=200)
RedirectResponse(url="/new", status_code=301)
StreamingResponse(async_generator(), media_type="text/event-stream")
FileResponse("report.pdf")
response.set_cookie(key="session", value="abc", httponly=True, samesite="lax")
```

### Endpoints (Class-Based) -> `references/http.md`

```python
from starlette.endpoints import HTTPEndpoint

class Users(HTTPEndpoint):
    async def get(self, request): ...
    async def post(self, request): ...
# Unhandled methods -> 405. Pass CLASS to Route, not instance.
```

### Middleware -> `references/middleware.md`

```python
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware  # requires: uv add itsdangerous
from starlette.middleware.gzip import GZipMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware

middleware = [Middleware(CORSMiddleware, allow_origins=["*"])]
# Execution order: ServerErrorMiddleware -> user middleware (top-to-bottom) -> ExceptionMiddleware -> Router
# Custom: subclass BaseHTTPMiddleware or write pure ASGI (see reference)
```

### Exception Handling -> `references/http.md`

```python
from starlette.exceptions import HTTPException, WebSocketException

raise HTTPException(status_code=404, detail="Not found")
# Register handlers: exception_handlers={404: handler, HTTPException: handler}
```

### WebSockets -> `references/features.md`

```python
from starlette.websockets import WebSocket, WebSocketDisconnect

async def handler(websocket: WebSocket):
    await websocket.accept()
    async for msg in websocket.iter_text():
        await websocket.send_text(f"Echo: {msg}")
```

### Static Files -> `references/features.md`

```python
from starlette.staticfiles import StaticFiles
Mount("/static", app=StaticFiles(directory="static"), name="static")
# HTML mode (SPA): StaticFiles(directory="public", html=True)
```

### Templates -> `references/features.md`

```python
from starlette.templating import Jinja2Templates  # requires: uv add jinja2
templates = Jinja2Templates(directory="templates")
return templates.TemplateResponse(request, "index.html", {"title": "Home"})
# url_for() is auto-available in templates
```

### Authentication -> `references/features.md`

```python
from starlette.authentication import requires
from starlette.middleware.authentication import AuthenticationMiddleware

@requires("authenticated")
async def protected(request): ...
# Implement AuthenticationBackend.authenticate() -> (AuthCredentials, BaseUser) or None
```

### Background Tasks -> `references/features.md`

```python
from starlette.background import BackgroundTask, BackgroundTasks

task = BackgroundTask(send_email, to=email)
return JSONResponse({"ok": True}, background=task)
# Multiple: tasks = BackgroundTasks(); tasks.add_task(fn, arg); sequential execution
```

### Configuration -> `references/features.md`

```python
from starlette.config import Config
from starlette.datastructures import Secret

config = Config(".env")
DEBUG = config("DEBUG", cast=bool, default=False)
SECRET = config("SECRET_KEY", cast=Secret)
# Precedence: env var > .env > default > KeyError
```

### Lifespan -> `references/features.md`

```python
import contextlib

@contextlib.asynccontextmanager
async def lifespan(app):
    yield {"http_client": client}  # available as request.state.http_client

app = Starlette(routes=routes, lifespan=lifespan)
```

### Testing -> `references/testing.md`

```python
from starlette.testclient import TestClient  # requires: uv add httpx

client = TestClient(app)
response = client.get("/")
assert response.status_code == 200

with client.websocket_connect("/ws") as ws:
    ws.send_text("hello")
    assert ws.receive_text() == "Echo: hello"
```

### Toolkit Mode / FastAPI Internals -> `references/http.md`, `references/middleware.md`

```python
from starlette.requests import Request
from starlette.responses import PlainTextResponse


async def app(scope, receive, send):
    assert scope["type"] == "http"
    request = Request(scope, receive)
    response = PlainTextResponse(f"{request.method} {request.url.path}")
    await response(scope, receive, send)
```

---

## Python Tooling Policy

This skill intentionally prefers `uv` for Python package management and command
execution. The goal is to stop agents from defaulting to raw `python3` and
`pip` commands when setting up or running Starlette projects.

Treat this as agent operating guidance, not a claim that every Starlette
project everywhere must use `uv`.

Default behavior:

- Use `uv` for new Starlette projects.
- Prefer `uv run ...` over `python3 ...`.
- Prefer `uv add ...` over `pip install ...`.
- Prefer `uv sync` when the project is already using `uv`.
- If the target repository already has an explicit Python workflow
  (`poetry`, `pdm`, `hatch`, `pip-tools`, `nix`, CI-pinned scripts, etc.),
  preserve that workflow instead of forcing a migration to `uv`.

Why this skill defaults to `uv`:

- It matches Starlette's own current development workflow.
- It avoids ad-hoc interpreter and virtualenv handling.
- It gives agents a consistent install/run pattern across tasks.

Use `uv` instead of `pip` or `python3` when there is no stronger project-level
tooling convention:

```bash
uv init myproject && cd myproject
uv add starlette uvicorn
uv add starlette[full]            # all optional deps
uv run uvicorn app:app --host 127.0.0.1 --port 8000 --reload
uv run pytest
```

- **Matches upstream.** Starlette's `scripts/install` is `uv sync --frozen`.
  Their test runner is `uv run coverage run -m pytest`.
- **Speed.** `uv add starlette[full]` resolves and installs in under a second.
- **Deterministic lockfile.** `uv.lock` pins exact versions across all platforms.
- **Implicit venv management.** `uv run` creates and reuses a venv automatically.
- **Full compatibility.** uv reads standard `pyproject.toml` and `requirements.txt`.

On macOS and Linux, avoid calling `python3` directly unless an existing project
workflow explicitly requires it. Prefer `uv run`, which manages the interpreter
and virtual environment for you.

---

## Dependencies

| Feature | Required Package |
|---|---|
| Core | `anyio>=3.6.2,<5` |
| TestClient | `httpx>=0.27.0,<0.29.0` |
| Templates | `jinja2` |
| Form parsing | `python-multipart>=0.0.18` |
| Sessions | `itsdangerous` |
| Schema YAML | `pyyaml` |
| Python | `>=3.10` |
| Async backends | `asyncio` (default), `trio` |
| Install all | `uv add starlette[full]` |

## ASGI Servers

### Development

```bash
uv run uvicorn myapp:app --host 127.0.0.1 --port 8000 --reload
```

### Production

```bash
# Uvicorn with multiple workers
uv run uvicorn myapp:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 4 \
  --log-level info

# Alternative servers (same explicit-binding principle)
uv run daphne --bind 0.0.0.0 --port 8000 myapp:app
uv run hypercorn --bind 0.0.0.0:8000 myapp:app
```

### Programmatic start

Useful as a script entrypoint or when wrapping the server in a CLI tool:

```python
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
```

### Discovering flags

Each server supports `--help` for the full flag list:

```bash
uv run uvicorn --help
uv run daphne --help
uv run hypercorn --help
```
