import os
import sys
import argparse
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.eval_metrics import evaluate_ranking_model
from src.tailor_llm import tailor_application
from src.models import Job

def simulate_human_reviewers(job: Job, resume_text: str, cover_letter_text: str) -> dict:
    """
    Uses the LLM as a Judge to simulate 3 different Hiring Managers reviewing the 
    tailored resume and cover letter. They vote Yes or No for an interview.
    """
    import google.generativeai as genai
    import json
    
    current_api_key = os.getenv("GEMINI_API_KEY", "")
    if not current_api_key or current_api_key == "your_gemini_key_here":
        # Mock reviewers
        return {"reviewer_1": "Yes", "reviewer_2": "Yes", "reviewer_3": "No", "majority_decision": "Yes"}
        
    try:
        genai.configure(api_key=current_api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        prompt = f"""
        You are simulating 3 independent Hiring Managers at {job.company} reviewing an applicant for the role of {job.title}.
        
        JOB DESCRIPTION: {job.description}
        REQUIRED SKILLS: {', '.join(job.skills)}
        
        APPLICANT COVER LETTER:
        {cover_letter_text}
        
        APPLICANT RESUME:
        {resume_text}
        
        Based ONLY on how well the applicant's resume and cover letter match the job description, each of the 3 reviewers must independently vote "Yes" or "No" to interview this candidate.
        
        Return exactly ONE raw JSON object with no markdown formatting. Schema:
        {{
            "reviewer_1": "Yes" or "No",
            "reviewer_2": "Yes" or "No",
            "reviewer_3": "Yes" or "No",
            "majority_decision": "Yes" if 2 or more reviewers voted Yes, otherwise "No"
        }}
        """
        
        response = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
        return json.loads(response.text)
        
    except Exception as e:
        print(f"Error simulating reviewers: {e}")
        return {"reviewer_1": "No", "reviewer_2": "No", "reviewer_3": "No", "majority_decision": "No"}

def run_evaluation():
    load_dotenv()
    
    base_skills = ["Python", "Machine Learning", "AWS", "SQL", "Pandas"]
    csv_path = "data/benchmark_jobs.csv"
    
    print("\n--- Phase 1: Precision@10 Evaluation ---")
    metrics = evaluate_ranking_model(csv_path, base_skills)
    
    print(f"Total Jobs Evaluated: {metrics['total_jobs_evaluated']}")
    print(f"Precision@10: {metrics['precision_at_10'] * 100}%")
    
    print("\nTop 10 Ranked Jobs:")
    for rank, row in enumerate(metrics["top_10_results"]):
        # A hit is an "Interview" ground-truth appearing in the top 10
        hit = "✅ HIT" if row['expected'] == 'Interview' else "❌ MISS"
        print(f" {rank+1}. [{hit}] {row['title']} (Score: {row['score']:.2f})")
        
    print("\n--- Phase 2: Interview Yield Simulation ---")
    print("Selecting the top 3 jobs to simulate tailored applications and human review...")
    
    top_3_jobs = metrics["top_10_results"][:3]
    with open("data/sample_resume.docx", "rb") as f:
        # In a real script we would extract docx text. We mock it for the evaluator speed.
        base_resume_text = "Experienced Software Engineer skilled in Python, AWS, and Machine Learning."
    
    total_yield = 0
    
    for row in top_3_jobs:
        job = Job(id=row["id"], title=row["title"], company="Company", location="Remote", url="", description="Desc", skills=base_skills)
        print(f"\nEvaluating: {job.title}...")
        
        print(" -> Tailoring Resume via LLM...")
        tailored_data = tailor_application(job, base_resume_text)
        
        print(" -> Simulating 3 Human Reviewers...")
        yield_result = simulate_human_reviewers(job, tailored_data.get("tailored_resume", ""), tailored_data.get("cover_letter", ""))
        
        print(f"    Reviewer 1: {yield_result.get('reviewer_1')}")
        print(f"    Reviewer 2: {yield_result.get('reviewer_2')}")
        print(f"    Reviewer 3: {yield_result.get('reviewer_3')}")
        print(f"    Majority Decision: {yield_result.get('majority_decision')}")
        
        if yield_result.get("majority_decision", "No").lower() == "yes":
            total_yield += 1
            
    print(f"\nFINAL INTERVIEW YIELD: {total_yield}/3 ({(total_yield/3)*100:.1f}%)")

if __name__ == "__main__":
    run_evaluation()
