import requests

GREENHOUSE_URL = "https://boards-api.greenhouse.io/v1/boards/{slug}/jobs"
LEVER_URL = "https://api.lever.co/v0/postings/{slug}"

HEADERS = {"User-Agent": "job-alert-bot/1.0"}


def _fetch_greenhouse(company: dict) -> list[dict]:
    slug = company["slug"]
    name = company["name"]
    try:
        resp = requests.get(
            GREENHOUSE_URL.format(slug=slug),
            params={"content": "false"},
            headers=HEADERS,
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:
        print(f"[greenhouse] {name} ({slug}) fetch failed: {exc}")
        return []

    jobs = []
    for item in data.get("jobs", []):
        location = ""
        offices = item.get("offices") or item.get("location", {})
        if isinstance(offices, list) and offices:
            location = offices[0].get("name", "")
        elif isinstance(offices, dict):
            location = offices.get("name", "")

        url = item.get("absolute_url") or item.get("url") or ""
        if not url:
            continue
        jobs.append({
            "title": item.get("title", ""),
            "company": name,
            "location": location,
            "url": url,
            "source": "greenhouse",
            "priority": company.get("priority", False),
        })
    return jobs


def _fetch_lever(company: dict) -> list[dict]:
    slug = company["slug"]
    name = company["name"]
    try:
        resp = requests.get(
            LEVER_URL.format(slug=slug),
            headers=HEADERS,
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:
        print(f"[lever] {name} ({slug}) fetch failed: {exc}")
        return []

    jobs = []
    for item in data:
        categories = item.get("categories") or {}
        location = categories.get("location") or categories.get("team") or ""
        url = item.get("hostedUrl") or item.get("applyUrl") or ""
        if not url:
            continue
        jobs.append({
            "title": item.get("text", ""),
            "company": name,
            "location": location,
            "url": url,
            "source": "lever",
            "priority": company.get("priority", False),
        })
    return jobs


def fetch(companies: list[dict]) -> list[dict]:
    jobs = []
    for company in companies:
        board_type = company.get("type", "").lower()
        if board_type == "greenhouse":
            jobs.extend(_fetch_greenhouse(company))
        elif board_type == "lever":
            jobs.extend(_fetch_lever(company))
        else:
            print(f"[greenhouse_lever] unknown type '{board_type}' for {company.get('name')}")
    return jobs
