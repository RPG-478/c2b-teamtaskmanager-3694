# Discord Task Management Bot

This is a Discord bot designed to help teams manage tasks directly within Discord. It supports basic task viewing, creation, modification, and deletion, with persistent storage.

## Features

- **Task Management**: Add, mark as done, edit, and delete tasks.
- **Task Viewing**: List all active tasks or view details of a specific task.
- **Persistence**: All task data is saved to a JSON file, ensuring data is not lost on bot restarts.
- **Uptime Monitoring**: Includes a simple web server for health checks and keeping the bot alive on hosting platforms.

## Setup Instructions

### Prerequisites

- Python 3.9+
- Discord Bot Token

### Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd discord-task-bot
    ```

2.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: `venv\Scripts\activate`
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    (Note: `requirements.txt` will be generated in a later step, for now, assume `discord.py` and `Flask` are needed.)

### Environment Variables

Create a `.env` file in the root directory of the project based on `.env.example` and fill in your bot token and desired port.

```ini
# .env
DISCORD_TOKEN=YOUR_BOT_TOKEN_HERE
PORT=8080
```

### Running the Bot

1.  **Ensure your `.env` file is configured.**
2.  **Start the bot:**
    ```bash
    python main.py
    ```

The bot should log in to Discord, and the `keep_alive.py` Flask server will start on the specified `PORT` (default 8080).
