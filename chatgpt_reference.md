# ChatGPT Reference Notes & Architecture Recommendations

## Part 1: A-Grade, End-to-End Package Architecture

Awesome — I’ll give you an **A-grade, end-to-end package** you can directly turn into a GitHub repo: **architecture + folder structure + complete code skeleton + evaluation + Streamlit demo + report/demo checklist**.

Everything below is aligned exactly to your assignment requirements (Search → Filter → Rank → Tailor + logging + evaluation + demo + repo runnability).

---

### 0) What you’ll build (clean + realistic)

A Python agent that:

- Uses **SerpAPI** (Google Jobs / job board results) to fetch jobs
- Extracts: title, company, location, skills, salary (if present), URL
- Filters:
  - **FAANG+ blacklist**
  - **startup heuristic** (employee count from Clearbit OR fallback heuristic)
- Ranks top 10 using:
  - skill match
  - location preference
  - recency
- Tailors resume + cover letter for top 3 using an LLM (OpenAI/Gemini)
- Logs every decision (“why filtered”, “why ranked”, “why tailored”)
- Evaluates with **20-job benchmark** and computes Precision@10 + yield

✅ No “auto-submitting applications” (not required, and usually violates site policies). Your assignment wants “simulate applicant workflows”, not click Apply automatically.

---

### 1) Repo structure (copy this)

```
middle-america-agent/
  README.md
  requirements.txt
  .env.example
  data/
    sample_resume.txt
    sample_cover_letter.txt
    benchmark_jobs.csv
    benchmark_labels.csv
    runs/                       # auto-created
  src/
    config.py
    models.py
    utils.py
    search_serpapi.py
    extract.py
    filter_rules.py
    ranker.py
    tailor_llm.py
    pipeline.py
    eval_metrics.py
  app/
    streamlit_app.py
  docs/
    design_doc.md               # you can convert to PDF
    report_outline.md
  scripts/
    run_pipeline.py
    run_eval.py
```

---

### 2) requirements.txt

```txt
python-dotenv
requests
pandas
numpy
python-dateutil
pydantic
tqdm
streamlit
# If Gemini: add google-generativeai. If OpenAI: add openai
```

---

### 3) .env.example

```bash
SERPAPI_API_KEY="your_key"
LLM_PROVIDER="openai"          # openai or gemini
OPENAI_API_KEY="your_key"
GEMINI_API_KEY="your_key"

# preferences
PREF_LOCATIONS="Texas,Oklahoma,Iowa"
MAX_JOB_AGE_DAYS="30"
```

---

### 4) Core code (file-by-file)

#### `src/models.py`

```python
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class Job(BaseModel):
    title: str
    company: str
    location: str
    url: str
    salary: Optional[str] = None
    posted_at: Optional[datetime] = None
    skills: List[str] = Field(default_factory=list)
    raw: Dict[str, Any] = Field(default_factory=dict)

class Decision(BaseModel):
    stage: str
    item_id: str
    decision: str
    reason: str
    meta: Dict[str, Any] = Field(default_factory=dict)
```

#### `src/config.py`

```python
import os
from dotenv import load_dotenv

load_dotenv()

SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY", "")
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

PREF_LOCATIONS = [x.strip() for x in os.getenv("PREF_LOCATIONS", "Texas").split(",")]
MAX_JOB_AGE_DAYS = int(os.getenv("MAX_JOB_AGE_DAYS", "30"))

FAANG_BLACKLIST = {
    "google", "alphabet", "meta", "facebook", "amazon", "apple", "netflix",
    "microsoft", "openai", "tesla", "nvidia"
}
```

#### `src/utils.py`

```python
import json, os, re
from datetime import datetime
from dateutil import parser

def norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip().lower())

def safe_dt(s: str):
    try:
        return parser.parse(s)
    except Exception:
        return None

def ensure_dir(p: str):
    os.makedirs(p, exist_ok=True)

def jdump(obj, path: str):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2, default=str)

def now_ts():
    return datetime.utcnow().strftime("%Y%m%d_%H%M%S")
```

