import os
import sys
import pandas as pd

# Add parent dir to path so we can import src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models import Job
from src.filter_rules import evaluate_filters
from src.ranker import rank_jobs
from src.eval_metrics import calculate_precision_at_k

def run_evaluation():
    csv_path = "data/benchmark_jobs.csv"
    if not os.path.exists(csv_path):
        print(f"Benchmark file not found at {csv_path}")
        return
        
    df = pd.read_csv(csv_path)
    
    # Simulate extraction phase
    jobs = []
    ground_truth_good_ids = []
    
    for idx, row in df.iterrows():
        job_id = str(row['job_id'])
        job = Job(
            id=job_id,
            title=str(row['title']),
            company=str(row['company']),
            location=str(row['location']),
            skills=["Python", "Machine Learning"], # Mock static skills for eval
            salary="N/A",
            url=f"http://example.com/{job_id}",
            description="Mock description"
        )
        jobs.append(job)
        
        if int(row['is_good_match']) == 1:
            ground_truth_good_ids.append(job_id)
            
    print(f"Loaded {len(jobs)} benchmark jobs.")
    print(f"Ground truth identifies {len(ground_truth_good_ids)} 'good' target jobs.\n")
    
    # Pipeline
    filtered_jobs = []
    for job in jobs:
        passed, _ = evaluate_filters(job)
        if passed:
            filtered_jobs.append(job)
            
    print(f"After filtering FAANG/Startups, {len(filtered_jobs)} jobs remain.")
    
    user_skills = ["Python", "SQL", "Machine Learning", "AWS"]
    ranked_jobs = rank_jobs(filtered_jobs, user_skills)
    
    # Calculate Metrics
    precision_10 = calculate_precision_at_k(ranked_jobs, ground_truth_good_ids, k=10)
    
    print("\n========= EVALUATION RESULTS =========")
    print(f"Precision@10: {precision_10 * 100}%")
    
    # Print the top 10 recommended
    print("\nTop 10 Researched Jobs vs Ground Truth:")
    for i, job in enumerate(ranked_jobs[:10]):
        is_hit = "✅ HIT" if job.id in ground_truth_good_ids else "❌ MISS"
        print(f"{i+1}. {job.company} - {job.title} | {is_hit}")

if __name__ == "__main__":
    run_evaluation()
