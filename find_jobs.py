#!/usr/bin/env python3
"""
find_jobs.py — GATHER stage for the job-search skill.

Casts a wide net across remote job boards and company ATS feeds, applies a
coarse pre-filter (seniority + engineering role + relevant tech + remote),
and writes candidates to job_candidates.json for Claude to judge.

All configuration is read from config.json (copy config.example.json to get
started). No third-party deps required (stdlib urllib only).
"""

import json
import os
import re
import sys
import time
import urllib.request
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(SCRIPT_DIR, "config.json")

# ----------------------------- load config ------------------------------------

def load_config():
    if not os.path.exists(CONFIG_PATH):
        print(f"ERROR: {CONFIG_PATH} not found.")
        print("Copy config.example.json to config.json and fill in your details.")
        sys.exit(1)
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return json.load(f)


CFG = load_config()

SENIORITY = CFG.get("search_keywords", {}).get("seniority",
    ["senior", "staff", "principal", "lead", "sr.", "sr "])
ROLE = CFG.get("search_keywords", {}).get("role",
    ["engineer", "developer", "swe", "software"])
TECH = CFG.get("search_keywords", {}).get("tech",
    ["react", "typescript", "javascript", "full stack", "fullstack",
     "full-stack", "front-end", "frontend", "node", "python"])
US_HINTS = CFG.get("search_keywords", {}).get("us_hints",
    ["us", "usa", "u.s", "united states", "anywhere", "worldwide",
     "north america", "remote"])

GREENHOUSE = CFG.get("sources", {}).get("greenhouse_tokens", [])
ASHBY = CFG.get("sources", {}).get("ashby_names", [])
LEVER = CFG.get("sources", {}).get("lever_tokens", [])
USE_REMOTEOK = CFG.get("sources", {}).get("remoteok", True)
USE_REMOTIVE = CFG.get("sources", {}).get("remotive", True)

RESUME_CFG = CFG.get("resume", {})
APPLIED_DIR = RESUME_CFG.get("applied_docs_dir", "")
RESUME_PATTERN = RESUME_CFG.get("resume_filename_pattern", "Resume_{company}.docx")
COVER_LETTER_PATTERN = RESUME_CFG.get("cover_letter_filename_pattern", "CoverLetter_{company}.docx")

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                     "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
      "Accept": "application/json,text/plain,*/*"}
TIMEOUT = 20
RETRIES = 3
SNIPPET_LEN = 700

# ----------------------------- helpers ----------------------------------------

def get(url):
    last = None
    for attempt in range(RETRIES):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=TIMEOUT) as r:
                return r.read().decode("utf-8", "replace")
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(1.5 * (attempt + 1))
    raise last


def _norm(s):
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def _extract_company_from_filename(filename):
    """Extract company token from a resume/cover-letter filename using the configured patterns."""
    for pattern in [RESUME_PATTERN, COVER_LETTER_PATTERN]:
        # Turn "Name_Resume_{company}.docx" into a regex
        escaped = re.escape(pattern).replace(r"\{company\}", r"(.+)")
        m = re.match(escaped, filename, re.I)
        if m:
            return _norm(m.group(1))
    return None


def applied_tokens():
    """Company tokens from tailored docs in APPLIED_DIR, to skip already-applied roles."""
    if not APPLIED_DIR or not os.path.isdir(APPLIED_DIR):
        return set()
    toks = set()
    try:
        for fn in os.listdir(APPLIED_DIR):
            tok = _extract_company_from_filename(fn)
            if tok:
                toks.add(tok)
    except Exception:
        pass
    return toks


def is_applied(company, toks):
    if not toks:
        return False
    c = _norm(company)
    return bool(c) and any(len(t) >= 4 and (t in c or c in t) for t in toks)


def strip_html(s):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s or "")).strip()


def extract_salary(text):
    if not text:
        return None
    t = text.replace(",", "")
    vals = [int(m) for m in re.findall(r"\$\s?(\d{5,7})\b", t)]
    vals += [int(m) * 1000 for m in re.findall(r"\$?\s?(\d{2,3})\s?[kK]\b", text)]
    plausible = [v for v in vals if 50_000 <= v <= 1_000_000]
    return max(plausible) if plausible else None


def coarse_match(title, blob):
    tl = title.lower()
    return (any(s in tl for s in SENIORITY)
            and any(r in tl for r in ROLE)
            and any(k in blob.lower() for k in TECH))


def us_remote(text):
    t = (text or "").lower()
    return any(h in t for h in US_HINTS)


def rec(title, company, desc, url, source, location, salary_text=""):
    return {
        "title": title, "company": company,
        "salary": extract_salary((salary_text or "") + " " + desc),
        "location": location or "Remote",
        "us": us_remote((location or "") + " " + desc[:400]),
        "url": url, "source": source,
        "snippet": strip_html(desc)[:SNIPPET_LEN],
    }