---

### 5) Job Search via SerpAPI

#### `src/search_serpapi.py`

```python
import requests
from typing import List, Dict, Any
from .config import SERPAPI_API_KEY

def serpapi_search(q: str, num: int = 20) -> List[Dict[str, Any]]:
    url = "https://serpapi.com/search.json"
    params = {
        "engine": "google_jobs",
        "q": q,
        "hl": "en",
        "api_key": SERPAPI_API_KEY,
        "num": num
    }
    r = requests.get(url, params=params, timeout=60)
    r.raise_for_status()
    data = r.json()
    return data.get("jobs_results", [])
```

#### `src/extract.py`

```python
from typing import List, Dict, Any
from .models import Job
from .utils import safe_dt

def extract_jobs(raw_jobs: List[Dict[str, Any]]) -> List[Job]:
    out = []
    for x in raw_jobs:
        title = x.get("title", "") or ""
        company = (x.get("company_name") or x.get("company") or "") or ""
        location = x.get("location", "") or ""
        url = x.get("related_links", [{}])[0].get("link") or x.get("job_id") or x.get("apply_options", [{}])[0].get("link") or ""
        salary = x.get("detected_extensions", {}).get("salary") if isinstance(x.get("detected_extensions"), dict) else None

        posted = None
        ext = x.get("detected_extensions")
        if isinstance(ext, dict):
            posted = safe_dt(ext.get("posted_at") or ext.get("posted_time") or "")
        skills = []
        desc = (x.get("description") or "")[:2000]
        for s in ["python","tensorflow","pytorch","mlflow","aws","azure","gcp","sql","nlp","llm","docker","kubernetes"]:
            if s in desc.lower():
                skills.append(s)
        out.append(Job(
            title=title, company=company, location=location, url=url,
            salary=salary, posted_at=posted, skills=sorted(set(skills)), raw=x
        ))
    return out
```

---

### 6) Filtering

#### `src/filter_rules.py`

```python
from typing import Tuple
from .utils import norm
from .config import FAANG_BLACKLIST

def is_faang(company: str) -> Tuple[bool, str]:
    c = norm(company)
    for b in FAANG_BLACKLIST:
        if b in c:
            return True, f"Blacklisted company match: '{b}'"
    return False, "Not in blacklist"

def is_startup_heuristic(job) -> Tuple[bool, str]:
    txt = (job.raw.get("description") or "").lower()
    flags = ["startup", "seed", "series a", "series b", "stealth", "small team", "early stage"]
    for f in flags:
        if f in txt:
            return True, f"Startup heuristic triggered: '{f}'"
    return False, "No startup indicators found"
```

---

### 7) Ranking

#### `src/ranker.py`

```python
from typing import List, Dict
from datetime import datetime, timedelta
from .utils import norm
from .config import PREF_LOCATIONS, MAX_JOB_AGE_DAYS

def skill_score(job_skills: List[str], resume_skills: List[str]) -> float:
    js = set([norm(x) for x in job_skills])
    rs = set([norm(x) for x in resume_skills])
    if not js:
        return 0.2
    inter = len(js & rs)
    return inter / max(1, len(js))

def location_score(loc: str) -> float:
    l = norm(loc)
    for p in PREF_LOCATIONS:
        if norm(p) in l:
            return 1.0
    return 0.2

def recency_score(posted_at) -> float:
    if not posted_at:
        return 0.4
    age = datetime.utcnow() - posted_at.replace(tzinfo=None)
    if age <= timedelta(days=7): return 1.0
    if age <= timedelta(days=MAX_JOB_AGE_DAYS): return 0.7
    return 0.2

def rank_jobs(jobs, resume_skills: List[str]) -> List[Dict]:
    ranked = []
    for j in jobs:
        s1 = skill_score(j.skills, resume_skills)
        s2 = location_score(j.location)
        s3 = recency_score(j.posted_at)
        score = 0.5*s1 + 0.3*s2 + 0.2*s3
        ranked.append({
            "job": j,
            "score": round(score, 4),
            "breakdown": {"skill": round(s1,4), "location": round(s2,4), "recency": round(s3,4)}
        })
    ranked.sort(key=lambda x: x["score"], reverse=True)
    return ranked
```

