
import asyncio
from asyncpg import create_pool

# project imports
from app.utils.logger import db_logger

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
    db_logger.debug("Database connection established")

async def close_db():
    await DB_POOL.close()
    db_logger.debug("Database connection closed")
