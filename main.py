from fastapi import FastAPI
import random, string
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv
import asyncpg

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
    app.state.db_pool = db_pool
    yield
    await db_pool.close()
    
app = FastAPI(lifespan=lifespan)

storage = {}

@app.post("/shorten")
async def shorten_url (url: str):
    if url.startswith("http://") or url.startswith("https://"):
        if url not in storage:
            storage[url] = ''.join(random.choices(string.ascii_letters + string.digits, k = 6))
            return {"shortened_url": storage[url]}
        else:
            return {"shortened_url": storage[url]}
    else:
        return {"error": "Invalid URL"}

@app.get("/{shortened_url}")
async def redirect(shortened_url: str):
    for url, code in storage.items():
        if code == shortened_url:
            return {"long_url": url}
    return {"error": "Shortened URL not found"}