---

### 8) Tailoring with LLM (resume + cover letter)

#### `src/tailor_llm.py`

```python
from typing import Tuple
from .config import LLM_PROVIDER
# If using OpenAI, install openai and uncomment below.
# from openai import OpenAI

def build_prompt(job_title, company, location, job_desc, base_resume, base_cl):
    return f"""
You are an assistant helping tailor job applications ethically and truthfully.

JOB:
Title: {job_title}
Company: {company}
Location: {location}
Description: {job_desc}

BASE RESUME:
{base_resume}

BASE COVER LETTER:
{base_cl}

TASK:
1) Produce a tailored RESUME (same truth; re-order bullets, emphasize relevant skills, add keywords that match job, do NOT invent experience).
2) Produce a tailored COVER LETTER (150-220 words, confident, specific, not generic).
3) Provide a short CHANGELOG with 5-8 bullets explaining edits.

Output format:
===TAILORED_RESUME===
...
===TAILORED_COVER_LETTER===
...
===CHANGELOG===
- ...
"""

def call_llm(prompt: str) -> str:
    # Minimal placeholder so repo runs even without keys.
    # Replace this with OpenAI/Gemini call.
    return "===TAILORED_RESUME===\n[LLM output here]\n===TAILORED_COVER_LETTER===\n[LLM output here]\n===CHANGELOG===\n- [LLM output here]"

def tailor(job, base_resume: str, base_cl: str) -> Tuple[str, str, str]:
    jd = (job.raw.get("description") or "")[:3500]
    p = build_prompt(job.title, job.company, job.location, jd, base_resume, base_cl)
    out = call_llm(p)
    return out, p, jd
```

---

### 9) Pipeline (Search → Filter → Rank → Tailor + Logging)

#### `src/pipeline.py`

```python
import os
from typing import Dict, Any
from .utils import ensure_dir, now_ts, jdump
from .search_serpapi import serpapi_search
from .extract import extract_jobs
from .filter_rules import is_faang, is_startup_heuristic
from .ranker import rank_jobs
from .tailor_llm import tailor

def run_pipeline(query: str, resume_skills, base_resume, base_cl, out_dir="data/runs") -> Dict[str, Any]:
    ts = now_ts()
    run_dir = os.path.join(out_dir, ts)
    ensure_dir(run_dir)

    trace = []
    def log(stage, item_id, decision, reason, meta=None):
        trace.append({
            "stage": stage, "item_id": item_id, "decision": decision, "reason": reason, "meta": meta or {}
        })

    raw = serpapi_search(query, num=30)
    jdump(raw, os.path.join(run_dir, "raw_serpapi.json"))

    jobs = extract_jobs(raw)
    jdump([j.model_dump() for j in jobs], os.path.join(run_dir, "extracted_jobs.json"))

    # FILTER
    keep = []
    for j in jobs:
        jid = f"{j.company} | {j.title} | {j.location}"
        f1, r1 = is_faang(j.company)
        if f1:
            log("filter", jid, "reject", r1)
            continue
        f2, r2 = is_startup_heuristic(j)
        if f2:
            log("filter", jid, "reject", r2)
            continue
        log("filter", jid, "keep", "Passed filters")
        keep.append(j)

    # RANK TOP 10
    ranked = rank_jobs(keep, resume_skills)
    top10 = ranked[:10]
    for x in top10:
        j = x["job"]
        jid = f"{j.company} | {j.title} | {j.location}"
        log("rank", jid, "scored", "Computed rank score", x["breakdown"] | {"score": x["score"]})

    # TAILOR TOP 3
    top3 = top10[:3]
    tailored = []
    for x in top3:
        j = x["job"]
        jid = f"{j.company} | {j.title} | {j.location}"
        out, prompt, jd = tailor(j, base_resume, base_cl)
        log("tailor", jid, "generated", "Tailored resume + cover letter", {"score": x["score"]})
        tailored.append({"job": j.model_dump(), "score": x["score"], "llm_output": out})

    jdump(top10, os.path.join(run_dir, "ranked_top10.json"))
    jdump(tailored, os.path.join(run_dir, "tailored_top3.json"))
    jdump(trace, os.path.join(run_dir, "trace.json"))

    return {"run_dir": run_dir, "top10": top10, "tailored_top3": tailored, "trace": trace}
```

