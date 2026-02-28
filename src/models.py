from pydantic import BaseModel, HttpUrl
from typing import List, Optional

class Job(BaseModel):
    id: str
    title: str
    company: str
    location: str
    skills: List[str]
    salary: Optional[str] = None
    url: str
    description: Optional[str] = None
    score: float = 0.0

class Decision(BaseModel):
    step: str
    action: str
    reason: str
    job_id: str
