import simplejson as json
import logging
import multiprocessing
import asyncio
from app.utils.redis_config import redis_conn
from app.models_db import Signal
import os
import redis.asyncio

logger = logging.getLogger("sanic.root.exch")

async def exch_process_async():

    # Create a Redis connection
    logger.debug("EXCH process: setting up redis and subscribing to broker_channel...")
    redis_url = os.getenv("REDIS_URL", "redis://localhost")
    redis_conn = await redis.asyncio.from_url(redis_url)
    redis_conn = await redis.asyncio.from_url(redis_url)
    redis_pubsub = redis_conn.pubsub()
    await redis_pubsub.subscribe("broker_channel")

    while True:
        message = await redis_pubsub.get_message(ignore_subscribe_messages=True)
        if message is not None and message["type"] == "message":
            logger.debug(f"EXCH Process received message: {message}")

            message_data = json.loads(message['data'], use_decimal=True)
            operation = message_data["operation"]
            payload = message_data["payload"]

            if operation == "EXECUTE_TRADE":
                signal = Signal.from_json(payload)
                logger.debug(f"exch Trade Execution: {signal.__repr__()}")

                # Simulate async exch API operation
                await asyncio.sleep(1)

            elif operation == "STOP":
                break

        # Sleep for a short time to avoid blocking the event loop
        await asyncio.sleep(0.1)

def exch_process():
    """Run the async exch process using asyncio.run."""
    asyncio.run(exch_process_async())