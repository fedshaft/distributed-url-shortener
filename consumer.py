import asyncpg
import asyncio
from redis import asyncio as aioredis
import os
from dotenv import load_dotenv

load_dotenv()

async def db_connect():
    db_pool = await asyncpg.create_pool(
        min_size=1,
        max_size=10,
        host=os.getenv("db_host"),
        user=os.getenv("db_user"),
        password=os.getenv("db_password"),
        database=os.getenv("db_name")
    )
    return db_pool

async def redis_connect():
    cache = aioredis.from_url(os.getenv("redis_url"), decode_responses=True)
    return cache

async def consume():
    db_pool = await db_connect()
    cache = await redis_connect()
    async with db_pool.acquire() as conn:
        last_id = await conn.fetchval(
            "select last_id from consumer_offsets where stream_name = 'analytics'"
        )
        if last_id is None:
            last_id = "0"
    while True:
        try:
            entries = await cache.xread({"analytics": last_id}, count=10, block=1000)
            if not entries:
                continue
            rows = []
            for stream_id, field_dict in entries[0][1]:
                rows.append(
                    (
                        stream_id,
                        field_dict["short_code"],
                        float(field_dict["timestamp"])  
                    )
                )
        
            new_last_id = entries[0][1][-1][0]
        
            #get a connection for the batch transaction inside the loop
            async with db_pool.acquire() as conn:
                async with conn.transaction():
                    await conn.executemany(
                        """
                        insert into analytics (stream_id, short_code, clicked_at) 
                        values ($1, $2, $3)
                        """, 
                        rows
                    )

                    await conn.execute(
                        """
                        insert into consumer_offsets (stream_name, last_id) 
                        values ('analytics', $1) 
                        on conflict (stream_name) 
                        do update set last_id = EXCLUDED.last_id
                        """, 
                        new_last_id
                    )
            last_id = new_last_id
        except Exception as e:
            print(f"Error occurred: {e}")
            await asyncio.sleep(1)  

if __name__ == "__main__":
    asyncio.run(consume())