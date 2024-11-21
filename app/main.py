
from sanic import Sanic
from sanic.response import json
from app.routes import setup_routes

app = Sanic("TradingApp")

# Setup routes
setup_routes(app)

# Run the app
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
