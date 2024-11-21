import json
import logging
from app.utils.redis_config import redis_conn
from sanic.response import json as json_sanic
from sqlalchemy import select, insert
from sqlalchemy.ext.asyncio import AsyncSession

# project imports
from app.models import Signal
from app.utils.database import AsyncSessionLocal
from app.services.trading_service import execute_buy, execute_sell, handle_stop_loss

logger = logging.getLogger("sanic.root.webhook")

def setup_routes(app):

    logger.debug("Setting up routes")

    @app.post("/webhook")
    async def tradingview_webhook(request):
        try:
            data = request.json
            logger.info("Received data: %s", data)

            signal = Signal(
                strategy=data["strategy"],
                order_id=data["orderId"],
                symbol=data["symbol"],
                action=data["action"],
                price=data["price"],
                quantity=data["quantity"]
            )

            # Send the signal to the DB process
            redis_conn.publish("db_channel", json.dumps({"operation": "INSERT_SIGNAL", "payload": signal.to_json()}))
            
            # Example: Send a trade execution to the exch process
            if signal.action.lower() in ["buy", "sell"]:
                redis_conn.publish("broker_channel", json.dumps({"operation": "EXECUTE_TRADE", "payload": signal.to_json()}))
            else:
                return json_sanic({"status": "error", "message": "Invalid action"}, status=400)

            # Respond to the client immediately
            return json_sanic({"status": "success", "message": "Signal processed: {signal}"}, status=200)
    
        except Exception as e:
            logger.exception("Unhandled exception occurred")
            return json_sanic({"error": "Internal Server Error (routes.py)"}, status=500)