import os
from src.models import Job
from src.tailor_llm import tailor_application

test_job = Job(
    id="123",
    title="Test Job",
    company="Test Co",
    location="Texas",
    url="http",
    skills=["Python", "SQL"],
    description="Test.",
    score=1.0
)

print(f"Key loaded: {os.getenv('GEMINI_API_KEY', '')[:5]}...")
result = tailor_application(test_job, "I am a dev.")
print("Result Cover Letter length:", len(result.get("cover_letter", "")))
print("Result Tailored Resume length:", len(result.get("tailored_resume", "")))
