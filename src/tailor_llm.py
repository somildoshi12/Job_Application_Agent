import google.generativeai as genai
from .config import GEMINI_API_KEY
from .models import Job

def build_prompt(job: Job, base_resume_text: str) -> str:
    """Creates the prompt forcing the LLM to tailor the resume ethically in-place."""
    return f"""
    You are an expert AI Job Application Agent.
    Your task is to generate a custom cover letter and a list of exact text replacements to tailor the candidate's base resume to the following job description.
    
    CRITICAL RULE: YOU MUST BE ETHICAL.
    You may ONLY suggest replacing generic achievement metrics with targeted industry keywords found in the Job Description.
    You may NEVER invent experiences, skills, or jobs the candidate never had.
    
    JOB TITLE: {job.title}
    COMPANY: {job.company}
    JOB DESCRIPTION: {job.description}
    REQUIRED SKILLS: {', '.join(job.skills)}
    
    CANDIDATE's BASE RESUME:
    {base_resume_text}
    
    Return your response strictly as a JSON object with two keys:
    "cover_letter": a professionally written cover letter in markdown format.
    "replacement_operations": a JSON array of objects, where each object has "original_text" (the exact sub-string from the Base Resume you want to change) and "new_text" (the tailored replacement string). Keep replacements short and target specific phrases, not entire paragraphs.
    """

def tailor_application(job: Job, base_resume_text: str) -> dict:
    """Calls Gemini to generate a tailored resume, cover letter, and replacement ops."""
    import os
    from dotenv import load_dotenv
    load_dotenv()
    
    current_api_key = os.getenv("GEMINI_API_KEY", "")
    
    if not current_api_key or current_api_key == "your_gemini_key_here":
        print("GEMINI_API_KEY not found or invalid. Using mock tailored response.")
        return {
            "cover_letter": f"Mock Cover Letter for {job.title} at {job.company}.",
            "tailored_resume": f"# Mock Tailored Resume\n\nThis is a mock tailored resume for **{job.title}** at **{job.company}**.\n\n## Skills\n\n- {chr(10)+'- '.join(job.skills)}",
            "replacement_operations": [{"original_text": "Sample Data", "new_text": "Tailored Data"}]
        }
        
    try:
        genai.configure(api_key=current_api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')
        prompt = build_prompt(job, base_resume_text)
        
        response = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
        
        import json
        out = json.loads(response.text)
        
        return {
            "cover_letter": out.get("cover_letter", ""),
            "tailored_resume": out.get("tailored_resume", ""),
            "replacement_operations": out.get("replacement_operations", [])
        }
        
    except Exception as e:
        print(f"Error calling Gemini LLM: {e}. Falling back to mock data.")
        return {
            "cover_letter": "Mock Cover Letter.",
            "tailored_resume": f"Mock Tailored Resume for {job.title} at {job.company}.",
            "replacement_operations": [{"original_text": "Data Engineering", "new_text": "Data Engineering & Machine Learning"}]
        }
