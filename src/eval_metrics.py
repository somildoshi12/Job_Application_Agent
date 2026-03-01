import pandas as pd
from typing import List, Tuple
from .models import Job
from .ranker import rank_jobs

def load_benchmark_jobs(csv_path: str) -> List[Tuple[Job, str]]:
    """Loads the CSV and returns a list of (Job_Object, Expected_Outcome)."""
    df = pd.read_csv(csv_path)
    jobs_with_ground_truth = []
    
    for _, row in df.iterrows():
        job = Job(
            id=str(row['id']),
            title=str(row['title']),
            company=str(row['company']),
            location=str(row['location']),
            description=str(row['description']),
            skills=[s.strip() for s in str(row['skills']).split(',')],
            url=f"http://example.com/job/{row['id']}"
        )
        jobs_with_ground_truth.append((job, str(row['expected_outcome'])))
        
    return jobs_with_ground_truth

def calculate_precision_at_k(ranked_jobs: List[Job], ground_truth: dict, k: int = 10) -> float:
    """
    Calculates Precision@k.
    In our binary classification case, an 'Interview' (relevant) correctly landing in the top K
    counts as a hit. Precision = Hits / K.
    """
    top_k_jobs = ranked_jobs[:k]
    hits = 0
    
    for job in top_k_jobs:
        if ground_truth.get(job.id) == "Interview":
            hits += 1
            
    return hits / k

def evaluate_ranking_model(csv_path: str, user_skills: List[str]) -> dict:
    """
    Runs the benchmark jobs through the Ranker module and returns P@10 metrics.
    """
    benchmark_data = load_benchmark_jobs(csv_path)
    
    # Isolate Job objects for the Ranker
    jobs_to_rank = [item[0] for item in benchmark_data]
    ground_truth_map = {item[0].id: item[1] for item in benchmark_data}
    
    # Run the real ML algorithm
    ranked_jobs = rank_jobs(jobs_to_rank, user_skills)
    
    # Calculate Metrics
    precision_10 = calculate_precision_at_k(ranked_jobs, ground_truth_map, k=10)
    
    return {
        "precision_at_10": precision_10,
        "total_jobs_evaluated": len(jobs_to_rank),
        "top_10_results": [
            {
                "id": j.id, 
                "title": j.title, 
                "score": j.score, 
                "expected": ground_truth_map.get(j.id)
            } 
            for j in ranked_jobs[:10]
        ]
    }
