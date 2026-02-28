from typing import Tuple
from .models import Job
from .config import FAANG_BLACKLIST

def is_blocked_by_faang(job: Job) -> Tuple[bool, str]:
    """Filters out any FAANG companies based on blacklist."""
    company_lower = job.company.lower()
    for blocked_co in FAANG_BLACKLIST:
        if blocked_co in company_lower:
            return True, f"Blocked: Matches FAANG Blacklist ({blocked_co})."
    return False, ""

def is_startup(job: Job) -> Tuple[bool, str]:
    """
    Heuristic to determine if a company is a small startup.
    Since we don't have premium Clearbit API to fetch company headcount,
    we look for specific keywords in the description representing small startups.
    """
    desc = job.description.lower() if job.description else ""
    company = job.company.lower()
    
    startup_keywords = ["seed stage", "series a", "small startup", "< 50 employees", "early stage"]
    
    # We also explicitly check for "startup" combined with small numbers
    if "startup" in company or "startup" in desc:
        for kw in startup_keywords:
            if kw in desc:
                return True, f"Blocked: Matches Startup Heuristic ({kw})."
                
    return False, ""

def evaluate_filters(job: Job) -> Tuple[bool, str]:
    """
    Returns (Passed, Reason)
    If Passed is True, the job is kept.
    If Passed is False, the job is filtered out, with Reason explaining why.
    """
    is_faang, f_reason = is_blocked_by_faang(job)
    if is_faang:
        return False, f_reason
        
    is_st, st_reason = is_startup(job)
    if is_st:
        return False, st_reason
        
    return True, "Passed all filters."
