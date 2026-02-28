import google.generativeai as genai
from .config import GEMINI_API_KEY
from .models import Job

def build_prompt(job: Job, base_resume_text: str) -> str:
    """Creates the prompt forcing the LLM to tailor the resume ethically."""
    return f"""
    You are an expert AI Job Application Agent.
    Your task is to tailor the candidate's base resume to the following job description.
    
    CRITICAL RULE: YOU MUST BE ETHICAL.
    You may ONLY reorder bullet points, change templates, or add industry keywords.
    You may NEVER invent experiences, skills, or jobs the candidate never had.
    
    JOB TITLE: {job.title}
    COMPANY: {job.company}
    JOB DESCRIPTION: {job.description}
    REQUIRED SKILLS: {', '.join(job.skills)}
    
    CANDIDATE's BASE RESUME:
    {base_resume_text}
    
    Output the tailored resume exactly as it should look. At the very end of your response, add a section called "///CHANGELOG///" where you list exactly what changes you made so the user can verify them.
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
        
        response = model.generate_content(prompt)
        return response.text
        
    except Exception as e:
        print(f"Error calling Gemini LLM: {e}. Falling back to mock data.")
        return f"MOCK TAILORED RESUME FOR: {job.title}\n\n[Base resume content reordered to emphasize {', '.join(job.skills)}]\n\n///CHANGELOG///\n- Emphasized Python and Machine Learning skills.\n- Reordered Data Engineering internship to top."
