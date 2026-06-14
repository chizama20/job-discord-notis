import re
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

URL_RE = re.compile(r"https?://[^\s|>\]]+")


def _extract_url(text: str) -> str:
    # Slack wraps URLs like <https://example.com|display text> — extract the raw URL
    match = re.search(r"<(https?://[^|>]+)", text)
    if match:
        return match.group(1)
    match = URL_RE.search(text)
    return match.group(0) if match else ""


def _parse_message(text: str, source_label: str) -> dict | None:
    url = _extract_url(text)
    if not url:
        return None

    # Best-effort: strip the URL and Slack formatting, use remaining text as title/company hint
    clean = re.sub(r"<https?://[^>]+>", "", text)
    clean = re.sub(r"[*_~`]", "", clean).strip()
    lines = [l.strip() for l in clean.splitlines() if l.strip()]

    title = lines[0] if lines else "Job Opportunity"
    company = lines[1] if len(lines) > 1 else ""

    return {
        "title": title,
        "company": company,
        "location": "",
        "url": url,
        "source": source_label,
    }


def _fetch_channel(client: WebClient, channel_id: str, source_label: str) -> list[dict]:
    jobs = []
    try:
        cursor = None
        while True:
            kwargs = {"channel": channel_id, "limit": 200}
            if cursor:
                kwargs["cursor"] = cursor
            resp = client.conversations_history(**kwargs)
            for msg in resp.get("messages", []):
                if msg.get("subtype"):  # skip joins, topic changes, etc.
                    continue
                text = msg.get("text", "")
                job = _parse_message(text, source_label)
                if job:
                    jobs.append(job)
            cursor = resp.get("response_metadata", {}).get("next_cursor")
            if not cursor:
                break
    except SlackApiError as exc:
        print(f"[colorstack_slack] {source_label} fetch failed: {exc.response['error']}")
    return jobs


def fetch(token: str, opportunities_channel_id: str, ft_channel_id: str) -> list[dict]:
    if not token:
        print("[colorstack_slack] SLACK_USER_TOKEN not set, skipping")
        return []

    client = WebClient(token=token)
    jobs = []

    if opportunities_channel_id:
        jobs.extend(_fetch_channel(client, opportunities_channel_id, "colorstack"))

    if ft_channel_id:
        jobs.extend(_fetch_channel(client, ft_channel_id, "colorstack_ft"))

    return jobs
