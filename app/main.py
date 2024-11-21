import logging
from multiprocessing import Process
import os
from sanic import Sanic
from sanic.log import LOGGING_CONFIG_DEFAULTS
from sanic.response import json as json_sanic
import sys

# Add the app directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# project imports
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

    logger.debug("Setting up worker")

if __name__ == "__main__":

    try:
        app.run(host="0.0.0.0", port=10000, workers=4)
    finally:
        # Stop background processes on shutdown
        if hasattr(app.ctx, "db_proc"):
            app.ctx.db_proc.join()
        if hasattr(app.ctx, "exch_proc"):
            app.ctx.exch_proc.join()