from sanic.response import json

def setup_routes(app):
    @app.post("/webhook")
    async def tradingview_webhook(request):
        try:
            data = request.json
            
            # Validate payload
            required_fields = [
                "strategy", "orderId", "action", "ticker", "price", "quantity"
            ]
            for field in required_fields:
                if field not in data:
                    return json({"error": f"Missing required field: {field}"}, status=400)
            
            # Extract relevant fields
            action = data["action"]
            ticker = data["ticker"]
            price = data["price"]
            quantity = data["quantity"]
            
            # Log the received payload
            print(f"Received webhook: {data}")

            # Process action
            if action.lower() == "buy":
                await execute_buy(ticker, price, quantity)
            elif action.lower() == "sell":
                await execute_sell(ticker, price, quantity)
            elif action.lower() == "stop_loss":
                await handle_stop_loss(ticker, price)
            else:
                return json({"error": "Unknown action"}, status=400)
            
            return json({"status": "success", "message": "Signal processed"}, status=200)

        except Exception as e:
            print(f"Error processing webhook: {e}")
            return json({"error": "Internal Server Error"}, status=500)
