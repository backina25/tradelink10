import os
from sanic import Sanic
from sanic.response import json
import sys

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.routes import setup_routes

app = Sanic("TradingApp")

# Setup routes
setup_routes(app)

# Run the app
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
