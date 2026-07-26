---
name: job-search
description: Find and triage remote senior/staff software engineering jobs for Tom Colarusso. Use whenever Tom says "find me jobs", "go find jobs", "any new roles", "search for jobs", or wants a fresh batch of job matches to review. Gathers postings from remote boards + company ATS feeds, filters to real fits against his resume and salary bar, and drives a one-by-one apply/reject triage.
---

# Job Search & Triage

Tom's ask: **"Claude, go find me jobs."** Do the searching, throw out bad matches
against his resume + pay bar, return a curated shortlist, then work them one-by-one
(apply or reject). Never auto-apply — applying is always Tom's explicit call.

## Tom's profile (judge fit against this)

- **Level:** Senior / Staff / Principal / Lead (IC). Open to Eng Manager too.
- **Stack:** Full-stack. Frontend-strong. **Vue + deep TypeScript** primary;
  **hands-on Python (FastAPI)**, C#/.NET, Node.js; **REST & GraphQL**; NoSQL
  (RavenDB/Redis); AWS (Lambda/serverless); Tailwind + Bootstrap; WCAG 2.1 AA
  accessibility; Vitest/Playwright/Storybook.
- **Differentiators:** frontend-platform / developer-productivity leadership
  (org-wide standards for 100+ engineers, 100+ component library); **Claude Code
  power user** who builds agentic AI tooling (skills, subagents, MCP servers,
  workflows); observability/performance (Datadog RUM/APM); 13+ yrs, B2B/fintech.
- **React:** willing to learn; currently ramping. Vue-first.

## Hard requirements (Tom's criteria)

1. **Salary $200k+** (base). If undisclosed, keep only if the level/company makes
   $200k+ plausible (most staff roles do) and flag as "salary unconfirmed".
2. **Fully remote**, US-eligible. Drop hybrid/onsite-only and non-US-only roles
   (flag any where US eligibility is unclear).
3. **Senior/Staff-level** engineering role that genuinely uses his stack.

## Workflow

1. **Gather.** Run the pre-filter script:
   `python "<this skill dir>/find_jobs.py"`
   It writes `job_candidates.json` (coarse keyword matches + description snippets +
   salary + links). This stage is dumb on purpose.
2. **Judge (this is the real value).** Read `job_candidates.json`. For each record,
   read the snippet and decide true fit against Tom's profile + hard requirements.
   **Aggressively drop garbage:** wrong level, non-remote, obvious stack mismatch
   (e.g. pure mobile/ML/embedded/Salesforce), staffing-agency spam, duplicates,
   sub-$200k when salary is disclosed. Prefer precision over volume — a tight list
   of real fits beats a long noisy one.
3. **Return a ranked shortlist.** For each survivor, one line:
   `Title @ Company — $salary (or "salary unconfirmed") — 1-phrase why it fits — link`.
   Rank by fit strength. Note any caveats (React-heavy, scope stretch, US-eligibility
   unclear). If the snippet is too thin to judge, fetch the full JD (Greenhouse/Ashby/
   Lever API or WebFetch) before deciding.
4. **Triage one-by-one.** Go through the shortlist with Tom. For each: **apply** or
   **reject**. Keep it quick.
5. **On "apply":** tailor from the master resume `C:\Users\comph\Documents\Tom_Colarusso_Resume.docx`
   using python-docx (copy -> edit summary/skills/bullets to the JD, save as
   `Tom_Colarusso_Resume_<Company>.docx`). Offer a matching cover letter (same
   letterhead builder, with live LinkedIn/website/GitHub/email links). Be honest —
   never fabricate skills; surface real gaps and flag anything that needs Tom's
   confirmation.

## Notes / maintenance

- Sources: RemoteOK + Remotive (cross-company remote) and per-company Greenhouse/
  Ashby/Lever feeds. There is no universal job API; LinkedIn/Indeed are not
  scrapable. To widen coverage, add company ATS tokens to the CONFIG lists in
  `find_jobs.py` (unknown tokens are skipped safely).
- Salary filtering is best-effort (many posts omit pay). The script extracts pay
  from text; when absent, Claude uses level/company judgment.
