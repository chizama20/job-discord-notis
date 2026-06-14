import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "jobs.db")
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "schema.sql")


def _connect():
    return sqlite3.connect(DB_PATH)


def init_db():
    with open(SCHEMA_PATH, "r") as f:
        schema = f.read()
    with _connect() as conn:
        conn.executescript(schema)


# ── seen_jobs (dedup — prevents re-queueing across runs) ──────────────────────

def is_seen(job_key: str) -> bool:
    with _connect() as conn:
        row = conn.execute(
            "SELECT 1 FROM seen_jobs WHERE job_key = ?", (job_key,)
        ).fetchone()
    return row is not None


def mark_seen(job: dict, matched_broad: bool, matched_strict: bool):
    with _connect() as conn:
        conn.execute(
            """
            INSERT OR IGNORE INTO seen_jobs
                (source, job_key, title, company, location, matched_broad, matched_strict)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                job.get("source"),
                job.get("url"),
                job.get("title"),
                job.get("company"),
                job.get("location"),
                int(matched_broad),
                int(matched_strict),
            ),
        )


# ── job_queue (rate-limited delivery) ─────────────────────────────────────────

def enqueue(job: dict, broad: bool, priority: bool):
    """Add job to queue, or update its channel flags if already queued."""
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO job_queue (job_key, source, title, company, location, url, send_broad, send_priority)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(job_key) DO UPDATE SET
                send_broad    = send_broad    | excluded.send_broad,
                send_priority = send_priority | excluded.send_priority
            """,
            (
                job.get("url"),
                job.get("source"),
                job.get("title"),
                job.get("company"),
                job.get("location"),
                job.get("url"),
                int(broad),
                int(priority),
            ),
        )


def get_queue_batch(channel: str, limit: int) -> list[dict]:
    """Return up to `limit` unsent jobs for a channel, oldest first."""
    col = "broad_sent" if channel == "broad" else "priority_sent"
    send_col = "send_broad" if channel == "broad" else "send_priority"
    with _connect() as conn:
        rows = conn.execute(
            f"""
            SELECT job_key, source, title, company, location, url
            FROM job_queue
            WHERE {send_col} = 1 AND {col} = 0
            ORDER BY queued_at ASC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [
        {"url": r[5], "source": r[1], "title": r[2], "company": r[3], "location": r[4]}
        for r in rows
    ]


def mark_queue_sent(job_keys: list[str], channel: str):
    """Mark a batch of jobs as sent for the given channel."""
    if not job_keys:
        return
    col = "broad_sent" if channel == "broad" else "priority_sent"
    with _connect() as conn:
        conn.executemany(
            f"UPDATE job_queue SET {col} = 1 WHERE job_key = ?",
            [(k,) for k in job_keys],
        )


def get_queue_depth() -> dict:
    """Return pending counts per channel for logging."""
    with _connect() as conn:
        broad = conn.execute(
            "SELECT COUNT(*) FROM job_queue WHERE send_broad=1 AND broad_sent=0"
        ).fetchone()[0]
        priority = conn.execute(
            "SELECT COUNT(*) FROM job_queue WHERE send_priority=1 AND priority_sent=0"
        ).fetchone()[0]
    return {"broad": broad, "priority": priority}
