from fastapi import FastAPI, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import uvicorn
import os
import sys

# Add the project root to sys.path so we can import from 'core'
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.follower_tracker import track_growth

app = FastAPI(title="Instagram Analytics Backend")

# Initialize Scheduler
scheduler = BackgroundScheduler()

def scheduled_task():
    print(f"Running scheduled update at {os.popen('date').read().strip()}")
    track_growth()

# Schedule daily tracking at 9:00 AM IST (which is around 03:30 UTC depending on server time, but we'll use local time if possible)
# FastAPI scheduler usually uses local system time.
scheduler.add_job(func=track_growth, trigger="cron", hour=9, minute=0, id="daily_tracking", replace_existing=True)

@app.on_event("startup")
async def startup_event():
    if not scheduler.running:
        scheduler.start()
    print("Backend started. Scheduler is running.")

@app.on_event("shutdown")
async def shutdown_event():
    if scheduler.running:
        scheduler.shutdown()
    print("Backend shutting down.")

# Serve static files (HTML, etc.)
# Root-level files are served via FileResponse in routes below
# app.mount("/static", StaticFiles(directory="web"), name="static")

# Base directory for the project
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

@app.get("/")
async def read_index():
    return FileResponse(os.path.join(BASE_DIR, "index.html"))

@app.get("/activity.html")
async def read_activity_html():
    return FileResponse(os.path.join(BASE_DIR, "activity.html"))

@app.get("/index.html")
async def read_index_html():
    return FileResponse(os.path.join(BASE_DIR, "index.html"))

@app.post("/update")
async def trigger_update(background_tasks: BackgroundTasks):
    """Trigger a manual update of the tracker in the background."""
    background_tasks.add_task(track_growth)
    return {"message": "Update triggered in background"}

@app.get("/status")
async def get_status():
    """Check the status of the data files and scheduler."""
    return {
        "csv_exists": os.path.exists(os.path.join("data", "ig_growth_tracker_wide.csv")),
        "index_exists": os.path.exists(os.path.join(BASE_DIR, "index.html")),
        "activity_page_exists": os.path.exists(os.path.join(BASE_DIR, "activity.html")),
        "activity_exists": os.path.exists(os.path.join("data", "ig_activity_tracker.csv")),
        "scheduler_running": scheduler.running,
        "next_run": str(scheduler.get_job("daily_tracking").next_run_time) if scheduler.get_job("daily_tracking") else None
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
