from __future__ import annotations
from flask import Flask
from threading import Thread
import os

app = Flask(__name__)

@app.route('/')
def home() -> str:
    # TODO: Implement health check endpoint
    # - Return a simple HTTP 200 OK response
    # - This endpoint is used by external services to check bot's uptime
    return "Bot is alive!"

def run() -> None:
    # TODO: Run the Flask server
    # - Get the port from environment variables, default to 8080
    # - Start the Flask application
    port = int(os.getenv("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive() -> None:
    # TODO: Start the Flask server in a separate thread
    # - This prevents the Flask server from blocking the main bot process
    # - Ensure the thread is a daemon thread so it exits with the main program
    t = Thread(target=run)
    t.daemon = True
    t.start()
