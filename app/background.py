import multiprocessing
import asyncio
from multiprocessing import Queue


async def db_process_async(db_queue):
    """Async DB process coroutine."""
    while True:
        request = await asyncio.get_event_loop().run_in_executor(None, db_queue.get)
        if request == "STOP":
            break
        # Process the DB operation here
        operation, payload = request
        if operation == "INSERT_SIGNAL":
            print(f"DB Insert: {payload}")
            # Simulate a success response
            await asyncio.sleep(1)  # Simulate async DB operation
            db_queue.put(("SUCCESS", None))

def db_process(db_queue):
    """Run the async DB process using asyncio.run."""
    asyncio.run(db_process_async(db_queue))

async def broker_process_async(broker_queue):
    """Async Broker process coroutine."""
    while True:
        request = await asyncio.get_event_loop().run_in_executor(None, broker_queue.get)
        if request == "STOP":
            break
        # Process the broker operation here
        operation, payload = request
        if operation == "EXECUTE_TRADE":
            print(f"Broker Trade Execution: {payload}")
            # Simulate async broker API operation
            await asyncio.sleep(1)
            broker_queue.put(("SUCCESS", None))

def broker_process(broker_queue):
    """Run the async Broker process using asyncio.run."""
    asyncio.run(broker_process_async(broker_queue))