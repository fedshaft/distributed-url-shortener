from fastapi import FastAPI, Request, Depends
from fastapi.responses import RedirectResponse
from fastapi import HTTPException
import random, string
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv
import asyncpg
from redis import asyncio as aioredis
from time import time
from redis.exceptions import RedisError
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
async def shorten_url(...):

    if not url.startswith(("http://", "https://")):
        raise HTTPException(status_code=400, detail="Invalid URL format")
    try:
        result = await conn.fetchrow("SELECT short_code FROM urls WHERE long_url=$1",url)
    except asyncpg.PostgresError:
        logger.exception("Failed while reading URL")
        raise HTTPException(status_code=500, detail="Database error")
    if result:
        return {"short_code": result["short_code"]}
    for _ in range(5):
        short_code = "".join(
            random.choices(string.ascii_letters + string.digits, k=6)
        )
        try:
            await conn.execute("INSERT INTO urls (long_url, short_code) VALUES ($1, $2)",url,short_code)
            await cache.set(short_code, url, ex=3600)
            return {"short_code": short_code}
        except asyncpg.UniqueViolationError:
            continue
        except asyncpg.PostgresError:
            logger.exception("Failed while inserting URL")
            raise HTTPException(status_code=500, detail="Database error")
    raise HTTPException(status_code=503, detail="Failed to generate unique short code",)

@app.get("/{shortened_url}")
async def redirect(shortened_url: str, request: Request, cache=Depends(get_cache)):
    try:
        cached_url = await cache.get(shortened_url)
    except RedisError:
        logger.exception("Failed to read from Redis")
        cached_url = None
    if cached_url:
        try:
            await cache.xadd("analytics",{"short_code": shortened_url, "timestamp": str(time())}, maxlen=1000, approximate=True)
        except RedisError:
            logger.exception("Failed to write analytics to Redis")
        return RedirectResponse(cached_url, status_code=302)
    try:
        async with request.app.state.db_pool.acquire() as conn:
            result = await conn.fetchrow("SELECT long_url FROM urls WHERE short_code = $1", shortened_url)
    except asyncpg.PostgresError:
        logger.exception("Failed while reading from database")
        raise HTTPException(status_code=500, detail="Database error")
    if result is None:
        raise HTTPException(status_code=404, detail="Shortened URL not found")
    try:
        await cache.set(shortened_url, result["long_url"],ex=3600)
        await cache.xadd("analytics",{"short_code": shortened_url, "timestamp": str(time())}, maxlen=1000, approximate=True)
    except RedisError:
        logger.exception("Failed to update Redis cache")
    return RedirectResponse(result["long_url"],status_code=302)