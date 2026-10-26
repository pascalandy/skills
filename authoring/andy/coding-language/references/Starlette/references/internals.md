# Internals: Data Structures, Concurrency, Status Codes, Schemas, WSGI, Patterns

## Table of Contents

- Data structures
- Concurrency utilities
- Status codes
- API schemas
- Database and GraphQL
- WSGI compatibility
- Common patterns

## Data Structures

### URL

```python
from starlette.datastructures import URL

url = URL("https://user:pass@example.com:8080/path?q=1#frag")
url.scheme       # "https"
url.hostname     # "example.com"
url.port         # 8080
url.path         # "/path"
url.query        # "q=1"
url.fragment     # "frag"
url.username     # "user"
url.password     # "pass"
url.netloc       # "user:pass@example.com:8080"
url.is_secure    # True (https or wss)

# Immutable modifications (return new URL)
url.replace(hostname="other.com", port=443)
url.include_query_params(page=2, sort="name")
url.replace_query_params(q="new-search")
url.remove_query_params(["q", "page"])
```

### Headers / MutableHeaders

```python
from starlette.datastructures import Headers, MutableHeaders

headers = Headers({"content-type": "text/html", "x-custom": "value"})
headers["Content-Type"]       # case-insensitive: "text/html"
headers.getlist("x-custom")   # ["value"]

mutable = headers.mutablecopy()
mutable["X-New"] = "val"
mutable.append("X-Multi", "a")
mutable.add_vary_header("Accept-Encoding")
mutable |= {"X-Extra": "merged"}
del mutable["X-New"]
```

### QueryParams

```python
from starlette.datastructures import QueryParams

params = QueryParams("page=1&tag=python&tag=async")
params["page"]            # "1"
params.getlist("tag")     # ["python", "async"]
params.multi_items()      # [("page", "1"), ("tag", "python"), ("tag", "async")]
str(params)               # "page=1&tag=python&tag=async"
```

### MultiDict / ImmutableMultiDict

```python
from starlette.datastructures import MultiDict

md = MultiDict([("key", "a"), ("key", "b"), ("other", "c")])
md["key"]            # "a" (first value)
md.getlist("key")    # ["a", "b"]
md.multi_items()     # all pairs including duplicates
md.append("key", "d")
md.poplist("key")    # ["a", "b", "d"]
```

### State

```python
from starlette.datastructures import State

state = State()
state.counter = 0       # attribute access
state["counter"] = 1    # dict access
del state.counter
len(state)              # 0
```

### FormData

```python
from starlette.datastructures import FormData, UploadFile

# Immutable multi-dict of str | UploadFile values
# Returned by request.form()
form = FormData([("field", "value"), ("file", upload_file_instance)])
form["field"]         # "value"
form.getlist("field") # ["value"]
form.multi_items()    # all key-value pairs
await form.close()    # closes all UploadFile instances
```

### URLPath

```python
from starlette.datastructures import URLPath

# Returned by url_path_for() -- a str subclass with extra metadata
path = URLPath("/users/tom", protocol="http", host="example.com")
str(path)                                      # "/users/tom"
path.make_absolute_url("https://example.com")  # URL("https://example.com/users/tom")
```

### Secret / CommaSeparatedStrings / Address

```python
from starlette.datastructures import Secret, CommaSeparatedStrings, Address

secret = Secret("key")              # repr hides value, str reveals it
hosts = CommaSeparatedStrings("a, b, c")  # list(hosts) == ["a", "b", "c"]
addr = Address(host="127.0.0.1", port=8000)
```

---

## Concurrency Utilities

### run_in_threadpool

```python
from starlette.concurrency import run_in_threadpool

async def handler(request: Request):
    # Run blocking code without blocking the event loop
    result = await run_in_threadpool(blocking_function, arg1, arg2)
    return JSONResponse({"result": result})
```

### iterate_in_threadpool

```python
from starlette.concurrency import iterate_in_threadpool

async def handler(request: Request):
    sync_iter = range(100)
    async for item in iterate_in_threadpool(sync_iter):
        ...
```

### Thread Pool Tuning

Sync endpoints, FileResponse, UploadFile, and sync BackgroundTasks all run in
anyio's default thread pool (40 concurrent threads).

```python
import anyio.to_thread

limiter = anyio.to_thread.current_default_thread_limiter()
limiter.total_tokens = 100  # increase for high-concurrency sync workloads
```

---

## Status Codes

```python
from starlette import status

# HTTP
status.HTTP_200_OK                     # 200
status.HTTP_201_CREATED                # 201
status.HTTP_204_NO_CONTENT             # 204
status.HTTP_301_MOVED_PERMANENTLY      # 301
status.HTTP_302_FOUND                  # 302
status.HTTP_304_NOT_MODIFIED           # 304
status.HTTP_307_TEMPORARY_REDIRECT     # 307
status.HTTP_308_PERMANENT_REDIRECT     # 308
status.HTTP_400_BAD_REQUEST            # 400
status.HTTP_401_UNAUTHORIZED           # 401
status.HTTP_403_FORBIDDEN              # 403
status.HTTP_404_NOT_FOUND              # 404
status.HTTP_405_METHOD_NOT_ALLOWED     # 405
status.HTTP_409_CONFLICT               # 409
status.HTTP_422_UNPROCESSABLE_CONTENT  # 422
status.HTTP_429_TOO_MANY_REQUESTS      # 429
status.HTTP_500_INTERNAL_SERVER_ERROR  # 500

# WebSocket
status.WS_1000_NORMAL_CLOSURE         # 1000
status.WS_1001_GOING_AWAY             # 1001
status.WS_1008_POLICY_VIOLATION       # 1008
status.WS_1011_INTERNAL_ERROR         # 1011
```

