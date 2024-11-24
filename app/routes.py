import simplejson as json
import logging
import os
import redis.asyncio
from sanic import Blueprint
from sanic.response import json as json_sanic
from sqlalchemy import select, insert
from sqlalchemy.ext.asyncio import AsyncSession

# project imports
from app.models_db import Signal
from app.models_mem import OurGenericList
from app.services.trading_service import execute_buy, execute_sell, handle_stop_loss
from app.utils.database import AsyncSessionLocal
from app.utils.serializer import datetime_serializer


logger = logging.getLogger("sanic.root.webhook")

# Define a Blueprint for the routes
api = Blueprint("api", url_prefix="/api")

@api.get("/signals")
async def get_signals(request):
    item_list = request.app.ctx.signals.to_dict()['items']
    return json_sanic(item_list, status=200)

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
            ourlist=OurGenericList([signal])

            # Send the signal to the DB process
            await app.ctx.redis_conn.publish("db_channel", json.dumps({
                "operation": "INSERT_SIGNAL",
                "item_list": ourlist.to_json()},    # to_dict() does not work here: Input string must be text, not bytes
                sort_keys=True, default=datetime_serializer, use_decimal=True))
            
            # Example: Send a trade execution to the exch process
            # if signal.action.lower() in ["buy", "sell"]:
            #     await app.ctx.redis_conn.publish("broker_channel", json.dumps({
            #         "operation": "EXECUTE_TRADE",
            #         "item_list": ourlist.to_json()},    # to_dict() does not work here: Input string must be text, not bytes
            #         sort_keys=True, default=datetime_serializer, use_decimal=True))
            # else:
            #     return json_sanic({"status": "error", "message": "Invalid action"}, status=400)

            # Respond to the client immediately
            return json_sanic({"status": "success", "message": "Signal processed: {signal}"}, status=200)
    
        except Exception as e:
            logger.exception("Unhandled exception occurred")
            return json_sanic({"error": "Internal Server Error (routes.py)"}, status=500)
    
    app.blueprint(api)