# ------------------------------ sources ---------------------------------------

def from_remoteok():
    out = []
    try:
        data = json.loads(get("https://remoteok.com/api"))[1:]
    except Exception:
        return out
    for j in data:
        title = j.get("position", "")
        blob = strip_html(j.get("description", "")) + " " + " ".join(j.get("tags", []))
        if coarse_match(title, blob):
            out.append(rec(title, j.get("company", ""), blob,
                           j.get("url") or j.get("apply_url", ""), "RemoteOK",
                           j.get("location") or "Remote"))
    return out


def from_remotive():
    out = []
    try:
        data = json.loads(get("https://remotive.com/api/remote-jobs?category=software-dev&limit=100"))
    except Exception:
        return out
    for j in data.get("jobs", []):
        title = j.get("title", "")
        blob = strip_html(j.get("description", "")) + " " + " ".join(j.get("tags", []))
        if coarse_match(title, blob):
            out.append(rec(title, j.get("company_name", ""), blob, j.get("url", ""),
                           "Remotive", j.get("candidate_required_location", ""),
                           j.get("salary", "")))
    return out


def from_greenhouse(token):
    out = []
    try:
        data = json.loads(get(f"https://boards-api.greenhouse.io/v1/boards/{token}/jobs?content=true"))
    except Exception:
        return out
    for j in data.get("jobs", []):
        title = j.get("title", "")
        loc = (j.get("location") or {}).get("name", "")
        content = strip_html(urllib.parse.unquote(j.get("content", "")))
        if "remote" in (loc + " " + content).lower() and coarse_match(title, content):
            out.append(rec(title, token.title(), content, j.get("absolute_url", ""),
                           "Greenhouse", loc))
    return out


def from_ashby(name):
    out = []
    try:
        data = json.loads(get("https://api.ashbyhq.com/posting-api/job-board/"
                              + urllib.parse.quote(name) + "?includeCompensation=true"))
    except Exception:
        return out
    for j in data.get("jobs", []):
        title = j.get("title", "")
        loc = j.get("location") or ""
        if not (j.get("isRemote") or "remote" in loc.lower()):
            continue
        desc = j.get("descriptionPlain") or strip_html(j.get("descriptionHtml", ""))
        if coarse_match(title, desc):
            out.append(rec(title, name, desc, j.get("applyUrl") or j.get("jobUrl", ""),
                           "Ashby", loc, json.dumps(j.get("compensation") or {})))
    return out


def from_lever(token):
    out = []
    try:
        data = json.loads(get(f"https://api.lever.co/v0/postings/{token}?mode=json"))
    except Exception:
        return out
    for j in data:
        title = j.get("text", "")
        cats = j.get("categories") or {}
        loc = cats.get("location", "")
        desc = j.get("descriptionPlain", "")
        if "remote" in (loc + " " + desc).lower() and coarse_match(title, desc):
            out.append(rec(title, token.title(), desc, j.get("hostedUrl", ""),
                           "Lever", loc, json.dumps(j.get("salaryRange") or {})))
    return out


def main():
    jobs = []
    with ThreadPoolExecutor(max_workers=16) as ex:
        futs = []
        if USE_REMOTEOK:
            futs.append(ex.submit(from_remoteok))
        if USE_REMOTIVE:
            futs.append(ex.submit(from_remotive))
        futs += [ex.submit(from_greenhouse, t) for t in GREENHOUSE]
        futs += [ex.submit(from_ashby, n) for n in ASHBY]
        futs += [ex.submit(from_lever, t) for t in LEVER]
        for f in as_completed(futs):
            try:
                jobs.extend(f.result())
            except Exception:
                pass

    seen, uniq = set(), []
    for j in jobs:
        k = (j["company"].lower(), j["title"].lower())
        if k not in seen:
            seen.add(k)
            uniq.append(j)

    # drop companies already applied to
    toks = applied_tokens()
    excluded = sorted({j["company"] for j in uniq if is_applied(j["company"], toks)})
    uniq = [j for j in uniq if not is_applied(j["company"], toks)]
    uniq.sort(key=lambda x: (-(x["salary"] or 0), x["company"]))

    out_path = os.path.join(SCRIPT_DIR, "job_candidates.json")
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(uniq, fh, indent=2)

    by_src = {}
    for j in uniq:
        by_src[j["source"]] = by_src.get(j["source"], 0) + 1
    print(f"Gathered {len(uniq)} coarse-matched candidates by source: {by_src}")
    print(f"With disclosed salary: {sum(1 for j in uniq if j['salary'])}")
    if excluded:
        print(f"Excluded (already applied): {', '.join(excluded)}")
    print(f"JSON written to: {out_path}")
    print("Next: Claude reads job_candidates.json and judges fit per record.")


if __name__ == "__main__":
    main()
