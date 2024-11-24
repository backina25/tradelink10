import asyncio
import logging
from multiprocessing import Process
import os
import redis.asyncio
from sanic import Sanic
from sanic_cors import CORS
from sanic.log import LOGGING_CONFIG_DEFAULTS
from sanic.response import json as json_sanic
import simplejson as json
import sys

# Add the app directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# project imports
from app.models_db import Account, Signal, WebSource
from models_mem import OurGenericList
from app.process_db import db_process
from app.process_exch import exch_process
from app.routes import setup_routes
from app.task_worker import worker_background_task_to_process_messages
from app.utils.logger import create_loggers

create_loggers()
logger = logging.getLogger("sanic.root")

# Sanic app setup

app = Sanic("tradelink10")
CORS(app)

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

    logprefix = f"Worker[{os.getpid()}]: "

    # setup lists app.ctx.TABLENAME for our db classes
    for db_class in [Account, Signal, WebSource]:
        setattr(app.ctx, db_class.get_tablename(), OurGenericList(force_item_class=db_class))

    app.ctx.redis_conn = None   # workers must only publish (and not receive) messages

    # lunch a subtask to listen for redis messages
    # the worker itself does not listen for messages!
    logger.debug(f"{logprefix}setting up background task to process messages")
    app.add_task(worker_background_task_to_process_messages(app))

@app.listener('before_server_stop')
async def shutdown_worker(app, loop):

    logger.info(f"Worker[{os.getpid()}]: Shutting down worker")

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