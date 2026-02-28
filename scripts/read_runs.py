from docx import Document

doc = Document('data/Somil_Resume.docx')
for i, p in enumerate(doc.paragraphs):
    if not p.text.strip(): continue
    print(f"Paragraph {i}:")
    for j, r in enumerate(p.runs):
        if r.text:
            bold = r.bold
            print(f"  Run {j} (bold={bold}): {r.text!r}")
