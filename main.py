from fastapi import FastAPI, Request, Depends
from fastapi.responses import RedirectResponse
import random, string
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv
import asyncpg
from redis import asyncio as aioredis
from time import time

load_dotenv()
@asynccontextmanager
async def lifespan(app: FastAPI):
    db_pool = await asyncpg.create_pool(
        min_size = 1,
        max_size = 10,
        host = os.getenv("db_host"),
        user = os.getenv("db_user"),
        password = os.getenv("db_password"),
        database = os.getenv("db_name")
    )
    cache = aioredis.from_url(os.getenv("redis_url"), decode_responses=True)

    app.state.db_pool = db_pool
    app.state.cache = cache
    yield
    await db_pool.close()
    await cache.close()

app = FastAPI(lifespan=lifespan)

async def get_conn(request: Request):
    async with request.app.state.db_pool.acquire() as conn:
        yield conn

async def get_cache(request: Request):
    yield request.app.state.cache
    
@app.post("/shorten")
async def shorten_url(url: str, conn = Depends(get_conn), cache = Depends(get_cache)):
    if not url.startswith("http://") and not url.startswith("https://"):
        return {"error": "Invalid URL format"}
    try:
        result = await conn.fetchrow("select short_code from urls where long_url = $1",url)
        if result:
            return {"short_code": result["short_code"]}
        max_tries = 5
        for _ in range(max_tries):
            short_code = ''.join(random.choices(string.ascii_letters + string.digits,k=6))
            try:
                await conn.execute("insert into urls (long_url, short_code) values ($1, $2)", url,short_code)
                await cache.set(short_code, url, ex = 3600)
                return {"short_code": short_code}
            except asyncpg.UniqueViolationError:
                continue
        return {"error": "failed to generate unique short code"}
    except Exception as e:
        return {"error": str(e)}

@app.get("/{shortened_url}")
async def redirect(shortened_url: str, request: Request, cache = Depends(get_cache)):
        try:
            cached_url = await cache.get(shortened_url)
            if cached_url:
                await cache.xadd("analytics", {"short_code" : shortened_url, "timestamp": str(time())}, maxlen = 1000, approximate=True)
                return RedirectResponse(cached_url, status_code=302)
            async with request.app.state.db_pool.acquire() as conn:
                result = await conn.fetchrow("select long_url from urls where short_code = $1", shortened_url)
            if result:
                await cache.set(shortened_url, result['long_url'], ex = 3600)
                await cache.xadd("analytics", {"short_code" : shortened_url, "timestamp": str(time())}, maxlen = 1000, approximate=True)
                return RedirectResponse(result['long_url'], status_code=302)
            else:
                return {"error": "Short URL not found"}
        except Exception as e:
            return {"error": str(e)}
        