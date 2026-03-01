from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
import os
import sys
import json
import io

import docx
import PyPDF2
from fpdf import FPDF
import markdown2

from fastapi.middleware.cors import CORSMiddleware

# Add parent directory to path so we can import the src logic
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.pipeline import run_pipeline

app = FastAPI(title="Job Application Agent API")

# Add CORS middleware to allow React to communicate with FastAPI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all origins for local dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/run-pipeline")
async def execute_pipeline(
    query: str = Form(...),
    location: str = Form(...),
    user_skills: str = Form(...),
    target_top_k: int = Form(3),
    resume_file: UploadFile = File(...)
):
    try:
        content = await resume_file.read()
        filename = resume_file.filename.lower()
        
        base_resume_text = ""
        if filename.endswith(".pdf"):
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
            for page in pdf_reader.pages:
                base_resume_text += page.extract_text() + "\n"
        elif filename.endswith(".docx") or filename.endswith(".doc"):
            doc = docx.Document(io.BytesIO(content))
            for para in doc.paragraphs:
                base_resume_text += para.text + "\n"
        elif filename.endswith(".txt"):
            base_resume_text = content.decode('utf-8')
        else:
            raise HTTPException(400, "Unsupported file type. Please upload PDF, DOCX, or TXT.")

        skills_list = [s.strip() for s in user_skills.split(",")]

        # Run the core logic
        results = run_pipeline(
            query=query,
            location=location,
            user_skills=skills_list,
            base_resume_text=base_resume_text,
            target_top_k=target_top_k
        )
        
        # Load the trace log from disk so we can return it sequentially
        trace_data = []
        if os.path.exists(results["trace_file"]):
            with open(results["trace_file"], "r") as f:
                trace_data = json.load(f)
                
        # We need to serialize the Pydantic Job objects into dicts for FastAPI to build the JSON response correctly
        ranked_jobs = [j.model_dump() for j in results["ranked_jobs"]]
                
        return {
            "status": "success",
            "ranked_jobs": ranked_jobs,
            "tailored_applications": results["tailored_results"],
            "trace_log": trace_data,
            "trace_file": results["trace_file"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class DocxRequest(BaseModel):
    text: str
    company_name: str

@app.post("/api/download-pdf")
def download_pdf(req: DocxRequest):
    """Generates a .pdf file on the fly from the tailored text response"""
    pdf = FPDF()
    pdf.add_page()
    
    # Add generic fallback fonts
    pdf.set_font("Helvetica", size=11)
    
    # Clean up unsupported unicode chars that break standard PDF encoding
    replacements = {
        '•': '-', '—': '-', '–': '-', '’': "'", '‘': "'", '“': '"', '”': '"', '…': '...'
    }
    safe_text = req.text
    for k, v in replacements.items():
        safe_text = safe_text.replace(k, v)
    safe_text = safe_text.encode('latin-1', 'ignore').decode('latin-1')
    
    # Convert LLM Markdown output to basic HTML for the PDF engine
    html_content = markdown2.markdown(safe_text)
    
    try:
        pdf.write_html(html_content)
    except Exception as e:
        # Fallback to plain text if HTML parsing fails due to complex markdown
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Helvetica", size=11)
        for line in safe_text.split('\n'):
            pdf.multi_cell(0, 5, txt=line)
            
    pdf_bytes = pdf.output()
    file_stream = io.BytesIO(pdf_bytes)
    
    filename = f"Application_{req.company_name.replace(' ', '_')}.pdf"
    
    return StreamingResponse(
        file_stream, 
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@app.get("/")
def health_check():
    return {"status": "Agent API is live."}
