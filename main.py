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

@app.post("/shorten")
async def shorten_url (url: str):
    if not url.startswith("http://") and not url.startswith("https://"):
        return {"error": "Invalid URL format"}
    async with app.state.db_pool.acquire() as conn:
        try:
            result = await conn.fetchrow ("select short_code from urls where long_url = $1", url)
            if result:
                return {'short_code': result['short_code']}
            
            max_tries = 5
            for i in range(max_tries):
                short_code = ''.join(random.choices(string.ascii_letters + string.digits, k = 6))
                try:
                    await conn.execute("insert into urls (long_url, short_code) values ($1, $2)", url, short_code)
                    return {"short_code": short_code}
                except asyncpg.UniqueViolationError:
                    continue
                except Exception as e:
                    return {"error": str(e)}
            return {"error": "failed to generate unique short code after multiple attempts"}
            

@app.get("/{shortened_url}")
async def redirect(shortened_url: str):
    async with app.state.db_pool.acquire() as conn:
        result = await conn.fetchrow("select long_url from urls where short_code = $1", shortened_url)
        if not result:
            return {"error": "Shortened URL not found"}
        return {"url": result['long_url']}