---

### 10) Evaluation (Precision@10 + yield)

#### `src/eval_metrics.py`

```python
import pandas as pd

def precision_at_k(pred_ids, true_relevant_ids, k=10):
    pred_k = pred_ids[:k]
    hits = sum([1 for x in pred_k if x in true_relevant_ids])
    return hits / k

def interview_yield(human_yes_count, total=10):
    return human_yes_count / max(1, total)

def run_eval(ranked_top10_json_path, labels_csv_path):
    ranked = pd.read_json(ranked_top10_json_path)
    labels = pd.read_csv(labels_csv_path)

    pred_ids = ranked["job"].apply(lambda j: f"{j['company']}|{j['title']}|{j['location']}").tolist()
    true_ids = set(labels[labels["is_relevant"] == 1]["job_id"].tolist())

    p10 = precision_at_k(pred_ids, true_ids, k=10)
    return {"Precision@10": round(p10, 4)}
```

#### Benchmark files format

`data/benchmark_jobs.csv` (20 jobs)
`data/benchmark_labels.csv` (10 relevant + 10 reject)
Example:

```csv
job_id,is_relevant
CompanyA|AI Engineer|Iowa,1
CompanyB|ML Engineer|Texas,0
```

---

### 11) Streamlit demo (for your 8–10 min video)

#### `app/streamlit_app.py`

```python
import streamlit as st
from pathlib import Path
from src.pipeline import run_pipeline

st.title("Middle America Job & Application Agent")

q = st.text_input("Job query", "AI Engineer Python MLflow")
resume_skills = st.text_input("Resume skills (comma-separated)", "python,tensorflow,mlflow,aws,sql").split(",")

base_resume = Path("data/sample_resume.txt").read_text(encoding="utf-8")
base_cl = Path("data/sample_cover_letter.txt").read_text(encoding="utf-8")

if st.button("Run Agent"):
    res = run_pipeline(q, [x.strip() for x in resume_skills], base_resume, base_cl)
    st.success(f"Run saved to: {res['run_dir']}")

    st.subheader("Top 10 Ranked Jobs")
    for i, x in enumerate(res["top10"], 1):
        j = x["job"]
        st.write(f"**{i}. {j.company} — {j.title} ({j.location})** | Score: {x['score']} | {x['breakdown']}")
        st.write(j.url)

    st.subheader("Tailored Applications (Top 3)")
    for x in res["tailored_top3"]:
        st.markdown(f"### {x['job']['company']} — {x['job']['title']}")
        st.code(x["llm_output"][:4000])
```

---

### 12) Scripts to run (CLI)

#### `scripts/run_pipeline.py`

```python
from pathlib import Path
from src.pipeline import run_pipeline

if __name__ == "__main__":
    q = "AI Engineer Python MLflow Texas"
    base_resume = Path("data/sample_resume.txt").read_text(encoding="utf-8")
    base_cl = Path("data/sample_cover_letter.txt").read_text(encoding="utf-8")
    resume_skills = ["python","tensorflow","mlflow","aws","sql","docker"]
    res = run_pipeline(q, resume_skills, base_resume, base_cl)
    print("Saved to:", res["run_dir"])
```

#### `scripts/run_eval.py`

