import asyncio
from app.utils.redis_config import redis_conn
import simplejson as json
import logging
import multiprocessing
import os
import redis.asyncio

# project imports
import config
from app.models_db import Account, Signal, WebSource
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.future import select
from sqlalchemy.dialects.postgresql import insert
import logging

logger = logging.getLogger("sanic.root.db")

class DBProcess:
    def __init__(self):
        self.redis_conn = None
        self.redis_pubsub = None
        self.engine = None
        self.AsyncSessionLocal = None

    async def broadcast(self, db_class):
        try:
            logger.debug(f"DB Process: fetching all {db_class.__name__.lower()} from database...")
            async for session in self.get_async_session():
                items = await session.execute(select(db_class))
                items = items.scalars().all()
                items = [item.to_dict() for item in items]
            
            logger.debug(f"DB Process: publishing {len(items)} {db_class.__name__.lower()} to workers_channel...")
            await self.redis_conn.publish("workers_channel", json.dumps({
                "operation": "INITIALIZE",
                "class_name": db_class.__name__,
                "dict_list": items},
                indent=4, sort_keys=True, default=str, use_decimal=True))
        except Exception as e:
            logger.error(f"DB Process: failed to fetch {db_class.__name__.lower()} from database: {e}")

    async def db_add_initial_data(self):
        # Add default rows to the database if table is empty
        async for session in self.get_async_session():
            for cls in [Account, Signal, WebSource]:
                items = await session.execute(select(cls))
                items = items.scalars().all()
                if len(items) == 0:
                    logger.debug(f"DB Process: adding default {cls.__name__.lower()} to database...")
                    if cls.__name__ in config.DATABASE['initial_data']:
                        for item in config.DATABASE['initial_data'][cls.__name__]:
                            await cls(**item).insert(session)

    async def db_connect(self):
        # Connecting to database
        logger.debug("DB process: connecting to the database...")
        DATABASE_URL = os.getenv("DATABASE_URL")
        self.engine = create_async_engine(DATABASE_URL, echo=True)
        self.AsyncSessionLocal = sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )

    async def db_create_tables(self):
        async with self.engine.begin() as conn:
            logger.debug("DB Process: creating tables if missing...")
            await conn.run_sync(Account.metadata.create_all)
            await conn.run_sync(Signal.metadata.create_all)
            await conn.run_sync(WebSource.metadata.create_all)

    async def db_set_loglevel(self):
        # Check and set the level for all handlers attached to this logger
        sqlalchemy_logger = logging.getLogger('sqlalchemy.engine.Engine')
        for handler in sqlalchemy_logger.handlers:
            handler.setLevel(logging.WARNING)

    async def get_async_session(self):
        async with self.AsyncSessionLocal() as session:
            yield session

    async def redis_setup(self):
        logger.debug("DB process: initializing redis...")
        redis_url = os.getenv("REDIS_URL", "redis://localhost")
        self.redis_conn = await redis.asyncio.from_url(redis_url)
        self.redis_pubsub = self.redis_conn.pubsub()
        await self.redis_pubsub.subscribe("db_channel")

    async def setup(self):
        await self.redis_setup()
        await self.db_set_loglevel()
        await self.db_connect()
        await self.db_create_tables()
        await self.db_add_initial_data()


    async def run(self):

        # Initialization
        await self.setup()

        # read database and publish all data to all workers
        await self.broadcast(Account)
        await self.broadcast(Signal)
        await self.broadcast(WebSource)

        while True:
            # Check for new messages on the `db_channel` channel
            message = await self.redis_pubsub.get_message(ignore_subscribe_messages=True)
            if message is not None and message["type"] == "message":
                logger.debug(f"DB Process received message: {message}")

                # extract the operation and payload from the message
                message_data = json.loads(message['data'], use_decimal=True)
                operation = message_data["operation"]
                request_id = message_data.get("request_id", None)
                payload = message_data.get("payload", None)

                # ------------------------------
                if operation == "INSERT_SIGNAL":
                    signal = Signal.from_json(payload)
                    logger.debug(f"DB Insert: {signal.__repr__}")
                    try:
                        async for session in self.get_async_session():
                            logger.debug("DB Process: writing 1 received signal to database...")
                            await signal.insert(session)
                            logger.debug("DB Process: publishing 1 new signal to workers_channel")
                            await self.redis_conn.publish("workers_channel", json.dumps({
                                "operation": "ADD_SIGNAL",
                                "request_id": request_id,
                                "payload": signal},
                                indent=4, sort_keys=True, default=str, use_decimal=True))
            
                    except Exception as e:
                        logger.error(f"Failed to insert signal into the database: {e}")

                elif operation == "STOP":
                    break 

            # Sleep for a short time to avoid blocking the event loop
            await asyncio.sleep(0.1)

def db_process():
    """Run the async db process using asyncio.run."""
    db_process_instance = DBProcess()
    asyncio.run(db_process_instance.run())