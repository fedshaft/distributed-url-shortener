## Architectural design & optimizations

### High-Performance Redirection 

The application implements a decoupled, lazy-acquisition pattern for resources during URL redirection to maximize throughput and prevent connection pool starvation.

* **Cache Hits:** The redirection route fetches data entirely from the Redis caching layer. It bypasses FastAPI's dependency injection for PostgreSQL, ensuring that a database connection is **never** borrowed from the pool for cached entries.
* **Cache Misses:** The application explicitly handles the cache miss by opening an isolated context manager (`async with request.app.state.db_pool.acquire()`) to look up the short code in the database, populate the cache, and stream the telemetry event out-of-band.

This architecture scales reads linearly with the Redis capacity, ensuring the finite database connection pool ($\text{max\_size} = 10$) is preserved strictly for writes and cache misses.