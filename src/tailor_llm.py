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

def tailor_application(job: Job, base_resume_text: str) -> str:
    """Calls Gemini to generate the new resume and changelog."""
    
    if not GEMINI_API_KEY or GEMINI_API_KEY == "your_gemini_key_here":
        print("GEMINI_API_KEY not found or invalid. Using mock tailored response.")
        return f"MOCK TAILORED RESUME FOR: {job.title}\n\n[Base resume content reordered to emphasize {', '.join(job.skills)}]\n\n///CHANGELOG///\n- Emphasized Python and Machine Learning skills.\n- Reordered Data Engineering internship to top."
        
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-2.5-flash')
        prompt = build_prompt(job, base_resume_text)
        
        response = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
        
        import json
        out = json.loads(response.text)
        
        return {
            "cover_letter": out.get("cover_letter", ""),
            "replacement_operations": out.get("replacement_operations", [])
        }
        
    except Exception as e:
        print(f"Error calling Gemini LLM: {e}. Falling back to mock data.")
        return {
            "cover_letter": "Mock Cover Letter.",
            "replacement_operations": []
        }
