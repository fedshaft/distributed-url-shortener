# Distributed URL Shortener

[![CI](https://github.com/fedshaft/distributed-url-shortener/actions/workflows/ci.yml/badge.svg)](https://github.com/fedshaft/distributed-url-shortener/actions/workflows/ci.yml)

A high-performance URL shortening service built with **FastAPI**, **PostgreSQL** (asyncpg, raw SQL) and **Redis**. Redirects are served from a Redis cache, and click analytics are streamed out-of-band through **Redis Streams** to a background consumer, keeping the redirect path fast.

**Live demo:** https://url-shortener-jsii.onrender.com · **Try it in the browser:** https://url-shortener-jsii.onrender.com/docs

> Hosted on Render's free tier: the first request after idle can take ~30s while the service wakes up.

## Try it

```bash
# Shorten a URL
curl -X POST https://url-shortener-jsii.onrender.com/shorten \
  -H "Content-Type: application/json" \
  -d '{"url": "https://github.com/fedshaft/distributed-url-shortener"}'
# -> {"short_code": "1b1RAU"}

# Follow the short link (302 redirect)
curl -i https://url-shortener-jsii.onrender.com/1b1RAU
```

| Method | Path | Description |
|---|---|---|
| `POST` | `/shorten` | Create a short code for `{"url": "..."}` (duplicate URLs return the existing code) |
| `GET` | `/{short_code}` | 302 redirect to the original URL |
| `GET` | `/health` | Health check |
| `GET` | `/docs` | Interactive API docs (Swagger UI) |

## Architecture

```
            POST /shorten                     GET /{code}
                 |                                 |
                 v                                 v
          +-------------+   cache hit      +---------------+
          |   FastAPI   | <--------------- |  Redis cache  |
          +-------------+                  +---------------+
            |        |  cache miss / writes        ^
            v        +-----------------------------+
   +--------------+         populate cache
   |  PostgreSQL  |
   +--------------+
            ^
            |   click events (XADD)   +----------------+
            +------------------------ | Redis Stream   |
              analytics consumer  <-- | (analytics)    |
                                      +----------------+
```

- **FastAPI + asyncpg** with a shared connection pool; schema is applied idempotently on startup (`CREATE ... IF NOT EXISTS`).
- **Redis** caches short code -> URL lookups.
- **Redis Streams + consumer** record click analytics asynchronously, so a redirect never waits on an analytics write. Malformed events are skipped rather than retried forever.

## Tech stack

Python · FastAPI · PostgreSQL · Redis (cache + Streams) · Docker · GitHub Actions · Render

## Running locally

Requires Python, [uv](https://docs.astral.sh/uv/), PostgreSQL and Redis.

```bash
export DATABASE_URL=postgresql://postgres:postgres@localhost:5432/postgres
export REDIS_URL=redis://localhost:6379
uv sync
uv run uvicorn main:app --reload
```

Analytics events are processed by `consumer.py`: run it as a separate process (`uv run python consumer.py`), or set `RUN_CONSUMER=true` to run it inside the API process.

## Testing & CI

```bash
uv run pytest
```

GitHub Actions runs the pytest suite on every push and pull request against real PostgreSQL and Redis service containers.

## Deployment

Deployed to Render with a Blueprint (`render.yaml`): a Docker web service, managed PostgreSQL and a Key Value (Redis) instance, with connection strings injected as environment variables.

## Architectural design & optimizations

### High-Performance Redirection

The application implements a decoupled, lazy-acquisition pattern for resources during URL redirection to maximize throughput and prevent connection pool starvation.

* **Cache Hits:** The redirection route fetches data entirely from the Redis caching layer. It bypasses FastAPI's dependency injection for PostgreSQL, ensuring that a database connection is **never** borrowed from the pool for cached entries.
* **Cache Misses:** The application explicitly handles the cache miss by opening an isolated context manager (`async with request.app.state.db_pool.acquire()`) to look up the short code in the database, populate the cache, and stream the telemetry event out-of-band.

This architecture scales reads linearly with the Redis capacity, ensuring the finite database connection pool is preserved strictly for writes and cache misses.
