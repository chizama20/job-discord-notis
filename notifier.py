import time
from collections import Counter
from datetime import datetime
import requests

SOURCE_COLORS = {
    "github":        0x57F287,
    "greenhouse":    0x5865F2,
    "lever":         0x5865F2,
    "remoteok":      0xFFA500,
    "colorstack":    0x9B59B6,
    "colorstack_ft": 0xE91E8C,
}

SOURCE_LABELS = {
    "github":        "SimplifyJobs GitHub",
    "greenhouse":    "Greenhouse",
    "lever":         "Lever",
    "remoteok":      "RemoteOK",
    "colorstack":    "ColorStack",
    "colorstack_ft": "ColorStack (FT)",
}

BATCH_SIZE = 5
SEND_DELAY = 0.5


def _build_embed(job: dict) -> dict:
    source = job.get("source", "")
    return {
        "title": job.get("title", "Untitled"),
        "url": job.get("url", ""),
        "color": SOURCE_COLORS.get(source, 0x95A5A6),
        "fields": [
            {"name": "Company",  "value": job.get("company") or "Unknown",               "inline": True},
            {"name": "Location", "value": job.get("location") or "Remote / Not specified", "inline": True},
        ],
        "footer": {"text": f"via {SOURCE_LABELS.get(source, source)}"},
    }


def _source_breakdown(jobs: list[dict]) -> str:
    counts = Counter(
        SOURCE_LABELS.get(j.get("source", ""), j.get("source", "unknown"))
        for j in jobs
    )
    return " · ".join(f"{n} from {src}" for src, n in counts.most_common())


def _request(url: str, payload: dict) -> requests.Response | None:
    """POST with rate-limit retry. Returns the response object (even on 4xx) or None on network error."""
    for attempt in range(3):
        try:
            resp = requests.post(url, json=payload, timeout=10)
            if resp.status_code == 429:
                retry_after = float(resp.json().get("retry_after", 2))
                time.sleep(retry_after + 0.1)
                continue
            time.sleep(SEND_DELAY)
            return resp
        except Exception as exc:
            print(f"[notifier] request error: {exc}")
            return None
    return None


def _send_batched(webhook_url: str, jobs: list[dict], label: str):
    """Fallback for regular text channels — posts summary + batched embeds directly."""
    now = datetime.now().strftime("%b %d, %I:%M %p")
    summary = f"**{label} — {now} ({len(jobs)} found)**\n{_source_breakdown(jobs)}"
    _request(webhook_url, {"content": summary})

    for i in range(0, len(jobs), BATCH_SIZE):
        batch = jobs[i : i + BATCH_SIZE]
        _request(webhook_url, {"embeds": [_build_embed(j) for j in batch]})


def send_thread(webhook_url: str, jobs: list[dict], label: str):
    """
    Tries to post jobs as a Discord thread (requires Forum channel).
    Falls back to batched embeds in a regular text channel on 400.
    """
    if not webhook_url or not jobs:
        return

    now = datetime.now().strftime("%b %d, %I:%M %p")
    thread_name = f"{label} — {now} ({len(jobs)} found)"
    summary_embed = {
        "title": thread_name,
        "description": _source_breakdown(jobs),
        "color": 0x2B2D31,
    }

    resp = _request(
        webhook_url + "?wait=true",
        {"thread_name": thread_name, "embeds": [summary_embed]},
    )

    # 400 = regular text channel (thread_name not supported) → fall back
    if resp is None or not resp.ok:
        if resp is not None and resp.status_code == 400:
            print(f"[notifier] '{label}': channel is not a Forum channel, using batched mode")
        else:
            print(f"[notifier] '{label}': thread creation failed, using batched mode")
        _send_batched(webhook_url, jobs, label)
        return

    thread_id = resp.json().get("channel_id")
    if not thread_id:
        print(f"[notifier] '{label}': no thread_id returned, using batched mode")
        _send_batched(webhook_url, jobs, label)
        return

    thread_url = webhook_url + f"?thread_id={thread_id}"
    for i in range(0, len(jobs), BATCH_SIZE):
        batch = jobs[i : i + BATCH_SIZE]
        _request(thread_url, {"embeds": [_build_embed(j) for j in batch]})
