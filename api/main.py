from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import os
import sys
import json

from fastapi.middleware.cors import CORSMiddleware

# Add parent directory to path so we can import the src logic
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.pipeline import run_pipeline

app = FastAPI(title="Job Application Agent API")

# Add CORS middleware to allow React to communicate with FastAPI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all origins for local dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PipelineRequest(BaseModel):
    query: str
    location: str
    user_skills: List[str]
    base_resume: str
    target_top_k: Optional[int] = 3

@app.post("/api/run-pipeline")
async def execute_pipeline(req: PipelineRequest):
    try:
        # Run the core logic
        results = run_pipeline(
            query=req.query,
            location=req.location,
            user_skills=req.user_skills,
            base_resume_text=req.base_resume,
            target_top_k=req.target_top_k
        )
        
        # Load the trace log from disk so we can return it sequentially
        trace_data = []
        if os.path.exists(results["trace_file"]):
            with open(results["trace_file"], "r") as f:
                trace_data = json.load(f)
                
        # We need to serialize the Pydantic Job objects into dicts for FastAPI to build the JSON response correctly
        ranked_jobs = [j.model_dump() for j in results["ranked_jobs"]]
                
        return {
            "status": "success",
            "ranked_jobs": ranked_jobs,
            "tailored_applications": results["tailored_results"],
            "trace_log": trace_data,
            "trace_file": results["trace_file"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def health_check():
    return {"status": "Agent API is live."}
