# Project Execution Log

## Initialization

- Set up project directory (`src/`, `app/`, `data/`, `docs/`, `scripts/`).
- Instantiated `.env` and `requirements.txt`.
- Set up API configurations (`config.py`).

## Phase 2: Core Pipeline Construction

- **Step 1 (Search Module):** Implemented `search_serpapi.py` and `extract.py` to pull job listings via SerpAPI with fallbacks to mock data. Extracted attributes to Pydantic models.
- **Step 2 (Filter Module):** Implemented `filter_rules.py` applying the FAANG blacklist and <50 employee startup heuristic.
- **Step 3 (Ranking Engine):** Implemented `ranker.py` using a weighted formula (0.6 Skill Match + 0.4 Location Match).
- **Step 4 (Applicant Simulation):** Implemented `tailor_llm.py` tying into Gemini API with prompt engineering to ethically reorganize the resume template based on the extracted job description. Built master `pipeline.py` which tracks all trace analytics via JSON files.

## Current Progress

## Phase 3: Evaluation & Benchmarking

- **Step 5 (Evaluation Framework):** Created `data/benchmark_jobs.csv` containing 20 ground-truth mocked jobs. Implemented `src/eval_metrics.py` to calculate `Precision@10` against the evaluation set and implemented `scripts/run_eval.py` to test it.

## Phase 4: UI & Deliverables

- **Step 6 (Streamlit Dashboard):** Built `app/streamlit_app.py` to provide a visual interface. It includes toggle inputs for query, location, and skills, runs the master pipeline, and displays the Agent Trace logs and mock LLM tailoring.
- **Step 7 (Final Scripts):** Created CLI launcher `scripts/run_pipeline.py` and finalized the `README.md`.

## Phase 5: Modern Web Application (Extension)

- **Step 8 (FastAPI Backend):** Created `api/main.py` which wraps the core pipeline into a REST API endpoint and handles CORS.
- **Step 9 (Premium Vanilla Frontend):** Hand-rolled a stunning user interface entirely in pure HTML, vanilla Javascript (`frontend/app.js`), and premium glassmorphic CSS (`frontend/styles.css`) that operates independently of Node/React architecture.
- **Step 10 (System Verification):** Ran live tests successfully, passing query state through Javascript to FastAPI, executing Serpent search and Gemini 2.5 LLM generation, and natively DOM-rendering the ranked cards, parsed trace payloads, and document accordions.
