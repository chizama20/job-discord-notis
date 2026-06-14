import requests

API_URL = "https://remoteok.com/api"

SWE_TAGS = {
    "software", "dev", "engineering", "backend", "frontend", "fullstack",
    "python", "javascript", "typescript", "golang", "rust", "java", "ruby",
    "react", "node", "api", "cloud", "devops", "sre", "data",
}

SWE_TITLE_KEYWORDS = (
    "engineer", "developer", "software", "swe", "backend", "frontend",
    "fullstack", "devops", "data engineer", "ml engineer",
)


def _is_swe(job: dict) -> bool:
    title = (job.get("position") or "").lower()
    tags = {t.lower() for t in (job.get("tags") or [])}
    if any(k in title for k in SWE_TITLE_KEYWORDS):
        return True
    return bool(tags & SWE_TAGS)


def fetch() -> list[dict]:
    try:
        resp = requests.get(API_URL, headers={"User-Agent": "job-alert-bot/1.0"}, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:
        print(f"[remoteok] fetch failed: {exc}")
        return []

    jobs = []
    for item in data:
        if not isinstance(item, dict) or not item.get("position"):
            continue
        if not _is_swe(item):
            continue
        url = item.get("url") or item.get("apply_url") or ""
        if not url:
            continue
        jobs.append({
            "title": item.get("position", ""),
            "company": item.get("company", ""),
            "location": item.get("location") or "Remote",
            "url": url,
            "source": "remoteok",
        })

    return jobs
