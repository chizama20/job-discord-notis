import re
import requests

README_URL = (
    "https://api.github.com/repos/SimplifyJobs/New-Grad-Positions"
    "/contents/README.md?ref=dev"
)

HEADERS = {
    "User-Agent": "job-alert-bot/1.0",
    "Accept": "application/vnd.github.v3.raw",
}

_ROW_RE  = re.compile(r"<tr>\s*(.*?)\s*</tr>", re.DOTALL)
_CELL_RE = re.compile(r"<td[^>]*>(.*?)</td>", re.DOTALL)
_HREF_RE = re.compile(r'href="([^"]+)"')
_TAG_RE  = re.compile(r"<[^>]+>")
_ENTITY  = {"&amp;": "&", "&lt;": "<", "&gt;": ">", "&nbsp;": " ", "&#39;": "'"}


def _clean(html: str) -> str:
    text = _TAG_RE.sub("", html)
    for ent, ch in _ENTITY.items():
        text = text.replace(ent, ch)
    # strip non-ASCII (emoji flags, etc.)
    text = re.sub(r"[^\x00-\x7F]+", "", text)
    return text.strip(", \t\n\r")


def _apply_url(cell_html: str) -> str:
    if "🔒" in cell_html:
        return ""
    hrefs = _HREF_RE.findall(cell_html)
    # Prefer direct apply links over simplify.jobs profile pages
    for h in hrefs:
        if "simplify.jobs/p/" not in h and "simplify.jobs/c/" not in h:
            return h
    return hrefs[0] if hrefs else ""


def _parse(readme: str) -> list[dict]:
    jobs = []
    last_company = ""

    for m in _ROW_RE.finditer(readme):
        cells = _CELL_RE.findall(m.group(1))
        if len(cells) < 4:
            continue  # header row or malformed

        company_html, role_html, loc_html, apply_html = cells[:4]

        # Company: <strong><a href="...">Name</a></strong> or empty (sub-listing ↳)
        company_match = re.search(r"<a[^>]*>([^<]+)</a>", company_html)
        if company_match:
            last_company = company_match.group(1).strip()
        company = last_company
        if not company:
            continue

        role = _clean(role_html)
        if not role:
            continue

        location = _clean(loc_html)
        url = _apply_url(apply_html)
        if not url:
            continue

        jobs.append({
            "title": role,
            "company": company,
            "location": location,
            "url": url,
            "source": "github",
        })

    return jobs


def fetch(github_token: str = "") -> list[dict]:
    headers = dict(HEADERS)
    if github_token:
        headers["Authorization"] = f"token {github_token}"

    try:
        resp = requests.get(README_URL, headers=headers, timeout=30)
        resp.raise_for_status()
        jobs = _parse(resp.text)
        return jobs
    except Exception as exc:
        print(f"[github] fetch failed: {exc}")
        return []
