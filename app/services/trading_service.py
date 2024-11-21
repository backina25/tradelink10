import logging

logger = logging.getLogger("sanic.root.broker")

async def execute_buy(ticker, price, quantity):
    logger.info("Executing BUY order: %s of %s at price %s", quantity, ticker, price)

async def execute_sell(ticker, price, quantity):
    logger.info("Executing SELL order: %s of %s at price %s", quantity, ticker, price)

async def handle_stop_loss(ticker, price):
    logger.info("Handling STOP LOSS for %s at price %s", ticker, price)
