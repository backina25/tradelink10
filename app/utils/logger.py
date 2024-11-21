import asyncio
import logging
from sanic.log import LOGGING_CONFIG_DEFAULTS
import sys

# Sanic Logging configuration
# see, https://github.com/sanic-org/sanic/blob/main/sanic/logging/default.py

# Setup logging
def create_loggers():
    MY_DEFAULT_LEVEL="DEBUG"
    LOGGING_CONFIG_DEFAULTS["formatters"]["generic"]            = {"format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"}
    LOGGING_CONFIG_DEFAULTS["handlers"]["debug"]                = {"class": "logging.StreamHandler", "formatter": "generic", "stream": sys.stdout}
    LOGGING_CONFIG_DEFAULTS["loggers"]["sanic.root"]["level"]   = MY_DEFAULT_LEVEL
    LOGGING_CONFIG_DEFAULTS["loggers"]["sanic.root.broker"]     = {"level": MY_DEFAULT_LEVEL, "handlers": ["debug"], "propagate": False, "qualname": "sanic.root.broker"}
    LOGGING_CONFIG_DEFAULTS["loggers"]["sanic.root.db"]         = {"level": MY_DEFAULT_LEVEL, "handlers": ["debug"], "propagate": False, "qualname": "sanic.root.db"}
    LOGGING_CONFIG_DEFAULTS["loggers"]["sanic.root.webhook"]   = {"level": MY_DEFAULT_LEVEL, "handlers": ["debug"], "propagate": False, "qualname": "sanic.root.webhook"}
    LOGGING_CONFIG_DEFAULTS["loggers"]["sanic.root.trading"]    = {"level": MY_DEFAULT_LEVEL, "handlers": ["debug"], "propagate": False, "qualname": "sanic.root.trading"}


