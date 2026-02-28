from typing import List
from .models import Job

def calculate_precision_at_k(ranked_jobs: List[Job], ground_truth_ids: List[str], k: int = 10) -> float:
    """
    Calculates Precision@K.
    It takes the top K jobs returned by our ranker and checks how many of them 
    exist in the 'ground_truth_ids' (the list of known 'good' jobs).
    """
    top_k_jobs = ranked_jobs[:k]
    
    if not top_k_jobs:
        return 0.0
        
    hits = 0
    for job in top_k_jobs:
        if job.id in ground_truth_ids:
            hits += 1
            
    return hits / k

def calculate_interview_yield(tailored_applications: dict, success_rate_assumption: float = 0.25) -> float:
    """
    Simulates human evaluation for Interview Yield.
    If the agent generates 4 tailored applications, and we assume an extraordinarily 
    good tailored application gets a 25% callback rate, the yield is 4 * 0.25 = 1 Expected Interview.
    """
    num_applications_sent = len(tailored_applications)
    expected_interviews = num_applications_sent * success_rate_assumption
    return expected_interviews
