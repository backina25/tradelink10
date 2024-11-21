from sanic.response import json
from sqlalchemy import select, insert
from sqlalchemy.ext.asyncio import AsyncSession

# project imports
from app.models import Signal
from app.utils.database import AsyncSessionLocal
from app.utils.logger import webhook_logger
from app.services.trading_service import execute_buy, execute_sell, handle_stop_loss

def setup_routes(app):
    @app.post("/webhook")
    async def tradingview_webhook(request):
        async with AsyncSessionLocal() as db_session:
            try:
                data = request.json
                webhook_logger.info("Received data: %s", data)

                # Create a Signal instance
                signal = Signal(
                    strategy=data["strategy"],
                    order_id=data["orderId"],
                    action=data["action"],
                    ticker=data["ticker"],
                    price=data["price"],
                    quantity=data["quantity"]
                )

                # Add and commit the signal to the database
                db_session.add(signal)
                await db_session.commit()
                webhook_logger.info("Signal saved to database")
                
                # Process action
                if signal.action.lower() == "buy":
                    await execute_buy(signal.ticker, signal.price, signal.quantity)
                elif signal.action.lower() == "sell":
                    await execute_sell(signal.ticker, signal.price, signal.quantity)
                elif signal.action.lower() == "stop_loss":
                    await handle_stop_loss(signal.ticker, signal.price)
                else:
                    error_message = "Unknown action"
                    webhook_logger.error(error_message)
                    return json({"error": error_message}, status=400)

                webhook_logger.info("Signal processed successfully")
                return json({"status": "success", "message": "Signal processed"}, status=200)

            except Exception as e:
                webhook_logger.exception("Unhandled exception occurred")
                return json({"error": "Internal Server Error"}, status=500)