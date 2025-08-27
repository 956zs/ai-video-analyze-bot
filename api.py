import asyncio
import uuid
import os
import time
from fastapi import FastAPI, BackgroundTasks, Depends
from pydantic import BaseModel
from typing import Dict, Any
from contextlib import asynccontextmanager

from load_config import openai_api_key, openai_base_url
from analyze import VideoAnalyzer
from download_video import download_video, remove_video

# --- Globals for state management ---
# In a production environment, consider using Redis or a database instead of in-memory dicts.
tasks: Dict[str, Dict[str, Any]] = {}
analyzers: Dict[str, VideoAnalyzer] = {}
OPENAI_MODEL_NAME = os.getenv("OPENAI_MODEL_NAME", "[EXPRESS] gemini-2.5-pro")
DEBUG_TIMING = os.getenv("DEBUG_TIMING", "false").lower() in ("true", "1", "t")

# --- FastAPI App Initialization ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start a background task to clean up old tasks
    asyncio.create_task(cleanup_old_tasks())
    yield
    # Any cleanup on shutdown can go here

app = FastAPI(lifespan=lifespan)

# --- Pydantic Models ---
class AnalyzeRequest(BaseModel):
    video_url: str

class AskRequest(BaseModel):
    task_id: str
    question: str

# --- Background Task for Video Analysis ---
async def run_analysis(task_id: str, url: str):
    """
    This function runs in the background to download, encode, and analyze the video.
    It also records the time taken for each step.
    """
    video_filename = None
    start_time = time.time()
    try:
        # 1. Download the video
        tasks[task_id]["status"] = "downloading"
        # Run synchronous download in a thread to avoid blocking the event loop
        video_filename = await asyncio.to_thread(download_video, url)
        download_end_time = time.time()
        if not video_filename:
            tasks[task_id]["status"] = "failed"
            tasks[task_id]["result"] = "Download Failed: The video might be private, region-locked, or the URL is invalid."
            return

        # 2. Send to analysis
        tasks[task_id]["status"] = "analyzing"
        analyzer = VideoAnalyzer(api_key=openai_api_key, base_url=openai_base_url, model_name=OPENAI_MODEL_NAME)
        analyzers[task_id] = analyzer # Store the analyzer instance for follow-up questions
        
        reply_text = await analyzer.analyze_video_from_path(video_filename)
        analysis_end_time = time.time()

        # 3. Format timing report and store the results
        download_duration = download_end_time - start_time
        analysis_duration = analysis_end_time - download_end_time
        total_duration = analysis_end_time - start_time

        tasks[task_id]["status"] = "completed"
        if DEBUG_TIMING:
            timing_report = (
                f"\n\n---\n"
                f"**⏱️ Timing Report:**\n"
                f"- Download: `{download_duration:.2f}s`\n"
                f"- Analysis: `{analysis_duration:.2f}s`\n"
                f"**- Total: `{total_duration:.2f}s`**"
            )
            tasks[task_id]["result"] = reply_text + timing_report
        else:
            tasks[task_id]["result"] = reply_text

    except Exception as e:
        print(f"An unexpected error occurred during analysis for task {task_id}: {e}")
        tasks[task_id]["status"] = "failed"
        tasks[task_id]["result"] = f"An unexpected error occurred: {e}"
    finally:
        # 5. Clean up the downloaded file
        if video_filename:
            # Run synchronous remove in a thread
            await asyncio.to_thread(remove_video, video_filename)

# --- Background Task for Cleanup ---
async def cleanup_old_tasks():
    """
    Periodically cleans up tasks and analyzers that are older than a certain threshold.
    """
    while True:
        await asyncio.sleep(3600)  # Run every hour
        now = time.time()
        task_ids_to_delete = []
        for task_id, task_data in tasks.items():
            # Check if 'start_time' exists and if the task is older than 1 hour
            if "start_time" in task_data and (now - task_data["start_time"]) > 3600:
                task_ids_to_delete.append(task_id)

        for task_id in task_ids_to_delete:
            if task_id in tasks:
                del tasks[task_id]
            if task_id in analyzers:
                del analyzers[task_id]
        if task_ids_to_delete:
            print(f"Cleaned up {len(task_ids_to_delete)} old tasks.")

# --- API Endpoints ---
@app.post("/analyze")
async def analyze_video(request: AnalyzeRequest):
    task_id = str(uuid.uuid4())
    tasks[task_id] = {"status": "pending", "result": None, "start_time": time.time()}
    asyncio.create_task(run_analysis(task_id, request.video_url))
    return {"task_id": task_id, "message": "Video analysis started."}

@app.get("/status/{task_id}")
async def get_status(task_id: str):
    task = tasks.get(task_id)
    if not task:
        return {"error": "Task not found"}
    return {"task_id": task_id, "status": task["status"]}

@app.get("/result/{task_id}")
async def get_result(task_id: str):
    task = tasks.get(task_id)
    if not task:
        return {"error": "Task not found"}
    if task["status"] != "completed":
        return {"error": f"Task is still in progress with status: {task['status']}"}
    return {"task_id": task_id, "status": task["status"], "result": task["result"]}

@app.post("/ask")
async def ask_question(request: AskRequest):
    task_id = request.task_id
    question = request.question

    analyzer = analyzers.get(task_id)
    if not analyzer:
        return {"error": "Analyzer not found for this task. The task may have failed, not exist, or you need to analyze a video first."}

    try:
        # Running async function in a sync context from the main thread
        reply = await analyzer.ask_question(question)
        return {"task_id": task_id, "answer": reply}
    except Exception as e:
        print(f"Error during follow-up for task {task_id}: {e}")
        return {"error": f"Could not get a response. {e}"}