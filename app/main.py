import os
from sanic import Sanic
from sanic.response import json
import sys

# Add the app directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

print("Current working directory:", os.getcwd())
print("Python path:", sys.path)

from app.routes import setup_routes

app = Sanic("TradingApp")

# Setup routes
setup_routes(app)

# Run the app
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
