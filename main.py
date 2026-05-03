import asyncio
import sys

# Windows requires ProactorEventLoop for Playwright subprocess spawning
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uuid
from typing import Dict, Optional
from agent import ScrapingAgent

app = FastAPI(title="Agentic Web Scraper API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, replace with your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for jobs
# In a production app, this would be a database/Redis
jobs: Dict[str, Dict] = {}

class ScrapeRequest(BaseModel):
    url: str
    goal: str

class ScrapeResponse(BaseModel):
    job_id: str
    status: str

async def run_agent_job(job_id: str, url: str, goal: str):
    jobs[job_id]["status"] = "RUNNING"
    jobs[job_id]["steps"] = [
        {
            "thought": "Initializing agent and browser...",
            "code": None,
            "success": True,
            "result": "Browser starting..."
        }
    ]
    
    async def track_step(step_data):
        jobs[job_id]["steps"].append(step_data)
        jobs[job_id]["thought"] = step_data.get("thought") # For backward compat
        
    agent = ScrapingAgent(goal=goal, url=url, on_step=track_step)
    
    # Simple monkey-patch to capture final thought when DONE
    original_get_action = agent.get_action_from_gemini
    async def get_action_with_tracking(snapshot):
        action = await original_get_action(snapshot)
        jobs[job_id]["thought"] = action.get("thought")
        return action
    
    agent.get_action_from_gemini = get_action_with_tracking
    
    try:
        result = await agent.run()
        jobs[job_id]["status"] = "COMPLETED"
        jobs[job_id]["result"] = result
    except Exception as e:
        jobs[job_id]["status"] = "FAILED"
        jobs[job_id]["error"] = str(e)

@app.post("/scrape", response_model=ScrapeResponse)
async def create_scrape_job(request: ScrapeRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    jobs[job_id] = {
        "id": job_id,
        "status": "PENDING",
        "url": request.url,
        "goal": request.goal,
        "steps": [],
        "result": None,
        "error": None
    }
    
    background_tasks.add_task(run_agent_job, job_id, request.url, request.goal)
    
    return {"job_id": job_id, "status": "PENDING"}

@app.get("/status/{job_id}")
async def get_job_status(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return jobs[job_id]

@app.get("/jobs")
async def list_jobs():
    return list(jobs.values())

@app.delete("/jobs")
async def clear_jobs():
    jobs.clear()
    return {"message": "All jobs deleted"}

@app.delete("/jobs/{job_id}")
async def delete_job(job_id: str):
    if job_id in jobs:
        del jobs[job_id]
        return {"message": f"Job {job_id} deleted"}
    raise HTTPException(status_code=404, detail="Job not found")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False, loop="none")
