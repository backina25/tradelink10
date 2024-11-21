import logging
import multiprocessing
import asyncio
from multiprocessing import Queue

logger = logging.getLogger("sanic.root.exch")

async def exch_process_async(exch_queue):
    """Async exch process coroutine."""
    while True:
        request = await asyncio.get_event_loop().run_in_executor(None, exch_queue.get)
        if request == "STOP":
            break
        # Process the exch operation here
        operation, payload = request
        if operation == "EXECUTE_TRADE":
            logger.debug(f"exch Trade Execution: {payload}")
            # Simulate async exch API operation
            await asyncio.sleep(1)
            exch_queue.put(("SUCCESS", None))

def exch_process(exch_queue):
    """Run the async exch process using asyncio.run."""
    asyncio.run(exch_process_async(exch_queue))