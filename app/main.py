import asyncio
import logging
from multiprocessing import Process
import os
import redis.asyncio
from sanic import Sanic
from sanic.log import LOGGING_CONFIG_DEFAULTS
from sanic.response import json as json_sanic
import simplejson as json
import sys

# Add the app directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# project imports
from app.models_db import Account, Signal, WebSource
from app.process_db import db_process
from app.process_exch import exch_process
from app.routes import setup_routes
from app.utils.logger import create_loggers

create_loggers()
logger = logging.getLogger("sanic.root")

# Sanic app setup
app = Sanic("tradelink10")

# Setup routes
setup_routes(app)

@app.listener('main_process_start')
async def setup_main(app, loop):

    logger.debug("Setting up main process")

    # Start background processes
    app.ctx.db_proc = Process(target=db_process)
    app.ctx.db_proc.start()
    app.ctx.exch_proc = Process(target=exch_process)
    app.ctx.exch_proc.start()

@app.listener('before_server_start')
async def setup_worker(app, loop):

    app.ctx.accounts = []       # class Account   -> exchange_id, open_orders, closed_orders, positions, trades
    app.ctx.signals = []        # class Signal    -> BUY, SELL, CLOSE
    app.ctx.websources = []     # class WebSource -> "postman", "tradingview" 
    app.ctx.exchanges = []      # class Exchange  -> tickers

    app.ctx.redis_conn = None   # workers must only publish (and not receive) messages

    # lunch a subtask to listen for redis messages
    # the worker itself does not listen for messages!
    logger.debug(f"Worker[{os.getpid()}]: setting up background task to process messages")
    async def worker_background_task_to_process_messages():

        # Create a Redis connection
        logger.debug(f"WorkerBG[{os.getpid()}]: setting up redis and subscribing to workers_channel...")
        redis_url = os.getenv("REDIS_URL", "redis://localhost")
        redis_conn = await redis.asyncio.from_url(redis_url)
        app.ctx.redis_conn = redis_conn # workers must only publish (and not receive) messages
        redis_pubsub = redis_conn.pubsub()
        await redis_pubsub.subscribe("workers_channel")

        logger.debug(f"WorkerBG[{os.getpid()}]: READY to receive messages")
        try:
            while True:
                message = await redis_pubsub.get_message(ignore_subscribe_messages=True)
                if message is not None and message["type"] == "message":

                    # FIXME: code duplication of message parsing
                    # extract the operation and payload from the message
                    message_data = json.loads(message['data'], use_decimal=True)
                    operation = message_data["operation"]
                    # logger.debug(f"Worker[{os.getpid()}]: received message {operation}")

                    if operation in [ "ADD", "DELETE", "INITIALIZE", "MODIFY" ]:
                        class_name = message_data.get("class_name", None)
                        dict_list = message_data.get("dict_list", None)
                        if class_name is None:
                            logger.error(f"WorkerBG[{os.getpid()}]: {operation}: missing class_name")
                            return json_sanic({"error": "bad response from database"}, status=500)
                        if dict_list is None:
                            logger.error(f"WorkerBG[{os.getpid()}]: {operation}: missing dict_list")
                            return json_sanic({"error": "bad response from database"}, status=500)
                        cls = globals()[class_name]
                        if cls is None:
                            logger.error(f"WorkerBG[{os.getpid()}]: {operation}: class {class_name} not found")
                            return json_sanic({"error": "bad response from database"}, status=500)

                        if operation == "DELETE":
                            #FIXME: implement delete
                            raise NotImplementedError("DELETE operation not implemented")
                        
                        elif operation == "MODIFY":
                            #FIXME: implement delete
                            raise NotImplementedError("MODIFY operation not implemented")   

                        elif operation == "ADD":
                            count_new = 0
                            for new_item in dict_list:
                                for old_item in getattr(app.ctx, f"{class_name.lower()}s"):
                                    if old_item.id == new_item.id:
                                        logger.debug(f"WorkerBG[{os.getpid()}]: {operation}: error: item {old_item.id} already exists")
                                        return json_sanic({"error": "db error: item already exists"}, status=500)
                                getattr(app.ctx, f"{class_name.lower()}s").append(new_item)
                                count_new += 1
                            logger.debug(f"WorkerBG[{os.getpid()}]: {operation}: added {count_new} items")

                        elif operation == "INITIALIZE":
                            old_item_count = len(getattr(app.ctx, f"{class_name.lower()}s"))
                            setattr(app.ctx, f"{class_name.lower()}s", dict_list)
                            if len(dict_list) > 0 or old_item_count > 0:
                                logger.debug(f"WorkerBG[{os.getpid()}]: {operation}: added {len(dict_list)} {class_name.lower()}s (dropped {old_item_count})")

                    elif operation == "STOP":
                        break 

                    else:
                        logger.debug(f"ignoring message: {operation}")

                # Sleep for a short time to avoid blocking the event loop
                await asyncio.sleep(0.1)
        except asyncio.CancelledError:
            logger.debug(f"WorkerBG[{os.getpid()}]: CANCELLED")
        finally:
            logger.debug(f"WorkerBG[{os.getpid()}]: CLEANUP")

        redis_pubsub.close()
        await redis_pubsub.wait_closed()
        redis_conn.close()
        await redis_conn.wait_closed()
        app.ctx.redis_conn = None

    app.add_task(worker_background_task_to_process_messages())


@app.listener('before_server_stop')
async def shutdown_worker(app, loop):

    logger.debug(f"Worker[{os.getpid()}]: Shutting down worker")

    # if app.ctx.redis_conn is not None:
    #     app.ctx.redis_conn.close()
    #     await app.ctx.redis_conn.wait_closed()

# after_server_stop because all HTTP connections have been closed
@app.listener("after_server_stop")
async def stop_bg(app, loop):
    current = asyncio.current_task()
    for task in asyncio.all_tasks():
        if task is not current:
            logger.warning(f"MAIN: Stopping task: {task}")
            task.cancel()
            await task

if __name__ == "__main__":

    try:
        app.run(host="0.0.0.0", port=10000, workers=4)
    finally:
        # Stop background processes on shutdown
        if hasattr(app.ctx, "db_proc"):
            logger.warning(f"MAIN: Stopping process db_proc")
            app.ctx.db_proc.join()
        if hasattr(app.ctx, "exch_proc"):
            logger.warning(f"MAIN: Stopping process exch_proc")
            app.ctx.exch_proc.join()