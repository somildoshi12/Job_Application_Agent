import os
import json
from datetime import datetime
from typing import List, Dict, Any

from .models import Job, Decision
from .search_serpapi import search_jobs
from .extract import extract_jobs
from .filter_rules import evaluate_filters
from .ranker import rank_jobs
from .tailor_llm import tailor_application
from .docx_editor import apply_in_place_edits
import base64

def run_pipeline(query: str, location: str, user_skills: List[str], base_resume_text: str = "", base_resume_bytes: bytes = None, target_top_k: int = 3):
    trace_log: List[Decision] = []
    
    # STEP 1: Search & Extract
    print(f"Searching jobs for '{query}' in '{location}'...")
    raw_results = search_jobs(query, location)
    jobs = extract_jobs(raw_results)
    
    for job in jobs:
        trace_log.append(Decision(
            step="SEARCH", 
            action="Extracted", 
            reason=f"Found job '{job.title}' by '{job.company}'",
            job_id=job.id
        ))

    # STEP 2: Filter
    print("Filtering results...")
    filtered_jobs = []
    for job in jobs:
        passed, reason = evaluate_filters(job)
        if passed:
            filtered_jobs.append(job)
            trace_log.append(Decision(
                step="FILTER", action="Accepted", reason=reason, job_id=job.id
            ))
        else:
            trace_log.append(Decision(
                step="FILTER", action="Rejected", reason=reason, job_id=job.id
            ))
            
    # STEP 3: Rank
    print("Ranking results...")
    ranked_jobs = rank_jobs(filtered_jobs, user_skills)
    
    for rank, job in enumerate(ranked_jobs):
        trace_log.append(Decision(
            step="RANK", 
            action="Ranked", 
            reason=f"Rank {rank+1} with score {job.score}", 
            job_id=job.id
        ))

    # STEP 4: Tailor Top K
    print(f"Tailoring applications for top {target_top_k} jobs...")
    top_jobs = ranked_jobs[:target_top_k]
    
    tailored_results = {}
    for job in top_jobs:
        # 1. LLM Generation
        result = tailor_application(job, base_resume_text)
        
        # 2. In-Place DOCX Edit (if binary was provided)
        if base_resume_bytes and result.get("replacement_operations"):
            try:
                edited_bytes = apply_in_place_edits(base_resume_bytes, result["replacement_operations"])
                # We encode the binary to base64 so it can be serialized in the final JSON response payload
                result["tailored_docx_b64"] = base64.b64encode(edited_bytes).decode('utf-8')
            except Exception as e:
                print(f"Error applying in-place DOCX edits: {e}")
                
        tailored_results[job.id] = result
        
        trace_log.append(Decision(
            step="TAILOR", 
            action="Generated", 
            reason=f"Successfully generated tailored resume and changelog via LLM.", 
            job_id=job.id
        ))
        
    # Save Trace
    run_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    os.makedirs("data/runs", exist_ok=True)
    trace_file = f"data/runs/trace_{run_timestamp}.json"
    
    with open(trace_file, "w") as f:
        # Dump using Pydantic's built in model dump
        json.dump([t.model_dump() for t in trace_log], f, indent=4)
        
    print(f"Pipeline complete. Trace saved to {trace_file}")
    
    return {
        "ranked_jobs": ranked_jobs,
        "tailored_results": tailored_results,
        "trace_file": trace_file
    }
