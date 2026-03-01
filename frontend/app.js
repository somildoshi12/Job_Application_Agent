document.addEventListener('DOMContentLoaded', () => {
    // --- State & DOM Elements ---
    const form = document.querySelector('#agent-form');
    
    // States
    const stateWelcome = document.querySelector('#welcome-state');
    const stateLoading = document.querySelector('#loading-state');
    const stateDashboard = document.querySelector('#dashboard');
    
    // Tab Navigation
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');
    
    // Dynamic Content Areas
    const jobsGrid = document.querySelector('#jobs-grid');
    const resumeAccordion = document.querySelector('#resume-accordion');
    const traceTimeline = document.querySelector('#trace-timeline');

    // --- Tab Switching Logic ---
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            // Remove active classes
            tabBtns.forEach(b => b.classList.remove('active'));
            tabContents.forEach(c => c.classList.remove('active'));
            
            // Add active to clicked
            btn.classList.add('active');
            const targetId = btn.getAttribute('data-tab');
            document.querySelector(`#tab-${targetId}`).classList.add('active');
        });
    });

    // --- Main Form Submission ---
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        // 1. Gather Data using FormData for file upload
        const formData = new FormData();
        formData.append('query', document.querySelector('#query').value);
        formData.append('location', document.querySelector('#location').value);
        formData.append('user_skills', document.querySelector('#skills').value);
        formData.append('target_top_k', 3);
        
        const fileInput = document.querySelector('#resume_file');
        if (fileInput.files.length > 0) {
            formData.append('resume_file', fileInput.files[0]);
        }

        // 2. Transition UI to Loading
        stateWelcome.classList.add('hidden');
        stateDashboard.classList.add('hidden');
        stateLoading.classList.remove('hidden');

        try {
            // 3. Make the API Call to our FastAPI backend
            console.log("Calling API endpoint...");
            const response = await fetch('http://localhost:8001/api/run-pipeline', {
                method: 'POST',
                // Browser automatically sets Content-Type to multipart/form-data with boundary
                body: formData
            });

            if (!response.ok) {
                throw new Error(`API Error: ${response.statusText}`);
            }

            const data = await response.json();
            console.log("API Response:", data);

            // 4. Render Data
            renderRankedJobs(data.ranked_jobs);
            renderTailoredResumes(data.tailored_applications, data.ranked_jobs);
            renderTraceLog(data.trace_log);

            // 5. Re-initialize feather icons for newly injected DOM elements
            feather.replace();

            // 6. Transition UI to Dashboard
            stateLoading.classList.add('hidden');
            stateDashboard.classList.remove('hidden');

        } catch (error) {
            console.error(error);
            alert("Error running the agent pipeline. Check the console and ensure FastAPI is running on port 8001.");
            // Reset to welcome state on error
            stateLoading.classList.add('hidden');
            stateWelcome.classList.remove('hidden');
        }
    });

    // --- Render Functions ---

    function renderRankedJobs(jobs) {
        jobsGrid.innerHTML = ''; // Clear previous
        
        jobs.forEach((job, index) => {
            // Parse extensions/skills safely
            const skillTags = job.skills.map(s => `<span class="tag">${s}</span>`).join('');
            
            const cardHtml = `
                <div class="job-card" style="animation: slideUp ${0.3 + (index * 0.1)}s ease">
                    <div class="job-header">
                        <div>
                            <h3 class="job-title">${job.title}</h3>
                            <div class="job-company">${job.company}</div>
                        </div>
                        <div class="score-badge">Matches ${job.score*100}%</div>
                    </div>
                    
                    <div class="meta-row mt-2">
                        <i data-feather="map-pin"></i> ${job.location}
                    </div>
                    
                    ${job.salary ? `<div class="meta-row"><i data-feather="dollar-sign"></i> ${job.salary}</div>` : ''}
                    
                    <div class="skills-tags mt-3">
                        ${skillTags}
                    </div>
                    
                    <a href="${job.url}" target="_blank" class="apply-btn mt-4">
                        View Original Application <i data-feather="external-link" style="width: 14px;"></i>
                    </a>
                </div>
            `;
            jobsGrid.insertAdjacentHTML('beforeend', cardHtml);
        });
    }

    function renderTailoredResumes(tailoredDict, rankedJobs) {
        resumeAccordion.innerHTML = '';
        
        // Match up the raw text with the job metadata
        for (const [jobId, tailoredObj] of Object.entries(tailoredDict)) {
            const jobData = rankedJobs.find(j => j.id === jobId);
            const companyName = jobData ? jobData.company : "Unknown Company";
            
            const cvText = tailoredObj.cover_letter || "";
            const tailoredDocxB64 = tailoredObj.tailored_docx_b64 || "";
            
            const combinedPreview = `# Cover Letter\n\n${cvText}\n\n# Tailored Resume\n\n*Direct in-place DOCX editing complete. Open the downloaded file to see your tailored resume in its original formatting!*`;
            
            const accordionHtml = `
                <div class="accordion-item">
                    <button class="accordion-header">
                        <span>Tailored Resume and Cover Letter for <strong>${companyName}</strong></span>
                        <i data-feather="chevron-down" class="accordion-icon"></i>
                    </button>
                    <div class="accordion-content">
                        <div class="accordion-inner">
                            <div style="display: flex; gap: 1rem; margin-bottom: 1rem;">
                                <button class="download-btn cv-btn primary-btn" style="width: auto; padding: 0.5rem 1rem;" data-company="${escapeHtml(companyName)}" data-type="Cover_Letter" data-text="${escapeHtml(cvText)}">
                                    <i data-feather="download"></i> Cover Letter (.DOCX)
                                </button>
                                <button class="download-btn resume-btn primary-btn" style="width: auto; padding: 0.5rem 1rem;" data-company="${escapeHtml(companyName)}" data-type="Tailored_Resume" data-b64="${escapeHtml(tailoredDocxB64)}">
                                    <i data-feather="download"></i> Tailored Resume (.DOCX)
                                </button>
                            </div>
                            <div style="white-space: pre-wrap;">${escapeHtml(combinedPreview)}</div>
                        </div>
                    </div>
                </div>
            `;
            resumeAccordion.insertAdjacentHTML('beforeend', accordionHtml);
        }

        // Add download action listeners
        const downloadBtns = resumeAccordion.querySelectorAll('.download-btn');
        downloadBtns.forEach(btn => {
            btn.addEventListener('click', async (e) => {
                e.preventDefault();
                const companyName = btn.getAttribute('data-company');
                const docType = btn.getAttribute('data-type');
                
                let endpoint = 'http://localhost:8001/api/download-docx';
                let payload = {};
                
                if (docType === "Tailored_Resume") {
                    endpoint = 'http://localhost:8001/api/download-tailored-docx';
                    payload = {
                        company_name: companyName,
                        b64_bytes: btn.getAttribute('data-b64')
                    };
                } else {
                    payload = {
                        company_name: companyName,
                        text: btn.getAttribute('data-text')
                    };
                }

                const response = await fetch(endpoint, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });

                if (response.ok) {
                    const blob = await response.blob();
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `${companyName.replace(/ /g, '_')}_${docType}.docx`;
                    document.body.appendChild(a);
                    a.click();
                    a.remove();
                    window.URL.revokeObjectURL(url);
                } else {
                    alert("Failed to download DOCX.");
                }
            });
        });

        // Add accordion interaction logic
        const headers = resumeAccordion.querySelectorAll('.accordion-header');
        headers.forEach(header => {
            header.addEventListener('click', () => {
                const item = header.parentElement;
                const content = header.nextElementSibling;
                
                // Toggle active class
                item.classList.toggle('active');
                
                if (item.classList.contains('active')) {
                    content.style.maxHeight = content.scrollHeight + 'px';
                } else {
                    content.style.maxHeight = '0';
                }
            });
        });
    }

    function renderTraceLog(traceLog) {
        traceTimeline.innerHTML = '';
        
        traceLog.forEach((trace, index) => {
            const actionClass = trace.action.toLowerCase(); // accepted, rejected, ranked, generated
            
            const iconMap = {
                'search': 'search',
                'filter': 'filter',
                'rank': 'bar-chart-2',
                'tailor': 'edit-3'
            };
            const icon = iconMap[trace.step.toLowerCase()] || 'check-circle';

            const traceHtml = `
                <div class="trace-item" style="animation: slideUp ${0.2 + (index * 0.05)}s ease">
                    <div class="trace-dot ${actionClass}"></div>
                    <div class="trace-card">
                        <h4 style="color: var(--text-primary)"><i data-feather="${icon}" style="width: 16px;"></i> [${trace.step}] ${trace.action}</h4>
                        <p>${trace.reason}</p>
                        <p style="font-size: 0.75rem; color: var(--text-muted); margin-top: 0.5rem">Job ID Cache: ${trace.job_id}</p>
                    </div>
                </div>
            `;
            traceTimeline.insertAdjacentHTML('beforeend', traceHtml);
        });
    }
    
    // Utility to prevent HTML injection in the LLM text
    function escapeHtml(unsafe) {
        if (!unsafe) return "";
        return String(unsafe)
             .replace(/&/g, "&amp;")
             .replace(/</g, "&lt;")
             .replace(/>/g, "&gt;")
             .replace(/"/g, "&quot;")
             .replace(/'/g, "&#039;");
    }
});
