# redis stream -> consumer -> psql
# consumer reads from the stream and write to the db
import asyncpg
import asyncio
from redis import asyncio as aioredis
import os
from dotenv import load_dotenv

load_dotenv()
#connect to db and redis
async def db_connect():
    db_pool = await asyncpg.create_pool(
        min_size = 1,
        max_size = 10,
        host = os.getenv("db_host"),
        user = os.getenv("db_user"),
        password = os.getenv("db_password"),
        database = os.getenv("db_name")
    )
    return db_pool

async def redis_connect():
    cache = aioredis.from_url(os.getenv("redis_url"), decode_responses=True)
    return cache

async def consume():
    db_pool = await db_connect()
    cache = await redis_connect()
    #tract last id, start with 0 on first run
    last_id = "0"
    while True:
        try:
            #in loop call xread to read from the stream, if not batch insert use executemany call
            entries = await cache.xread({"analytics": last_id}, count = 5000)
            if entries:
                # entries returns a list of [stream_name, [(id, {fields}), ...]] so entries are at entries[0][1]
                rows = []
                for entry_id, field_dict in entries[0][1]:
                    short_code = field_dict.get("short_code")
                    clicked_at = float(field_dict.get("timestamp"))
                    rows.append((short_code, clicked_at))
                async with db_pool.acquire() as conn:
                    await conn.executemany("insert into analytics (short_code, clicked_at) values ($1, $2)", rows)
                last_id = entries[0][1][-1][0]
            else:
                await asyncio.sleep(1)
        except Exception as e:
            print(f"Error: {e}")
            await asyncio.sleep(1)
if __name__ == "__main__":
    asyncio.run(consume())