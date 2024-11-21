import json
import logging
import multiprocessing
import asyncio
from app.utils.redis_config import redis_conn

from models import Signal

logger = logging.getLogger("sanic.root.db")

async def db_process_async():
    pubsub = redis_conn.pubsub()
    pubsub.subscribe("db_channel")
    logger.debug("DB process subscribed to db_channel")

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
                    async with Signal.async_session() as session:
                        async with session.begin():
                            session.add(signal)
                            await session.commit()
                    logger.debug("Signal inserted into the database successfully.")
                except Exception as e:
                    logger.error(f"Failed to insert signal into the database: {e}")

            elif operation == "STOP":
                break 

def db_process():
    """Run the async db process using asyncio.run."""
    asyncio.run(db_process_async())