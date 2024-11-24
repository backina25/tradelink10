
import asyncio
import logging
import os
import redis.asyncio
import simplejson as json


# project imports
from app.models_db import Account, Signal, WebSource
from models_mem import OurGenericList

# project definitions and globals
logger = logging.getLogger("sanic.root.webhook")


async def worker_background_task_to_process_messages(app):

    logprefix_base = f"WorkerBG[{os.getpid()}]: "
    logprefix = logprefix_base

    # Create a Redis connection
    logger.debug(f"{logprefix}setting up redis and subscribing to workers_channel...")
    redis_url = os.getenv("REDIS_URL", "redis://localhost")
    redis_conn = await redis.asyncio.from_url(redis_url)
    app.ctx.redis_conn = redis_conn # workers must only publish (and not receive) messages
    redis_pubsub = redis_conn.pubsub()
    await redis_pubsub.subscribe("workers_channel")


    def get_list_from_message_data(message_data, logprefix=""):

        resulting_list = None
        if "item_list" not in message_data:
            logger.error(f"{logprefix}message misses field item_list")
        elif message_data["item_list"] is None:
            logger.error(f"{logprefix}item_list is None")
        else:
            item_list_json_str = message_data["item_list"]
            try:
                resulting_list = OurGenericList.from_json(item_list_json_str)
                if len(resulting_list) == 0:
                    logger.error(f"{logprefix}received an empty list")
                    resulting_list = None
            except Exception as e:
                logger.error(f"{logprefix}failed to convert JSON string {message_data.get('item_list', None)} to OurGenericList: {e}")
        return resulting_list                    

    def get_message_data(message, logprefix=""):
        message_data = None
        try:
            message_data = json.loads(message['data'], use_decimal=True)
            # operation is a mandatory field
            if 'operation' not in message_data:
                logger.error(f"{logprefix}message_data misses mandatory field operation")
                raise ValueError("missing operation")
            if message_data['operation'] is None:
                logger.error(f"{logprefix}message operation is None")
                raise ValueError("operation is None")
        except Exception as e:
            logger.error(f"{logprefix}failed to parse JSON: {e}")
            raise ValueError("failed to parse JSON: {e}")
        return message_data

    logger.debug(f"{logprefix}READY to receive messages")
    try:
        while True:
            message = await redis_pubsub.get_message(ignore_subscribe_messages=True)
            if message is not None and message["type"] == "message":

                # extract message data
                try:
                    message_data = get_message_data(message, logprefix)
                except ValueError as e:
                    continue

                operation = message_data["operation"]
                logprefix = f"{logprefix_base}{operation}: "

                # operations that do not use message_data
                if operation == "STOP":
                    break

                if operation in [ "ADD", "DELETE", "INITIALIZE", "MODIFY" ]:
                    given_list = get_list_from_message_data(message_data=message_data, logprefix=logprefix)
                    if given_list is None:
                        continue

                    # logger.debug(f"{logprefix}received {len(given_list)} items: {given_list.to_json()}")

                    tablename = given_list[0].__class__.get_tablename()
                    old_item_count = len(getattr(app.ctx, tablename))

                    if operation in [ "DELETE", "MODIFY" ]:
                        #FIXME: implement missing operations
                        logger.error(f"{logprefix}operation not implemented")

                    elif operation == "ADD":
                        try:
                            getattr(app.ctx, tablename).extend(given_list)
                        except Exception as e:
                            logger.error(f"{logprefix}failed to extend list app.ctx.{tablename}: {e}")
                        if len(given_list) > 0:
                            logger.debug(f"{logprefix}added {len(given_list)} {tablename} (total count: {len(getattr(app.ctx, tablename))})")

                    elif operation == "INITIALIZE":
                        getattr(app.ctx, tablename).clear()
                        getattr(app.ctx, tablename).extend(given_list)
                        if len(given_list) > 0 or old_item_count > 0:
                            logger.debug(f"{logprefix}added {len(given_list)} {tablename} (dropped {old_item_count})")

                elif operation == "STOP":
                    break 

                else:
                    logger.error(f"{logprefix}ignoring message")

            # Sleep for a short time to avoid blocking the event loop
            await asyncio.sleep(0.1)
    except asyncio.CancelledError:
        logger.debug(f"{logprefix}CANCELLED")
    finally:
        logger.debug(f"{logprefix}CLEANUP")

    # redis_pubsub.close()
    # await redis_pubsub.wait_closed()
    redis_conn.close()
    await redis_conn.wait_closed()
    app.ctx.redis_conn = None
