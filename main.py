import multiprocessing
import subprocess
import sys
import time
import os

def start_api():
    """Starts the FastAPI server using uvicorn."""
    print("Starting API server on http://127.0.0.1:8000...")
    # Using sys.executable ensures we use the python from the current environment
    command = [sys.executable, "-m", "uvicorn", "api:app", "--host", "127.0.0.1", "--port", "8000"]
    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        print(f"API server failed to start: {e}", file=sys.stderr)
    except FileNotFoundError:
        print("Error: 'uvicorn' command not found. Make sure it is installed.", file=sys.stderr)
        print(f"Attempted to run: {' '.join(command)}", file=sys.stderr)

def start_bot():
    """Starts the Discord bot."""
    # A small delay to ensure the API server is likely up and running.
    print("Waiting for API server to start...")
    time.sleep(5)
    print("Starting Discord bot...")
    command = [sys.executable, "bot.py"]
    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Bot failed to start: {e}", file=sys.stderr)
    except FileNotFoundError:
        print("Error: 'bot.py' not found.", file=sys.stderr)
        print(f"Attempted to run: {' '.join(command)}", file=sys.stderr)


if __name__ == "__main__":
    # Set start method for compatibility with macOS and Windows
    if sys.platform.startswith('darwin') or sys.platform.startswith('win'):
        multiprocessing.set_start_method('spawn')

    print("Launching API server and Discord bot...")
    
    api_process = multiprocessing.Process(target=start_api, name="API_Process")
    bot_process = multiprocessing.Process(target=start_bot, name="Bot_Process")

    api_process.start()
    bot_process.start()

    try:
        api_process.join()
        bot_process.join()
    except KeyboardInterrupt:
        print("\nShutting down services...")
        api_process.terminate()
        bot_process.terminate()
        api_process.join()
        bot_process.join()
        print("Services terminated.")