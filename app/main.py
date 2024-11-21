import logging
from multiprocessing import Queue, set_start_method, Process
import os
from sanic import Sanic
from sanic.log import LOGGING_CONFIG_DEFAULTS
from sanic.response import json
import sys

# Add the app directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# project imports
from app.background import broker_process, db_process
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

    # Create the queues
    app.shared_ctx.db_queue = Queue()
    app.shared_ctx.broker_queue = Queue() 

    # Start background processes
    app.ctx.db_proc = Process(target=db_process, args=(app.shared_ctx.db_queue,))
    app.ctx.db_proc.start()
    app.ctx.broker_proc = Process(target=broker_process, args=(app.shared_ctx.broker_queue,))
    app.ctx.broker_proc.start()

@app.listener('before_server_start')
async def setup_worker(app, loop):

    logger.debug("Setting up worker")

    

if __name__ == "__main__":

    try:
        app.run(host="0.0.0.0", port=10000, workers=4)
    finally:
        # Stop background processes on shutdown
        if hasattr(app.shared_ctx, "db_queue"):
            app.shared_ctx.db_queue.put("STOP")
        if hasattr(app.shared_ctx, "broker_queue"):
            app.shared_ctx.broker_queue.put("STOP")
        if hasattr(app.ctx, "db_proc"):
            app.ctx.db_proc.join()
        if hasattr(app.ctx, "broker_proc"):
            app.ctx.broker_proc.join()