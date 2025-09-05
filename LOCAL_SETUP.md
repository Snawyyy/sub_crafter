# Local Development Setup

This project can be run locally using Python virtual environments instead of Docker.

## Prerequisites

- Python 3.11 or higher
- Redis server
- FFmpeg

## Setup Instructions

1.  **Create a Python Virtual Environment:**
    ```bash
    cd backend
    python3.11 -m venv .venv
    source .venv/bin/activate
    pip install --upgrade pip
    pip install --no-cache-dir -r requirements.txt
    ```

2.  **Install FFmpeg:**
    - On Ubuntu/Debian: `sudo apt update && sudo apt install ffmpeg`
    - On macOS: `brew install ffmpeg`
    - On Windows: Download from https://ffmpeg.org/download.html

3.  **Install Redis:**
    - On Ubuntu/Debian: `sudo apt update && sudo apt install redis`
    - On Fedora/RHEL/CentOS: `sudo dnf install redis`
    - On Arch Linux: `sudo pacman -S redis`
    - On macOS: `brew install redis`
    - On Windows: Follow instructions at https://redis.io/docs/latest/operate/oss_and_stack/install/install-redis/install-redis-on-windows/

4.  **Configure Environment Variables:**
    Copy `.env.example` to `.env` and fill in the required values:
    ```bash
    cd backend
    cp .env.example .env
    # Edit .env to add your GEMINI_API_KEY
    ```

5.  **Start the Application:**
    Simply run the main script with the "local" argument:
    ```bash
    ./you_cap local
    ```
    
    This will automatically:
    - Start Redis server with persistence
    - Start the FastAPI server
    - Start the Celery worker

6.  **Access the Application:**
    The API will be available at `http://localhost:8000`.