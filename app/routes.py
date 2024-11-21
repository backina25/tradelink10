import logging
from multiprocessing import Queue
from sanic.response import json
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

            # Send the signal to the DB process
            app.shared_ctx.db_queue.put(("INSERT_SIGNAL", data))
            
            # Example: Send a trade execution to the exch process
            if data["action"] in ["buy", "sell"]:
                app.shared_ctx.exch_queue.put(("EXECUTE_TRADE", data))

            # Respond to the client immediately
            return json({"status": "success", "message": "Signal processed"}, status=200)
    
        except Exception as e:
            logger.exception("Unhandled exception occurred")
            return json({"error": "Internal Server Error (routes.py)"}, status=500)