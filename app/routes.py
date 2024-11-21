from sanic.response import json

def setup_routes(app):
    @app.post("/webhook")
    async def tradingview_webhook(request):
        try:
            data = request.json
            print("Received data:", data)  # Debug: Log received payload
            
            # Validate payload
            required_fields = [
                "strategy", "orderId", "action", "ticker", "price", "quantity"
            ]
            for field in required_fields:
                if field not in data:
                    error_message = f"Missing required field: {field}"
                    print("Error:", error_message)  # Debug: Log validation errors
                    return json({"error": error_message}, status=400)

            # Safely extract fields with defaults
            strategy = data.get("strategy", "unknown")
            order_id = data.get("orderId", "unknown")
            action = data.get("action", "unknown")
            ticker = data.get("ticker", "unknown")
            price = data.get("price", 0)
            quantity = data.get("quantity", 0)

            print(f"Action: {action}, Ticker: {ticker}, Price: {price}, Quantity: {quantity}")  # Debug: Log extracted fields

            # Process action
            if action.lower() == "buy":
                await execute_buy(ticker, price, quantity)
            elif action.lower() == "sell":
                await execute_sell(ticker, price, quantity)
            else:
                error_message = "Unknown action"
                print("Error:", error_message)  # Debug: Log unknown action
                return json({"error": error_message}, status=400)

            return json({"status": "success", "message": "Signal processed"}, status=200)

        except Exception as e:
            print("Unhandled Exception:", e)  # Debug: Log unexpected errors
            return json({"error": "Internal Server Error"}, status=500)
