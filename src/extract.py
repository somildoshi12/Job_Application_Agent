from typing import List, Dict, Any
import hashlib
from .models import Job

def safe_extract_salary(extensions: List[str]) -> str:
    for ext in extensions:
        if "salary" in ext.lower() or "$" in ext:
            return ext
    return None
    
def safe_extract_skills(description: str) -> List[str]:
    common_skills = ["python", "java", "c++", "sql", "aws", "docker", "kubernetes", "react", "machine learning", "pytorch", "tensorflow", "pandas"]
    found_skills = []
    desc_lower = description.lower() if description else ""
    for skill in common_skills:
        if skill in desc_lower:
            found_skills.append(skill.title())
    return found_skills

def extract_jobs(raw_jobs: List[Dict[str, Any]]) -> List[Job]:
    extracted_jobs = []
    
    for rj in raw_jobs:
        # Create a deterministic ID if none provided
        title = rj.get("title", "Unknown Title")
        company = rj.get("company_name", "Unknown Company")
        job_id = rj.get("job_id") or hashlib.md5(f"{title}_{company}".encode()).hexdigest()
        
        description = rj.get("description", "")
        extensions = rj.get("extensions", [])
        
        salary = safe_extract_salary(extensions)
        skills = safe_extract_skills(description)
        
        job = Job(
            id=job_id,
            title=title,
            company=company,
            location=rj.get("location", "Unknown Location"),
            skills=skills,
            salary=salary,
            url=rj.get("share_link", ""),
            description=description,
            score=0.0
        )
        extracted_jobs.append(job)
        
    return extracted_jobs
