import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.tailor_llm import tailor_application
from src.models import Job

def evaluate_tailoring_quality():
    """
    Simulates a human HR professional comparing a standard, untailored baseline resume
    against the AI Agent's custom-tailored resume, scoring the improvement from 1 to 5.
    """
    import google.generativeai as genai
    import json
    from dotenv import load_dotenv
    load_dotenv()
    
    current_api_key = os.getenv("GEMINI_API_KEY", "")
    
    base_skills = ["Python", "Machine Learning", "AWS", "SQL", "Pandas"]
    job = Job(id="eval_1", title="Senior Machine Learning Engineer", company="TechAI", location="Remote", url="", description="Looking for a Senior ML Engineer to optimize LLM training pipelines.", skills=["Python", "LLM", "AWS"])
    
    baseline_resume = "Software Developer with 4 years of experience. I know Python, Data Science, AWS, and basic ML algorithms."
    
    print(f"\nEvaluating Tailoring Quality for: {job.title}")
    print(" -> Generating AI Tailored Resume...")
    
    tailored_data = tailor_application(job, baseline_resume)
    tailored_resume = tailored_data.get("tailored_resume", "")
    
    if not current_api_key or current_api_key == "your_gemini_key_here":
        print("\n[MOCK] Score: 5/5")
        print("[MOCK] Justification: The tailored resume correctly highlights LLM skills context over the baseline.")
        return
        
    try:
        genai.configure(api_key=current_api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        prompt = f"""
        You are an HR Executive evaluating AI-generated resumes.
        
        JOB DESCRIPTION: {job.description}
        REQUIRED SKILLS: {', '.join(job.skills)}
        
        BASELINE RESUME (Manually written by applicant):
        {baseline_resume}
        
        AGENT-TAILORED RESUME:
        {tailored_resume}
        
        Compare the Baseline Resume to the Agent-Tailored Resume. Did the Agent successfully restructure the document to better match the job description without inventing fake experiences?
        
        Score the Tailoring Quality from 1 to 5, where:
        1 = Worse than baseline (Invented lies or ruined formatting)
        3 = Minor optimizations, but mostly the same
        5 = Excellent. Perfect emphasis on required skills without hallucinating.
        
        Return exactly ONE raw JSON object with no markdown formatting. Schema:
        {{
            "score": Integer between 1 and 5,
            "justification": "1 sentence explaining the score"
        }}
        """
        
        print(" -> Simulating HR Executive Scoring...")
        response = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
        result = json.loads(response.text)
        
        print(f"\n✅ SCORE: {result.get('score')}/5")
        print(f"📝 JUSTIFICATION: {result.get('justification')}")
        
    except Exception as e:
        print(f"Error evaluating tailoring: {e}")

if __name__ == "__main__":
    evaluate_tailoring_quality()
