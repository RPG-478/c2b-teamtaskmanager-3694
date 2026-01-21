from __future__ import annotations
import os

# TODO: Define configuration constants and environment variable retrieval
# - DISCORD_TOKEN: Bot's authentication token
# - PORT: Port for the keep_alive Flask server

DISCORD_TOKEN_ENV_VAR = "DISCORD_TOKEN"
PORT_ENV_VAR = "PORT"
DEFAULT_PORT = 8080

def get_discord_token() -> str | None:
    # TODO: Retrieve Discord token from environment variables
    # - Return None if the token is not set
    return os.getenv(DISCORD_TOKEN_ENV_VAR)

def get_port() -> int:
    # TODO: Retrieve port for keep_alive server from environment variables
    # - Return DEFAULT_PORT if the environment variable is not set or invalid
    try:
        return int(os.getenv(PORT_ENV_VAR, str(DEFAULT_PORT)))
    except ValueError:
        return DEFAULT_PORT
