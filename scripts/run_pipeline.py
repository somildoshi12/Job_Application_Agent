import os
import sys

# Add parent dir to path so we can import src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.pipeline import run_pipeline

if __name__ == "__main__":
    print("=== Running Job Agent Pipeline via CLI ===")
    
    query = "Machine Learning Engineer"
    location = "Texas"
    user_skills = ["Python", "Machine Learning", "AWS", "SQL", "Pandas"]
    base_resume = "Alex Mercer... ML Engineer... Python... Used AWS."
    
    results = run_pipeline(query, location, user_skills, base_resume, target_top_k=2)
    
    print(f"\nPipeline successfully finished. View trace at {results['trace_file']}.")
