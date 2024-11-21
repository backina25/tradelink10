import logging
import os
import redis

logger = logging.getLogger("sanic.root.db")

REDIS_URL = os.getenv("REDIS_URL")
logger.debug(f"REDIS_URL: {REDIS_URL}")
redis_conn = redis.Redis.from_url(REDIS_URL)
