import asyncio
from app.utils.redis_config import redis_conn
import json
import logging
import multiprocessing
import os

# project imports
from models import Signal
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger("sanic.root.db")

async def db_process_async():
    pubsub = redis_conn.pubsub()
    pubsub.subscribe("db_channel")
    logger.debug("DB process subscribed to db_channel")

    DATABASE_URL = os.getenv("DATABASE_URL")

    # Create the SQLAlchemy engine
    engine = create_async_engine(DATABASE_URL, echo=True)

    # Create a configured "Session" class
    AsyncSessionLocal = sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    # Dependency to get the async session
    async def get_async_session():
        async with AsyncSessionLocal() as session:
            yield session

    while True:
        message = pubsub.get_message(ignore_subscribe_messages=True)
        if message and message["type"] == "message":
            logger.debug(f"DB Process received task: {message}")

            message_data = json.loads(message['data'])
            operation = message_data["operation"]
            payload = message_data["payload"]

            if operation == "INSERT_SIGNAL":
                signal = Signal.from_json(payload)
                logger.debug(f"DB Insert: {signal.__repr__}")
                try:
                    async for session in get_async_session():
                        await signal.insert(session)
                        logger.debug("Signal inserted into the database successfully.")
                except Exception as e:
                    logger.error(f"Failed to insert signal into the database: {e}")

            elif operation == "STOP":
                break 

        # Sleep for a short time to avoid blocking the event loop
        await asyncio.sleep(0.1)

def db_process():
    """Run the async db process using asyncio.run."""
    asyncio.run(db_process_async())