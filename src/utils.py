import json
import re
from datetime import datetime

class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if hasattr(obj, "model_dump"):
            return obj.model_dump()
        return super().default(obj)

def normalize_text(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r'\s+', ' ', text).strip()
    return text.lower()

def safe_json_dump(data, filepath: str):
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=4, cls=CustomJSONEncoder)

def parse_date(date_str: str) -> datetime:
    try:
        from dateutil import parser
        return parser.parse(date_str)
    except Exception:
        return datetime.now()
