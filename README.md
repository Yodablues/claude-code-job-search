# claude-code-job-search

A [Claude Code](https://claude.ai/code) skill that finds remote software engineering jobs, filters them against your resume and salary requirements, and walks you through a triage workflow — all from your terminal.

It queries public job APIs (RemoteOK, Remotive, Greenhouse, Ashby, Lever), applies a coarse keyword filter, then hands the results to Claude to judge real fit against your profile. You get a ranked shortlist and go through it one-by-one: apply or reject.

## What you get

- **Automated sourcing** from 5+ job board APIs, parallelized
- **Coarse pre-filter** by seniority, role type, tech stack, and remote status
- **Claude-powered fit scoring** against your actual profile (not just keyword matching)
- **Already-applied detection** — skips companies you've already applied to based on tailored resume files on disk
- **Resume tailoring** on "apply" — copies your master resume and adjusts it for the role (requires [python-docx](https://python-docx.readthedocs.io/))

## Installation

```bash
# Clone into your Claude Code skills directory
git clone https://github.com/YOUR_USERNAME/claude-code-job-search ~/.claude/skills/job-search

# Create your config
cd ~/.claude/skills/job-search
cp config.example.json config.json
```

Edit `config.json` with your details:

- **profile** — your level, tech stack, differentiators, years of experience
- **requirements** — minimum salary, remote-only preference, location eligibility
- **resume** — path to your master resume `.docx` and the directory where tailored copies go
- **sources** — which job boards and company ATS feeds to query (add/remove companies freely — unknown tokens are skipped)
- **search_keywords** — seniority, role, and tech keywords for the coarse filter

## Usage

In Claude Code, just say:

```
/job-search
```

Or any variation: "find me jobs", "go find jobs", "any new roles", "search for jobs".

Claude will:
1. Run the gather script to pull fresh postings
2. Read the results and aggressively filter against your profile
3. Present a ranked shortlist
4. Walk through each match for you to apply or reject
5. On "apply", tailor your resume and draft a cover letter

## Requirements

- [Claude Code](https://claude.ai/code) (CLI, desktop app, or IDE extension)
- Python 3.8+ (stdlib only — no pip install needed)
- [python-docx](https://python-docx.readthedocs.io/) (only needed for resume tailoring: `pip install python-docx`)

## Adding company ATS feeds

The script queries company career pages via their public ATS APIs. To add companies, put their board token/name in the appropriate list in `config.json`:

- **Greenhouse** (`greenhouse_tokens`): The URL slug from `boards.greenhouse.io/{token}` — e.g. `"stripe"`, `"discord"`
- **Ashby** (`ashby_names`): The company name from their job board — e.g. `"Linear"`, `"Vercel"`
- **Lever** (`lever_tokens`): The URL slug from `jobs.lever.co/{token}` — e.g. `"netflix"`

Unknown or invalid tokens are silently skipped, so it's safe to add speculative entries.

## How it works

```
/job-search
    │
    ├── find_jobs.py          # GATHER: hits APIs, coarse keyword filter
    │   └── job_candidates.json   # raw candidates (gitignored)
    │
    └── Claude (SKILL.md)     # JUDGE: reads candidates, scores fit,
                              # presents shortlist, drives triage
```

The gather script is intentionally dumb — it casts a wide net with simple keyword matching. The real value is in Claude's judgment step, where it reads each job description against your full profile and drops the noise.

## License

MIT
