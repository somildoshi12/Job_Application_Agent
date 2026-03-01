import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
print(f"Loaded key: {GEMINI_API_KEY[:5]}...")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')
try:
    response = model.generate_content("Hello! Return {'hi': 'there'} strictly as JSON", generation_config={"response_mime_type": "application/json"})
    print("SUCCESS!")
    print(response.text)
except Exception as e:
    print(f"ERROR: {e}")
