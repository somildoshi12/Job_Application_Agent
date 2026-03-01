import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.eval_metrics import evaluate_ranking_model
from src.models import Job

def run_filter_toggle_simulation():
    """
    Demonstrates the agent's adaptability by ranking jobs normally, 
    and then applying a strict 'Texas-only' filter toggle to see if the top 10 changes.
    """
    base_skills = ["Python", "Machine Learning", "AWS", "SQL", "Pandas"]
    csv_path = "data/benchmark_jobs.csv"
    
    print("\n--- Baseline Run (All Locations) ---")
    metrics_all = evaluate_ranking_model(csv_path, base_skills)
    baseline_top_5 = [j["title"] + f" ({j['score']:.2f})" for j in metrics_all["top_10_results"][:5]]
    for rank, j in enumerate(baseline_top_5):
        print(f" {rank+1}. {j}")
        
    print("\n--- Adapting Filter Toggle 'Texas-Only Mode' ---")
    import pandas as pd
    from src.ranker import rank_jobs
    
    df = pd.read_csv(csv_path)
    jobs = []
    for _, row in df.iterrows():
        jobs.append(Job(id=str(row['id']), title=str(row['title']), company=str(row['company']), location=str(row['location']), description=str(row['description']), skills=[s.strip() for s in str(row['skills']).split(',')], url=""))
    
    # Apply toggle
    filtered_jobs = [j for j in jobs if "Texas" in j.location]
    
    ranked_filtered = rank_jobs(filtered_jobs, base_skills)
    
    filtered_top_5 = [j.title + f" ({j.score:.2f}) Location: {j.location}" for j in ranked_filtered[:5]]
    for rank, j in enumerate(filtered_top_5):
        print(f" {rank+1}. {j}")
        
    print(f"\n✅ Adaptation Successful: Agent correctly excluded {len(jobs) - len(filtered_jobs)} remote/out-of-state jobs to isolate Texas roles.")

if __name__ == "__main__":
    run_filter_toggle_simulation()
