import logging
import multiprocessing
import asyncio
from multiprocessing import Queue

logger = logging.getLogger("sanic.root.db")

async def db_process_async(db_queue):
    """Async DB process coroutine."""
    while True:
        request = await asyncio.get_event_loop().run_in_executor(None, db_queue.get)
        if request == "STOP":
            break
        # Process the DB operation here
        operation, payload = request
        if operation == "INSERT_SIGNAL":
            logger.debug(f"DB Insert: {payload}")
            # Simulate a success response
            await asyncio.sleep(1)  # Simulate async DB operation
            db_queue.put(("SUCCESS", None))

def db_process(db_queue):
    """Run the async db process using asyncio.run."""
    asyncio.run(db_process_async(db_queue))