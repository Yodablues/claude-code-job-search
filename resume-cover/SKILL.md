---
description: Tailor a resume and cover letter for a job posting
arguments:
  - name: url
    description: URL of the job posting
    required: true
---

# Resume & Cover Letter Generator

Create a tailored resume and cover letter for a specific job posting.

## Setup

Before first use, create a `config.json` in this skill's directory:

```json
{
  "name": "Your Name",
  "location": "City, State",
  "email": "you@example.com",
  "phone": "555-555-5555",
  "linkedin": "linkedin.com/in/your-profile",
  "website": "yoursite.com",
  "github": "github.com/you",
  "source_resume": "/path/to/Your_Resume.docx",
  "output_dir": "/path/to/output/directory"
}
```

## Inputs

- **Job posting URL:** $ARGUMENTS.url
- **Source resume:** path from `config.json` — extract text from this docx using
  python-docx or `python3 -c "import zipfile, xml.etree.ElementTree as ET; ..."`.
- **Docx generator script:** `generate_resume_cover.py` in this skill's directory.

## Steps

1. **Read config.json** from this skill's directory. All personal info comes from there.

2. **Fetch the job posting** from the provided URL using WebFetch. If the content
   doesn't load fully (dynamic pages), try WebSearch to find the posting on LinkedIn
   or other mirrors. Extract: job title, company, location, compensation,
   responsibilities, required qualifications, preferred qualifications.

3. **Read the source resume** by extracting text from the docx file. This is the
   user's master resume — use it as the factual basis. Never invent experience or
   skills that aren't in the source resume.

4. **Analyze the match.** Identify:
   - Strongest alignments with the role
   - Any gaps to address honestly (e.g., framework preferences)
   - Key language/phrases from the posting to mirror

5. **Tailor the resume.** Adjustments to make:
   - Rewrite the Professional Summary to lead with what matters most for THIS role
   - Reorder and reframe bullet points to emphasize relevant experience
   - Add relevant skills keywords from the posting to Technical Skills (only if
     genuinely possessed)
   - Trim older/less-relevant roles to keep it concise
   - Mirror the posting's language where authentic
   - Do NOT fabricate experience, inflate titles, or add skills not in the source

6. **Write the cover letter.** Structure:
   - Opening: specific interest in the role and company, 1-sentence positioning
   - 2-3 body paragraphs with bold lead-in phrases, each mapping a key requirement
     to concrete experience
   - If there's a notable gap, address it head-on with a confident reframe
   - Closing: why this company/role specifically, invitation to discuss
   - Tone: confident, specific, not sycophantic. Show don't tell.

7. **Generate .docx files** by running the generator script:
   ```
   python3 "<this skill dir>/generate_resume_cover.py" --config "<this skill dir>/config.json"
   ```
   First, write two intermediate files to the output directory:
   - `resume_tailored.json` — structured resume data
   - `cover_letter_tailored.json` — structured cover letter data

   See the script source for the exact JSON schemas.

8. **Report** the output file paths and a brief summary of tailoring choices made.

## Output files

All output goes to the configured `output_dir`:
- `{Name}_Resume_{CompanyName}_{ShortTitle}.docx`
- `{Name}_CoverLetter_{CompanyName}_{ShortTitle}.docx`

## Important rules

- ALWAYS output .docx format — never markdown, PDF, or plain text
- Use the source resume as the single source of truth for experience
- Never invent, exaggerate, or fabricate any experience or skills
- Keep the resume to 2 pages max
- Address gaps honestly rather than hiding them
