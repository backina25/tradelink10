from multiprocessing import Queue
import os
from sanic import Sanic
from sanic.response import json
import sys

# Add the app directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# project imports
from background import start_background_processes
from app.routes import setup_routes

# Create the queues
db_queue = Queue()
broker_queue = Queue()

app = Sanic("tradelink10")

# Setup routes
setup_routes(app)

if __name__ == "__main__":
    # Start background processes
    db_proc, broker_proc = start_background_processes(db_queue, broker_queue)
        
    try:
        app.run(host="0.0.0.0", port=10000, workers=4)
    finally:
        # Stop background processes on shutdown
        db_queue.put("STOP")
        broker_queue.put("STOP")
        db_proc.join()
        broker_proc.join()