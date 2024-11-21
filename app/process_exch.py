import json
import logging
import multiprocessing
import asyncio
from app.utils.redis_config import redis_conn
from models import Signal

logger = logging.getLogger("sanic.root.exch")

async def exch_process_async():

    pubsub = redis_conn.pubsub()
    pubsub.subscribe("broker_channel")
    logger.debug("DB process subscribed to broker_channel")

    while True:
        message = pubsub.get_message(ignore_subscribe_messages=True)
        if message and message["type"] == "message":
            logger.debug(f"EXCH Process received task: {message}")

            message_data = json.loads(message['data'])
            operation = message_data["operation"]
            payload = message_data["payload"]

            if operation == "EXECUTE_TRADE":
                signal = Signal.from_json(payload)
                logger.debug(f"exch Trade Execution: {signal.__repr__()}")

                # Simulate async exch API operation
                await asyncio.sleep(1)

            elif operation == "STOP":
                break

def exch_process():
    """Run the async exch process using asyncio.run."""
    asyncio.run(exch_process_async())