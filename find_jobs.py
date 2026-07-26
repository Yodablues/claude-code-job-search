#!/usr/bin/env python3
"""
find_jobs.py — GATHER stage for the job-search skill.

This script only casts a wide net and does a coarse pre-filter (seniority +
engineering role + relevant tech + remote). It deliberately does NOT decide fit
quality — Claude reads the emitted snippets and judges each against the
candidate's resume + salary bar.

Output: writes job_candidates.json (full records w/ snippets) next to this
script and prints a short summary. No third-party deps (urllib only).
Edit CONFIG to tune criteria or add companies (unknown ATS tokens are skipped).
"""

import json
import os
import re
import time
import urllib.request
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed

# ----------------------------- CONFIG ---------------------------------------
SENIORITY = ["senior", "staff", "principal", "lead", "sr.", "sr ", "distinguished"]
ROLE = ["engineer", "developer", "swe", "software"]
TECH = ["vue", "react", "typescript", "javascript", "full stack", "fullstack",
        "full-stack", "front-end", "frontend", "node", "python"]
US_HINTS = ["us", "usa", "u.s", "united states", "anywhere", "worldwide",
            "north america", "remote"]

GREENHOUSE = [
    # --- original ---
    "stripe", "airbnb", "reddit", "brex", "ramp", "gusto", "benchling",
    "discord", "robinhood", "coinbase", "databricks", "cloudflare",
    "twilio", "asana", "figma", "dropbox", "instacart", "affirm",
    "gitlab", "hashicorp", "shopify", "datadog", "doordash", "pinterest",
    "block", "elastic", "mongodb", "confluent", "samsara", "airtable",
    "webflow", "contentful", "sourcegraph", "postman", "grafanalabs",
    "render", "zapier", "retool", "mercury", "chime", "kraken", "okta",
    "cockroachlabs", "niantic", "roblox", "unity", "gemini", "plaid",
    # --- expanded: big tech / late-stage ---
    "netlify", "supabase", "vercel", "deno", "fly", "railway",
    "launchdarkly", "stytch", "axiom", "posthog", "planetscale",
    "neon", "turso", "upstash", "convex", "clerk", "inngest",
    "temporal", "prefect", "dagster", "modal", "anyscale", "replicate",
    "huggingface", "anthropic", "openai", "mistral",
    # --- fintech / payments ---
    "marqeta", "toast", "adyen", "wise", "remitly", "melio",
    "bill", "rippling", "justworks", "paylocity", "carta",
    "braintree", "lithic", "moderntreasury", "column", "increase",
    "unit", "treasuryprime", "synctera", "bond", "highnote",
    # --- B2B SaaS / productivity ---
    "notion", "coda", "clickup", "linear", "height", "shortcut",
    "loom", "miro", "mural", "canva", "grammarly", "calendly",
    "typeform", "airtable", "smartsheet", "monday", "lattice",
    "rippling", "gusto", "deel", "remote", "oysterhr", "justworks",
    "greenhouse", "lever", "ashbyhq", "gem", "dover",
    # --- developer tools / infra ---
    "hashicorp", "snyk", "sonar", "sentry", "circleci", "buildkite",
    "pulumi", "env0", "spacelift", "firehydrant", "rootly", "blameless",
    "pagerduty", "opsgenie", "squadcast", "honeycomb", "lightstep",
    "chronosphere", "cribl", "mezmo", "logdna", "coralogix",
    "launchdarkly", "split", "statsig", "eppo", "growthbook",
    "stytch", "workos", "fusionauth", "descope", "authzed",
    "zesty", "vantage", "cloudhealth", "spot", "cast",
    # --- data / analytics ---
    "dbt-labs", "fivetran", "airbyte", "census", "hightouch",
    "hex", "mode", "sigma", "lightdash", "cube", "metabase",
    "preset", "atlan", "alation", "collibra", "immuta",
    "snowflake", "motherduck", "clickhouse", "timescale", "questdb",
    # --- security ---
    "crowdstrike", "sentinelone", "lacework", "orca", "wiz",
    "snyk", "veracode", "checkmarx", "semgrep", "endor",
    "bitwarden", "1password", "dashlane", "keeper",
    # --- AI / ML companies ---
    "scale", "labelbox", "weights-and-biases", "mlflow",
    "pinecone", "weaviate", "qdrant", "chroma", "zilliz",
    "langchain", "llamaindex", "fixie", "dust", "vellum",
    "jasper", "writer", "copy-ai", "runway", "stability",
    "midjourney", "elevenelabs", "assemblyai", "deepgram",
    "glean", "moveworks", "adept", "cognition", "poolside",
    # --- e-commerce / marketplace ---
    "etsy", "poshmark", "mercari", "offerup", "depop",
    "faire", "shein", "fanatics", "goat", "stockx",
    "shipbob", "shippo", "easypost", "narvar",
    # --- health tech ---
    "oscar", "devoted", "cityblock", "ro", "hims",
    "truepill", "capsule", "alto", "amazon-pharmacy",
    "flatiron", "tempus", "veracyte", "grail",
    # --- education ---
    "duolingo", "coursera", "udemy", "masterclass", "khan",
    "replit", "codecademy", "brilliant",
    # --- misc remote-friendly ---
    "automattic", "zapier", "buffer", "doist", "toggl",
    "hotjar", "convertkit", "transistor", "fathom",
    "fly", "render", "railway", "coolify",
    "planetscale", "neon", "xata", "turso",
    "expo", "eas", "tamagui", "nativewind",
]
ASHBY = [
    # --- original ---
    "Gray Swan AI", "Linear", "Vercel", "Replit",
    "Retool", "Mercury", "Perplexity AI", "Cursor", "Cohere", "Notion", "Deel",
    # --- expanded ---
    "Ramp", "Anthropic", "OpenAI", "Mistral AI", "Anduril",
    "Supabase", "PostHog", "Deno", "Clerk", "Convex",
    "Inngest", "Axiom", "Neon", "Turso", "Upstash",
    "Fly.io", "Railway", "Render", "Coolify",
    "Stytch", "WorkOS", "Descope", "AuthZed",
    "Warp", "Fig", "Zed", "GitButler",
    "Temporal", "Prefect", "Dagster", "Modal",
    "Dust", "Vellum", "LangChain", "LlamaIndex",
    "Glean", "Harvey", "Casetext", "EvenUp",
    "Weights & Biases", "Pinecone", "Weaviate", "Chroma",
    "AssemblyAI", "Deepgram", "ElevenLabs", "Stability AI",
    "Scale AI", "Labelbox", "Replicate", "Together AI",
    "Braintrust", "Humanloop", "Helicone", "Langfuse",
    "Resend", "Loops", "Svix", "Knock", "Novu",
    "Cal.com", "Formbricks", "Documenso", "Eraser",
    "Doppler", "Infisical", "GitGuardian",
    "Secureframe", "Drata", "Vanta", "Launchnotes",
    "Hightouch", "Census", "Rudderstack", "Segment",
    "Hex", "Sigma Computing", "Lightdash", "Cube",
    "Atlan", "Monte Carlo", "Bigeye", "Metaplane",
    "Flatfile", "OneSchema", "Osmos",
    "Plain", "Intercom", "Front", "Missive",
    "Stripe", "Plaid", "Unit", "Lithic", "Increase",
    "Modern Treasury", "Column", "Synctera", "Highnote",
    "Carta", "Pulley", "AngelList", "Wellfound",
    "Remote", "Oyster", "Deel", "Plane",
    "Lattice", "Culture Amp", "15Five", "Leapsome",
    "Ashby", "Gem", "Dover", "Greenhouse",
    "Liveblocks", "Tldraw", "Excalidraw",
    "Trigger.dev", "Defer", "Qstash",
    "Mintlify", "ReadMe", "Stoplight", "Bump.sh",
    "Grafbase", "Hasura", "Stellate", "WunderGraph",
    "EdgeDB", "SurrealDB", "CockroachDB",
    "PlanetScale", "Xata", "Fauna",
]
LEVER = [
    # --- original ---
    "veeva", "plaid", "netflix", "nerdwallet", "attentive", "gopuff",
    # --- expanded ---
    "netlify", "sanity", "contentful", "strapi", "storyblok",
    "algolia", "typesense", "meilisearch",
    "auth0", "okta", "onelogin",
    "twilio", "sendgrid", "messagebird", "vonage",
    "segment", "amplitude", "mixpanel", "heap", "fullstory",
    "launchdarkly", "split", "statsig", "optimizely",
    "fastly", "akamai", "bunny",
    "circleci", "semaphore", "harness", "codefresh",
    "sonarqube", "codeclimate", "deepsource",
    "snyk", "bridgecrew", "checkov",
    "tailscale", "twingate", "zscaler",
    "loom", "pitch", "gamma", "beautiful",
    "calendly", "savvycal", "reclaim",
    "linear", "shortcut", "clickup", "height",
    "notion", "coda", "slite",
    "figma", "framer", "webflow", "bubble",
    "retool", "internal", "appsmith", "tooljet",
    "supabase", "firebase", "convex",
    "prisma", "drizzle", "kysely",
    "vercel", "netlify", "render", "railway",
    "fly", "modal", "replicate", "banana",
    "weights-and-biases", "comet", "neptune",
    "huggingface", "roboflow", "labelbox",
    "jasper", "writer", "copy-ai", "anyword",
    "grammarly", "textio", "hemingway",
    "wise", "remitly", "airwallex", "payoneer",
    "marqeta", "lithic", "highnote", "unit",
    "brex", "divvy", "ramp", "airbase",
    "toast", "square", "clover", "lightspeed",
    "shopify", "bigcommerce", "swell", "medusa",
    "faire", "handshake", "firstbase",
    "calm", "headspace", "noom", "peloton",
    "duolingo", "coursera", "udemy", "skillshare",
    "automattic", "ghost", "substack", "beehiiv",
    "doist", "todoist", "toggl", "clockify",
    "buffer", "hootsuite", "sprout", "later",
    "hotjar", "smartlook", "mouseflow", "clarity",
    "convertkit", "mailchimp", "customer-io", "braze",
    "intercom", "zendesk", "freshworks", "helpscout",
    "pagerduty", "opsgenie", "betteruptime",
    "sentry", "bugsnag", "rollbar", "raygun",
    "datadog", "newrelic", "dynatrace", "elastic",
    "hashicorp", "pulumi", "crossplane", "env0",
    "terraform", "spacelift", "scalr",
    "docker", "rancher", "portainer",
    "gitpod", "codespaces", "coder", "devpod",
    "doppler", "infisical", "vault",
    "tailscale", "ngrok", "cloudflared",
]

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                     "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
      "Accept": "application/json,text/plain,*/*"}
