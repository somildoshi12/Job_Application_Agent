import streamlit as st
import json
import os
import sys

# Add parent dir to path so we can import src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.pipeline import run_pipeline

st.set_page_config(page_title="Job Application AI Agent", layout="wide")

st.title("🤖 Middle America Job & Application Agent")
st.markdown("An autonomous agent that searches, filters, ranks, and tailors job applications using agent-reasoning.")

# Sidebar Controls
st.sidebar.header("Agent Controls")
query = st.sidebar.text_input("Job Search Query", value="Machine Learning Engineer Python")
location = st.sidebar.text_input("Location Filter", value="Texas")
skills_input = st.sidebar.text_area("Your Skills (comma separated)", value="Python, PyTorch, SQL, AWS, Pandas, Docker")
user_skills = [s.strip() for s in skills_input.split(",")]

# Mock Resume Input 
mock_resume = st.sidebar.text_area("Base Resume Text (For LLM tailoring)", value="Alex Mercer. ML Engineer. 3 years experience with Python, PyTorch, and AWS. Built ETL pipelines and deployed models.", height=150)

if st.sidebar.button("Run AI Agent Pipeline"):
    st.info("Agent is actively searching, filtering, and tailoring...")
    
    with st.spinner("Executing Pipeline..."):
        # Run the pipeline
        results = run_pipeline(
            query=query, 
            location=location, 
            user_skills=user_skills, 
            base_resume_text=mock_resume,
            target_top_k=2 # Default to 2 to minimize mocked output length
        )
        
    st.success("Pipeline Execution Complete!")
    
    # Create Tabs
    tab1, tab2, tab3 = st.tabs(["🏆 Top Ranked Jobs", "📝 Tailored Applications", "🧠 Agent Reasoning Trace"])
    
    with tab1:
        st.subheader("Filtered & Ranked Opportunities")
        for i, job in enumerate(results["ranked_jobs"]):
            with st.expander(f"#{i+1}: {job.title} at {job.company} (Score: {job.score})"):
                st.write(f"**Location:** {job.location}")
                st.write(f"**Required Skills Extracted:** {', '.join(job.skills)}")
                st.write(f"**Salary Info:** {job.salary}")
                st.write(f"[Apply Link]({job.url})")
                st.write(f"**Description Snippet:** {job.description[:200]}...")
                
    with tab2:
        st.subheader("LLM Generated Tailored Resumes")
        for job_id, tailored_text in results["tailored_results"].items():
            job = next(job for job in results["ranked_jobs"] if job.id == job_id)
            with st.expander(f"Tailored Application for {job.company}"):
                st.write(tailored_text)
                
    with tab3:
        st.subheader("Agent Decision Log")
        st.markdown("*This trace log proves the agent evaluated constraints rather than using naive if/else loops.*")
        
        try:
            with open(results["trace_file"], "r") as f:
                trace_data = json.load(f)
                
            for trace in trace_data:
                color = "green" if trace["action"] in ["Accepted", "Ranked", "Generated"] else "red" if trace["action"] in ["Rejected"] else "blue"
                
                st.markdown(f"""
                <div style='border-left: 3px solid {color}; padding-left: 10px; margin-bottom: 10px;'>
                    <strong>[{trace['step']}] {trace['action']}</strong>: {trace['reason']}
                </div>
                """, unsafe_allow_html=True)
                
        except Exception as e:
            st.error(f"Could not load trace log: {e}")
