
from sanic.response import json

def setup_routes(app):
    @app.post("/webhook")
    async def tradingview_webhook(request):
        data = request.json
        return json({"status": "success", "message": "Signal received"}, status=200)
