import requests
from typing import List, Dict, Any
from .config import SERPAPI_KEY

def mock_search_jobs(query: str) -> List[Dict[str, Any]]:
    return [
        {
            "title": "Machine Learning Engineer",
            "company_name": "TechNova Industries",
            "location": "Austin, Texas",
            "description": "Looking for an ML engineer with PyTorch, Pandas, SQL and AWS experience. Fast-paced environment.",
            "extensions": ["Salary: $120k-$150k", "Full-time"],
            "share_link": "https://example.com/job1"
        },
        {
            "title": "Data Scientist",
            "company_name": "Google",
            "location": "Remote",
            "description": "Data Scientist role focusing on NLP and Machine Learning. Requires Python and TensorFlow.",
            "extensions": ["Salary: $140k", "Full-time"],
            "share_link": "https://example.com/job2"
        },
        {
            "title": "Software Engineer Intern",
            "company_name": "AI Startup",
            "location": "San Francisco, CA",
            "description": "We are a small startup with 10 employees. Fun culture. Python and Docker skills preferred.",
            "extensions": ["Internship"],
            "share_link": "https://example.com/job3"
        }
    ]

def search_jobs(query: str, location: str = "United States", num_results: int = 20) -> List[Dict[str, Any]]:
    if not SERPAPI_KEY or SERPAPI_KEY == "your_serpapi_key_here":
        print("SERPAPI_KEY not found or invalid. Using mock data.")
        return mock_search_jobs(query)

    try:
        url = "https://serpapi.com/search.json"
        params = {
            "engine": "google_jobs",
            "q": query,
            "location": location,
            "hl": "en",
            "api_key": SERPAPI_KEY,
            "num": num_results
        }
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        return data.get("jobs_results", [])
    except Exception as e:
        print(f"Error calling SerpAPI: {e}. Falling back to mock data.")
        return mock_search_jobs(query)
