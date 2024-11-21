
import asyncio
from asyncpg import create_pool

DB_POOL = None

async def setup_db():
    global DB_POOL
    DB_POOL = await create_pool(
        user="your_db_user",
        password="your_db_password",
        database="your_db_name",
        host="your_db_host",
        port="5432"
    )

async def close_db():
    await DB_POOL.close()
