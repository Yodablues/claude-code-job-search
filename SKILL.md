---
name: job-search
description: Find and triage remote software engineering jobs. Gathers postings from remote boards + company ATS feeds, filters to real fits against the user's resume and salary requirements, and drives a one-by-one apply/reject triage.
---

# Job Search & Triage

The user's ask: **"Claude, go find me jobs."** Do the searching, throw out bad
matches against their profile + pay bar, return a curated shortlist, then work
them one-by-one (apply or reject). Never auto-apply — applying is always the
user's explicit call.

## Setup

This skill reads all configuration from `config.json` in the skill directory.
If it doesn't exist, tell the user to copy `config.example.json` to
`config.json` and fill in their details. The config contains:

- **profile** — level, stack, differentiators, years of experience
- **requirements** — minimum salary, remote-only, location eligibility
- **resume** — paths to master resume and directory for tailored docs
- **sources** — which job boards and company ATS feeds to query
- **search_keywords** — seniority/role/tech keywords for coarse filtering

Read `config.json` at the start of every run to get the user's current profile
and requirements. Use the profile to judge fit just as described below.

## Hard requirements (from config)

1. **Salary** at or above `requirements.min_salary` (base). If undisclosed,
   keep only if the level/company makes that salary plausible and flag as
   "salary unconfirmed".
2. **Fully remote**, eligible for the user's location. Drop hybrid/onsite-only
   and ineligible-location roles (flag any where eligibility is unclear).
3. **Appropriate level** engineering role that genuinely uses the user's stack.

## Workflow

1. **Gather.** Run the pre-filter script:
   `python "<this skill dir>/find_jobs.py"`
   It writes `job_candidates.json` (coarse keyword matches + description
   snippets + salary + links). This stage is intentionally broad.
2. **Judge (this is the real value).** Read `job_candidates.json`. For each
   record, read the snippet and decide true fit against the user's profile +
   hard requirements. **Aggressively drop garbage:** wrong level, non-remote,
   obvious stack mismatch (e.g. pure mobile/ML/embedded/Salesforce),
   staffing-agency spam, duplicates, sub-minimum salary when disclosed.
   Prefer precision over volume — a tight list of real fits beats a long noisy
   one.
3. **Return a ranked shortlist.** For each survivor, one line:
   `Title @ Company — $salary (or "salary unconfirmed") — 1-phrase why it fits — link`.
   Rank by fit strength. Note any caveats (stack mismatch, scope stretch,
   location-eligibility unclear). If the snippet is too thin to judge, fetch
   the full JD (Greenhouse/Ashby/Lever API or WebFetch) before deciding.
4. **Triage one-by-one.** Go through the shortlist with the user. For each:
   **apply** or **reject**. Keep it quick.
5. **On "apply":** If `resume.master_resume_path` is configured, tailor from
   that resume using python-docx (copy -> edit summary/skills/bullets to the
   JD, save using the configured filename pattern). Offer a matching cover
   letter. Be honest — never fabricate skills; surface real gaps and flag
   anything that needs the user's confirmation.

## Notes / maintenance

- Sources: RemoteOK + Remotive (cross-company remote) and per-company
  Greenhouse/Ashby/Lever feeds. There is no universal job API; LinkedIn/Indeed
  are not scrapable. To widen coverage, add company ATS tokens to the source
  lists in `config.json` (unknown tokens are skipped safely).
- Salary filtering is best-effort (many posts omit pay). The script extracts
  pay from text; when absent, Claude uses level/company judgment.
