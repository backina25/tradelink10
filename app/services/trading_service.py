from app.utils.logger import trading_logger, broker_logger

async def execute_buy(ticker, price, quantity):
    trading_logger.info("Executing BUY order: %s of %s at price %s", quantity, ticker, price)
    broker_logger.debug("Sending buy order to broker for %s: price=%s, quantity=%s", ticker, price, quantity)

async def execute_sell(ticker, price, quantity):
    trading_logger.info("Executing SELL order: %s of %s at price %s", quantity, ticker, price)
    broker_logger.debug("Sending sell order to broker for %s: price=%s, quantity=%s", ticker, price, quantity)

async def handle_stop_loss(ticker, price):
    trading_logger.info("Handling STOP LOSS for %s at price %s", ticker, price)
    broker_logger.debug("Updating stop loss for %s to price=%s", ticker, price)