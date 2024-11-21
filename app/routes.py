from sanic.response import json

# project imports
from app.utils.logger import webhook_logger
from app.services.trading_service import execute_buy, execute_sell, handle_stop_loss

def setup_routes(app):
    @app.post("/webhook")
    async def tradingview_webhook(request):
        try:
            data = request.json
            webhook_logger.info("Received data: %s", data)

            # Validate payload
            required_fields = [
                "strategy", "orderId", "action", "ticker", "price", "quantity"
            ]
            for field in required_fields:
                if field not in data:
                    error_message = f"Missing required field: {field}"
                    webhook_logger.warning(error_message)
                    return json({"error": error_message}, status=400)

            # Extract relevant fields
            action = data["action"]
            ticker = data["ticker"]
            price = data["price"]
            quantity = data["quantity"]

            webhook_logger.info(
                "Action: %s, Ticker: %s, Price: %s, Quantity: %s",
                action, ticker, price, quantity
            )

            # Process action
            if action.lower() == "buy":
                await execute_buy(ticker, price, quantity)
            elif action.lower() == "sell":
                await execute_sell(ticker, price, quantity)
            elif action.lower() == "stop_loss":
                await handle_stop_loss(ticker, price)
            else:
                error_message = "Unknown action"
                webhook_logger.error(error_message)
                return json({"error": error_message}, status=400)

            webhook_logger.info("Signal processed successfully")
            return json({"status": "success", "message": "Signal processed"}, status=200)

        except Exception as e:
            webhook_logger.exception("Unhandled exception occurred")
            return json({"error": "Internal Server Error"}, status=500)