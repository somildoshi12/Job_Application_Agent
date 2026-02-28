import os
from dotenv import load_dotenv

load_dotenv()

SERPAPI_KEY = os.getenv("SERPAPI_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini")

FAANG_BLACKLIST = [
    "google", "amazon", "apple", "netflix", "microsoft", "meta", "facebook", "openai", "alphabet"
]

PREFERRED_LOCATIONS = os.getenv("PREF_LOCATIONS", "Texas, Remote").split(",")
PREFERRED_LOCATIONS = [loc.strip() for loc in PREFERRED_LOCATIONS]

MAX_JOB_AGE_DAYS = int(os.getenv("MAX_JOB_AGE_DAYS", "14"))

USER_RESUME_PATH = "data/sample_resume.docx"
COVL_TEMPLATE_PATH = "data/sample_cover_letter.docx"
