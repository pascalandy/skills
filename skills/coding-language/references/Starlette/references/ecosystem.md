# Starlette Ecosystem

Third-party packages that extend Starlette, organized by what problem they solve.
Source: [third-party-packages.md](https://github.com/Kludex/starlette/blob/main/docs/third-party-packages.md)
and community contributions from the Starlette issue tracker.

---

## Auth & Security

| Package | What it does | Links |
|---|---|---|
| **Authlib** | OAuth and OpenID Connect client/server. The standard choice for social login and OAuth flows. | [GitHub](https://github.com/lepture/Authlib) [Docs](https://docs.authlib.org/en/latest/client/starlette.html) |
| **Imia** | Authentication framework with pluggable authenticators and login/logout flow. | [GitHub](https://github.com/alex-oleshkevich/imia) |
| **Starlette-Login** | User session management (login, logout, remember me). Modeled on Flask-Login. | [GitHub](https://github.com/jockerz/Starlette-Login) [Docs](https://starlette-login.readthedocs.io/en/stable/) |
| **Starlette OAuth2 API** | JWT-based auth middleware relying on an external auth provider. | [GitLab](https://gitlab.com/jorgecarleitao/starlette-oauth2-api) |
| **Starlette WTF** | WTForms integration with CSRF protection. Modeled on Flask-WTF. | [GitHub](https://github.com/muicss/starlette-wtf) |
| **Starlette DI** | Dependency injection with Scoped, Transient, and Singleton lifetimes (.NET Core-style). | [GitHub](https://github.com/daireto/starlette-di) |

## Sessions

| Package | What it does | Links |
|---|---|---|
| **Starsessions** | Pluggable session backends (Redis, database, file, etc.) replacing the built-in cookie-only SessionMiddleware. | [GitHub](https://github.com/alex-oleshkevich/starsessions) |

## WebSockets & Real-Time

| Package | What it does | Links |
|---|---|---|
| **ChannelBox** | Lightweight WebSocket broadcasting. Send messages to named channel groups. Persistent contributor to Starlette docs (5 PRs over multiple years). | [GitHub](https://github.com/Sobolev5/channel-box) |
| **Nejma** | WebSocket channel group management. Includes [nejma-chat](https://github.com/taoufik07/nejma-chat) demo app. | [GitHub](https://github.com/taoufik07/nejma) |
| **Fast Channels** | Django Channels-style consumer pattern for Starlette. Group broadcasting, cross-process messaging via Redis, async test framework. | [GitHub](https://github.com/huynguyengl99/fast-channels) |
| **sse-starlette** | Server-Sent Events support for Starlette. | [GitHub](https://github.com/sysid/sse-starlette) |

## Compression

| Package | What it does | Links |
|---|---|---|
| **Starlette Compress** | ZStd, Brotli, and GZip compression with sensible defaults. Born from the [OpenStreetMap-NG](https://github.com/Zaczero/openstreetmap-ng) project. | [GitHub](https://github.com/Zaczero/starlette-compress) |
| **Starlette Cramjam** | Brotli, gzip, and deflate compression with minimal dependencies. | [GitHub](https://github.com/developmentseed/starlette-cramjam) |

## Observability & Monitoring

| Package | What it does | Links |
|---|---|---|
| **Sentry** | Error tracking, performance monitoring, alerts. First-class Starlette integration. | [GitHub](https://github.com/getsentry/sentry-python) [Docs](https://docs.sentry.io/platforms/python/guides/starlette/) |
| **Apitally** | API analytics, request logging, and monitoring for REST APIs. | [GitHub](https://github.com/apitally/apitally-py) [Docs](https://docs.apitally.io/frameworks/starlette) |
| **Starlette Prometheus** | Prometheus metrics endpoint using the official Python client. | [GitHub](https://github.com/perdy/starlette-prometheus) |
| **Scout APM** | Application performance monitoring. | [GitHub](https://github.com/scoutapp/scout_apm_python) |

## API Documentation & Schemas

| Package | What it does | Links |
|---|---|---|
| **SpecTree** | Generate OpenAPI specs and validate requests/responses with type annotations. No YAML needed. | [GitHub](https://github.com/0b01001001/spectree) |
| **Starlette APISpec** | APISpec integration -- declare OpenAPI schemas in endpoint docstrings. | [GitHub](https://github.com/Woile/starlette-apispec) |
| **Apiman** | Swagger/OpenAPI integration with SwaggerUI and ReDoc. | [GitHub](https://github.com/strongbugman/apiman) |

## Request Handling

| Package | What it does | Links |
|---|---|---|
| **webargs-starlette** | Declarative request parsing and validation (querystring, JSON, form, headers, cookies) via type annotations. Built on [webargs](https://github.com/marshmallow-code/webargs). | [GitHub](https://github.com/sloria/webargs-starlette) |
| **Starlette Context** | Store and access per-request context data. Integrates with logging for x-request-id / x-correlation-id. | [GitHub](https://github.com/tomwojcik/starlette-context) |

## Admin & UI

| Package | What it does | Links |
|---|---|---|
| **Starlette-Admin** | Admin interface framework with Datatables, file handling, CSV/PDF/Excel export, multi-ORM support (SQLAlchemy, SQLModel, MongoEngine). Built with Tabler UI. [Live demo](https://starlette-admin-demo.jowilf.com/). | [GitHub](https://github.com/jowilf/starlette-admin) [Docs](https://jowilf.github.io/starlette-admin) |
| **Starception** | Beautiful exception page replacement for Starlette's default debug page. | [GitHub](https://github.com/alex-oleshkevich/starception) |

## Routing

| Package | What it does | Links |
|---|---|---|
| **DecoRouter** | FastAPI-style decorator routing for Starlette. | [GitHub](https://github.com/MrPigss/DecoRouter) |

## Deployment & Serverless

| Package | What it does | Links |
|---|---|---|
| **Mangum** | ASGI adapter for AWS Lambda & API Gateway. The standard for serverless Starlette on AWS. | [GitHub](https://github.com/erm/mangum) |
| **Vellox** | ASGI adapter for GCP Cloud Functions. | [GitHub](https://github.com/junah201/vellox) |

## Static Files & Resources

| Package | What it does | Links |
|---|---|---|
| **Starlette-StaticResources** | Mount Python [package resources](https://docs.python.org/3/library/importlib.resources.html) as static files (importlib.resources instead of filesystem paths). | [GitHub](https://github.com/DavidVentura/starlette-static-resources) |

## i18n

| Package | What it does | Links |
|---|---|---|
| **Starlette-Babel** | Translations, localization, and timezone support via Babel. | [GitHub](https://github.com/alex-oleshkevich/starlette_babel) |

## Compatibility

| Package | What it does | Links |
|---|---|---|
| **Starlette Bridge** | Backwards-compatible on_startup/on_shutdown event support (internally converts to lifespan). For packages that haven't migrated yet. | [GitHub](https://github.com/tarsil/starlette-bridge) [Docs](https://starlette-bridge.tarsild.io/) |

---

## Frameworks Built on Starlette

These are full web frameworks that use Starlette as their ASGI foundation.

| Framework | Focus | Links |
|---|---|---|
| **FastAPI** | High-performance API framework with automatic OpenAPI docs, Pydantic validation, dependency injection. The most widely used Starlette-based framework. | [GitHub](https://github.com/tiangolo/fastapi) [Docs](https://fastapi.tiangolo.com/) |
| **Flama** | Data-science oriented framework for deploying ML models as APIs. Turn ML models into auto-documented async APIs in one line. | [GitHub](https://github.com/vortico/flama) [Docs](https://flama.dev/) |
| **Ellar** | NestJS-inspired ASGI framework with OOP patterns, built on Starlette + Pydantic + injector. | [GitHub](https://github.com/eadwinCode/ellar) [Docs](https://eadwincode.github.io/ellar/) |
| **Xpresso** | Flexible framework built on Starlette, Pydantic, and [di](https://github.com/adriangb/di). | [GitHub](https://github.com/adriangb/xpresso) [Docs](https://xpresso-api.dev/) |
| **Responder** | Flask-style async web framework with YAML support and OpenAPI generation. | [GitHub](https://github.com/taoufik07/responder) [Docs](https://python-responder.org/en/latest/) |
| **Dark Star** | File-path based routing with htmx support. Minimal code to get HTML to the browser. | [GitHub](https://github.com/lllama/dark-star) [Docs](https://lllama.github.io/dark-star) |
| **Starlette-apps** | Roll-your-own framework with a Django-GDAPS-style app system. | [GitHub](https://github.com/yourlabs/starlette-apps) |
| **Shiny for Python** | Reactive web apps using Starlette and asyncio. Automatic state management and re-rendering. By Posit (RStudio). | [GitHub](https://github.com/posit-dev/py-shiny) [Docs](https://shiny.posit.co/py/) |
| **Greppo** | Geospatial dashboards and web-applications with data mutation hooks. | [GitHub](https://github.com/greppo-io/greppo) [Docs](https://docs.greppo.io/) |