TIMEOUT = 20
RETRIES = 3                # retry transient failures / rate limits with backoff
# Companies manually marked as already applied (no tailored doc on disk)
MANUAL_APPLIED = {"grafana", "grafanalabs", "github"}
# Directory scanned to auto-exclude companies already applied to (tailored docs present)
APPLIED_DIR = r"C:\Users\comph\Documents"
# Filename suffix tokens that are role descriptors / housekeeping, not companies
EXCLUDE_STOPWORDS = {"backup", "principal", "stafffrontend", "master"}
SNIPPET_LEN = 700
# ----------------------------------------------------------------------------


def get(url):
    last = None
    for attempt in range(RETRIES):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=TIMEOUT) as r:
                return r.read().decode("utf-8", "replace")
        except Exception as e:  # noqa: BLE001 - transient (rate limit / network); back off
            last = e
            time.sleep(1.5 * (attempt + 1))
    raise last


def _norm(s):
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def applied_tokens():
    """Company tokens from tailored docs in APPLIED_DIR, to skip already-applied roles."""
    toks = set()
    try:
        for fn in os.listdir(APPLIED_DIR):
            m = re.match(r"Tom_Colarusso_(?:Resume|CoverLetter)_(.+)\.docx$", fn, re.I)
            if m:
                tok = _norm(m.group(1))
                if tok and tok not in EXCLUDE_STOPWORDS:
                    toks.add(tok)
    except Exception:
        pass
    toks.update(MANUAL_APPLIED)
    return toks


def is_applied(company, toks):
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


# ------------------------------ sources -------------------------------------
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
    with ThreadPoolExecutor(max_workers=32) as ex:
        futs = [ex.submit(from_remoteok), ex.submit(from_remotive)]
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

    # drop companies already applied to (tailored docs on disk)
    toks = applied_tokens()
    excluded = sorted({j["company"] for j in uniq if is_applied(j["company"], toks)})
    uniq = [j for j in uniq if not is_applied(j["company"], toks)]
    uniq.sort(key=lambda x: (-(x["salary"] or 0), x["company"]))

    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "job_candidates.json")
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(uniq, fh, indent=2)

    by_src = {}
    for j in uniq:
        by_src[j["source"]] = by_src.get(j["source"], 0) + 1
    print(f"Gathered {len(uniq)} coarse-matched candidates (after exclusions) by source: {by_src}")
    print(f"With disclosed salary: {sum(1 for j in uniq if j['salary'])}")
    print(f"Excluded (already applied): {', '.join(excluded) if excluded else 'none'}")
    print(f"JSON written to: {out_path}")
    print("Next: Claude reads job_candidates.json and judges fit per record.")


if __name__ == "__main__":
    main()
