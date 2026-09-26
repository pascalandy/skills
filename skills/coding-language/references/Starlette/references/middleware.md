# Middleware

## Declaring Middleware

```python
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

middleware = [
    # Outermost -- processed first on request, last on response
    Middleware(TrustedHostMiddleware, allowed_hosts=["example.com", "*.example.com"]),
    Middleware(HTTPSRedirectMiddleware),
    Middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]),
    Middleware(GZipMiddleware, minimum_size=1000, compresslevel=9),
    Middleware(SessionMiddleware, secret_key="use-a-real-secret-here"),
    # Innermost
]

app = Starlette(routes=routes, middleware=middleware)
```

**Execution order**: `ServerErrorMiddleware` (auto) -> user middleware top-to-bottom -> `ExceptionMiddleware` (auto) -> Router -> Endpoint.

---

## Built-in Middleware

### CORSMiddleware

```python
Middleware(CORSMiddleware,
    allow_origins=["https://example.com"],
    allow_origin_regex=r"https://.*\.example\.org",  # use tight patterns, not ".*"
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
    allow_credentials=True,
    allow_private_network=True,   # Private Network Access (PNA)
    expose_headers=["X-Request-Id"],
    max_age=600,                  # preflight cache in seconds
)
```

To apply CORS headers to error responses too, wrap outside Starlette:

```python
app = Starlette(routes=routes)
app = CORSMiddleware(app=app, allow_origins=["*"])
```

**Warning**: Overly permissive `allow_origin_regex` (e.g., `".*"`) can allow
any origin. Always use fullmatch patterns like `r"https://.*\.example\.org"`.

### SessionMiddleware

```python
Middleware(SessionMiddleware,
    secret_key="use-a-real-secret",  # required
    session_cookie="session",         # cookie name
    max_age=14 * 24 * 60 * 60,       # 2 weeks; None = browser session cookie
    same_site="lax",                  # "lax" | "strict" | "none"
    path="/",
    https_only=False,                 # True sets Secure flag
    domain=None,                      # ".example.com"
)
```

Session cookies are always HttpOnly (not accessible from JavaScript).
The `Set-Cookie` header is only sent when the session is modified, not on read-only access.

```python
async def handler(request: Request):
    request.session["user"] = "alice"           # set
    username = request.session.get("user")      # get
    request.session.pop("user", None)           # remove
    request.session.clear()                     # clear all
```

**Requires**: `uv add itsdangerous`

### GZipMiddleware

```python
Middleware(GZipMiddleware,
    minimum_size=500,     # skip compression below this (bytes)
    compresslevel=9,      # 1 = fastest, 9 = smallest
)
```

Skips compression when: Content-Encoding already set, Content-Type is `text/event-stream`, or response uses `http.response.pathsend`.

### TrustedHostMiddleware

```python
Middleware(TrustedHostMiddleware,
    allowed_hosts=["example.com", "*.example.com"],
    www_redirect=True,  # redirect example.com -> www.example.com
)
```

### HTTPSRedirectMiddleware

```python
Middleware(HTTPSRedirectMiddleware)
# http -> https, ws -> wss (307 Temporary Redirect)
```

---

## Custom Middleware

### BaseHTTPMiddleware

```python
import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class TimingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        start = time.time()
        response = await call_next(request)
        response.headers["X-Process-Time"] = f"{time.time() - start:.4f}"
        return response
```

With constructor parameters:

```python
class CustomHeaderMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, header_value: str = "default"):
        super().__init__(app)
        self.header_value = header_value

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        response.headers["X-Custom"] = self.header_value
        return response

Middleware(CustomHeaderMiddleware, header_value="production")
```

**Caveat**: BaseHTTPMiddleware prevents `contextvars.ContextVar` changes from
propagating upward through the middleware stack. Use pure ASGI middleware if you
need contextvar propagation.

### Pure ASGI Middleware (Maximum Control)

```python
from starlette.types import ASGIApp, Message, Receive, Scope, Send


class PureASGIMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_wrapper(message: Message) -> None:
            if message["type"] == "http.response.start":
                from starlette.datastructures import MutableHeaders
                headers = MutableHeaders(scope=message)
                headers.append("X-Custom", "value")
            await send(message)

        await self.app(scope, receive, send_wrapper)
```

**Key patterns for pure ASGI middleware**:

Wrap `receive` to inspect/modify request body:
```python
async def __call__(self, scope, receive, send):
    if scope["type"] != "http":
        await self.app(scope, receive, send)
        return

    body_size = 0

    async def counting_receive():
        nonlocal body_size
        message = await receive()
        body_size += len(message.get("body", b""))
        return message

    await self.app(scope, counting_receive, send)
```

Wrap `send` to inspect/modify response:
```python
async def __call__(self, scope, receive, send):
    if scope["type"] != "http":
        await self.app(scope, receive, send)
        return

    async def send_with_headers(message):
        if message["type"] == "http.response.start":
            from starlette.datastructures import MutableHeaders
            headers = MutableHeaders(scope=message)
            headers["X-Added"] = "value"
        await send(message)

    await self.app(scope, receive, send_with_headers)
```

Short-circuit with an early response:
```python
async def __call__(self, scope, receive, send):
    if scope["type"] == "http" and URL(scope=scope).path == "/blocked":
        response = PlainTextResponse("Blocked", status_code=403)
        await response(scope, receive, send)
        return
    await self.app(scope, receive, send)
```

Inject data into scope for downstream access:
```python
import uuid

async def __call__(self, scope, receive, send):
    scope["request_id"] = str(uuid.uuid4())
    await self.app(scope, receive, send)
```

**Statelessness rule**: per-connection state must live in `__call__`, not on `self`.

---

## Middleware on Individual Routes

```python
routes = [
    Route("/compressed", handler, middleware=[Middleware(GZipMiddleware)]),
    Mount("/api", routes=api_routes, middleware=[Middleware(AuthMiddleware)]),
]
router = Router(routes=routes, middleware=[Middleware(LoggingMiddleware)])
```

Route-level middleware is NOT wrapped in `ExceptionMiddleware` -- exceptions
propagate directly.