---

## API Schemas (OpenAPI)

```python
from starlette.requests import Request
from starlette.routing import Route
from starlette.schemas import SchemaGenerator

schemas = SchemaGenerator(
    {"openapi": "3.0.0", "info": {"title": "My API", "version": "1.0"}}
)


async def list_users(request: Request):
    """
    responses:
      200:
        description: A list of users.
        examples:
          [{"username": "tom"}]
    """
    ...


async def openapi_schema(request: Request):
    return schemas.OpenAPIResponse(request=request)


routes = [
    Route("/users", list_users, methods=["GET"]),
    Route("/schema", openapi_schema, include_in_schema=False),
]
```

**Requires**: `uv add pyyaml`

Schema content is parsed from YAML in endpoint docstrings (after an optional `---` separator).

Generate a schema directly when you need to export or inspect it without serving
an endpoint:

```python
schema = schemas.get_schema(routes=app.routes)
print(schema["paths"])
```

Typical export pattern:

```python
import yaml

schema = schemas.get_schema(routes=app.routes)
print(yaml.dump(schema, default_flow_style=False))
```

---

## Database and GraphQL

Starlette is database-agnostic. Recommended async-compatible libraries:

- **SQLAlchemy** 2.0+ (native async support)
- **SQLModel** (SQLAlchemy + Pydantic)
- **Tortoise ORM** (Django-inspired async ORM)
- **Piccolo** (async ORM and query builder)

Use the lifespan handler to manage database connection pools.

GraphQL support was removed in Starlette 0.17. Use third-party libraries:
**Strawberry**, **Ariadne**, **starlette-graphene3**, or **tartiflette-asgi**.

---

## WSGI Compatibility (Deprecated)

```python
from starlette.middleware.wsgi import WSGIMiddleware
from starlette.routing import Mount


def legacy_wsgi_app(environ, start_response):
    start_response("200 OK", [("Content-Type", "text/plain")])
    return [b"Hello from WSGI"]


routes = [
    Mount("/legacy", app=WSGIMiddleware(legacy_wsgi_app)),
]
```

`WSGIMiddleware` is deprecated in Starlette 1.0. Migrate to the `a2wsgi` package.

---

## Common Patterns

### REST API

```python
import contextlib

from starlette.applications import Starlette
from starlette.endpoints import HTTPEndpoint
from starlette.exceptions import HTTPException
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

ITEMS: dict[int, dict] = {}


@contextlib.asynccontextmanager
async def lifespan(app):
    ITEMS[1] = {"id": 1, "name": "Widget"}
    yield
    ITEMS.clear()


class ItemList(HTTPEndpoint):
    async def get(self, request: Request) -> JSONResponse:
        return JSONResponse(list(ITEMS.values()))

    async def post(self, request: Request) -> JSONResponse:
        data = await request.json()
        item_id = max(ITEMS.keys(), default=0) + 1
        ITEMS[item_id] = {"id": item_id, **data}
        return JSONResponse(ITEMS[item_id], status_code=201)


class ItemDetail(HTTPEndpoint):
    async def get(self, request: Request) -> JSONResponse:
        item_id = request.path_params["item_id"]
        if item_id not in ITEMS:
            raise HTTPException(status_code=404, detail="Item not found")
        return JSONResponse(ITEMS[item_id])

    async def put(self, request: Request) -> JSONResponse:
        item_id = request.path_params["item_id"]
        if item_id not in ITEMS:
            raise HTTPException(status_code=404, detail="Item not found")
        data = await request.json()
        ITEMS[item_id] = {"id": item_id, **data}
        return JSONResponse(ITEMS[item_id])

    async def delete(self, request: Request) -> JSONResponse:
        item_id = request.path_params["item_id"]
        if item_id not in ITEMS:
            raise HTTPException(status_code=404, detail="Item not found")
        del ITEMS[item_id]
        return JSONResponse({"deleted": item_id})


routes = [
    Route("/items", ItemList),
    Route("/items/{item_id:int}", ItemDetail),
]

app = Starlette(
    routes=routes,
    middleware=[Middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"])],
    lifespan=lifespan,
)
```

### Server-Sent Events (SSE)

```python
import asyncio

from starlette.requests import Request
from starlette.responses import StreamingResponse


async def event_generator():
    count = 0
    while True:
        count += 1
        yield f"data: {count}\n\n"
        await asyncio.sleep(1)


async def sse_endpoint(request: Request) -> StreamingResponse:
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
```

### File Upload with Background Processing

```python
from starlette.background import BackgroundTask
from starlette.requests import Request
from starlette.responses import JSONResponse


async def process_file(content: bytes, filename: str) -> None:
    ...


async def upload(request: Request) -> JSONResponse:
    async with request.form() as form:
        file = form["file"]
        content = await file.read()
        filename = file.filename

    task = BackgroundTask(process_file, content=content, filename=filename)
    return JSONResponse(
        {"filename": filename, "size": len(content)},
        background=task,
    )
```

### Multi-Tenant with Host Routing

```python
from starlette.requests import Request
from starlette.responses import PlainTextResponse
from starlette.routing import Host, Route, Router


async def tenant_home(request: Request) -> PlainTextResponse:
    tenant = request.path_params["tenant"]
    return PlainTextResponse(f"Welcome to {tenant}")


routes = [
    Host("{tenant}.myapp.com", app=Router(routes=[
        Route("/", tenant_home),
    ]), name="tenant"),
]
```