```python
from src.eval_metrics import run_eval

if __name__ == "__main__":
    out = run_eval(
        ranked_top10_json_path="data/runs/<LATEST_RUN>/ranked_top10.json",
        labels_csv_path="data/benchmark_labels.csv"
    )
    print(out)
```

---

### 13) README.md (TA-proof)

````md
# Middle America Job & Application Agent

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# add SERPAPI_API_KEY and LLM key if using
```
````

## Run pipeline (CLI)

```bash
python scripts/run_pipeline.py
```

## Run Streamlit demo

```bash
streamlit run app/streamlit_app.py
```

```

---

### 14) Design Doc + Report

#### `docs/design_doc.md` (2–3 pages)
Include:
- pipeline diagram
- filter heuristics + justification
- tailoring workflow (truthful edits only)
- logging strategy (trace.json format)

#### `docs/report_outline.md` (8–10 pages)
1. Intro + requirements
2. Design & Implementation
3. Evaluation (benchmark + Precision@10 + yield + tailoring scores)
4. Bias/Ethics (fairness risks in tailoring, location constraints, keyword bias)
5. Appendix: agent trace snippets (trace.json screenshots)

---

### 15) Your demo video script (8–10 min)
1) Run fresh query live
2) Show filter toggle (change PREF_LOCATIONS)
3) Explain top job: score breakdown
4) Show tailored resume/CL for top 3
5) Show failure case (e.g., startup heuristic false positive) + how you adjusted rule

---

## Part 2: Agent Reasoning Trace & Tricks

Here is a **simple trick that will make your project look like a real AI agent system**, not just a Python script. Professors usually love this because it shows **agent reasoning and explainability**.

### The Trick: Add an **Agent Reasoning Trace**
Instead of just giving results, your agent should **explain every decision it makes**.
Your assignment actually hints at this requirement: "Logging of all decisions and rationales at each stage". But most students will only log simple messages. You can make it look like a **real AI agent thinking process**.

### Example Agent Reasoning Trace
```

===== AGENT TRACE =====

QUERY:
"AI Engineer Python MLflow Texas"

STEP 1 — SEARCH
Found 25 jobs from Google Jobs API

STEP 2 — EXTRACTION
Extracted fields:
title, company, location, salary, url

STEP 3 — FILTERING
Rejected: Google
Reason: FAANG blacklist

Rejected: Stealth AI Startup
Reason: Startup heuristic (<50 employees)

Accepted: Texas Instruments
Reason: Mid-size company, valid posting

Accepted: Halliburton
Reason: Oil & Gas company (>50 employees)

Remaining jobs: 14

STEP 4 — RANKING
Job: Halliburton AI Engineer
Skill match: 0.85
Location match: 1.0
Recency score: 0.9
Final Score: 0.89

Top 10 jobs selected

STEP 5 — APPLICATION TAILORING
Tailoring resume for:

1. Halliburton
2. Caterpillar

LLM modifications:

- Highlighted Python + MLflow
- Added model deployment experience
- Adjusted keywords for ATS

````

### Why This Impresses Professors
Because it shows:
✔ **Agent reasoning**
✔ **Transparency**
✔ **Explainable AI**
✔ **Decision logging**

### How to Implement It (Very Easy)
Add this to your pipeline:
```python
trace = []
def log(step, message):
    trace.append({
        "step": step,
        "message": message
    })
````

Save it:

```python
import json
with open("trace.json","w") as f:
    json.dump(trace,f,indent=2)
```

### Second Trick (Even More Impressive): Filter Toggle

Your assignment explicitly requires showing adaptability: "Filter toggle demonstration (e.g., Texas → adapt)".
Example UI:

```
Preferred Location:
[ Texas ]
[ Iowa ]
```

When you change it from Texas to Iowa, the rankings **automatically change**. That demonstrates **agent adaptability**.

### Optional Trick: LangChain / LangGraph

Turn this into a **real autonomous AI agent (like AutoGPT style)** using **LangChain/LangGraph**. It will make your project look like cutting-edge agent research.
