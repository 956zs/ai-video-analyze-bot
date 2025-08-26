# AI Video Analyzer Bot

This project provides a Discord bot that can download a video from a given URL, analyze its content using a multimodal AI model (like Gemini), and answer follow-up questions about it.

The project has been architected to use a decoupled backend API service, making it robust and scalable.

## Architecture

The system is composed of two main parts:

1.  **Backend API (`api.py`)**: A [FastAPI](https://fastapi.tiangolo.com/) server that handles the heavy lifting. It exposes endpoints for downloading, analyzing, and asking questions about videos. This allows the core logic to be independent and potentially used by other services.
2.  **Discord Bot (`bot.py`)**: The user-facing component. It listens for commands on Discord and communicates with the backend API to fulfill user requests.

This separation of concerns ensures that the Discord bot remains responsive, even while a long video analysis is in progress.

## Features

-   **Video Analysis**: Provide a video URL, and the bot will give you a detailed description.
-   **Follow-up Questions**: Ask questions about the video you just analyzed.
-   **Backend API**: All core functionalities are exposed via a local API.
-   **Debug Mode**: An optional debug mode to display a performance report for each analysis step (download, encoding, analysis).

## Setup

### 1. Prerequisites

-   Python 3.8+
-   [uv](https://github.com/astral-sh/uv): A fast Python package installer and resolver.
-   [yt-dlp](https://github.com/yt-dlp/yt-dlp): For downloading videos.
-   [ffmpeg](https://ffmpeg.org/): Required by `yt-dlp` for processing video and audio streams.

Make sure `yt-dlp` and `ffmpeg` are installed and accessible in your system's PATH.

### 2. Installation

Clone the repository and install the required Python dependencies using `uv`.

```bash
# Clone the repository
git clone <repository_url>
cd ai-video-analyze-bot

# Install dependencies
uv sync
```

### 3. Configuration

Rename the `.env.example` file to `.env` and fill in the necessary API keys and configuration.

```
# Your Discord Bot Token
discord_token="YOUR_DISCORD_BOT_TOKEN"

# OpenAI Compatible API Key
openai_api_key="YOUR_API_KEY"

# (Optional) OpenAI Compatible API Base URL
openai_base_url="https://api.example.com/v1"

# (Optional) The model name to use for analysis
OPENAI_MODEL_NAME="gpt-4o"
```

## Usage

This project uses a launcher script (`main.py`) to start both the API server and the Discord bot simultaneously.

### Standard Mode

To run the application, simply execute:

```bash
python main.py
```

This will start both services. To stop them, press `Ctrl+C` in the terminal.

### Debug Mode

If you want to see a performance report (timing for download, encoding, analysis) with each result, you can start the application in debug mode by setting the `DEBUG_TIMING` environment variable.

```bash
DEBUG_TIMING=true python main.py
```

Now, your bot is running and ready to analyze videos!
