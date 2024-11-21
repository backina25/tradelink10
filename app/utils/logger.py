import asyncio
import logging

def create_logger(name, level=logging.INFO):
    """
    Create and configure a logger to write logs to STDERR.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Stream handler for STDERR
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(level)
    # Async stream handler for STDERR
    class AsyncStreamHandler(logging.StreamHandler):
        async def emit(self, record):
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, super().emit, record)

    stream_handler = AsyncStreamHandler()
    # Log format
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    stream_handler.setFormatter(formatter)

    # Add handler to logger
    if not logger.hasHandlers():  # Avoid duplicate handlers in hot reloads
        logger.addHandler(stream_handler)

    return logger

# Create individual loggers for different subsystems
webhook_logger = create_logger("webhook")
trading_logger = create_logger("trading")
db_logger = create_logger("database")
broker_logger = create_logger("broker")
