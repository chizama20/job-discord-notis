import logging
from config import (
    BROAD_WEBHOOK_URL,
    PRIORITY_WEBHOOK_URL,
    SWE_ADJACENT_KEYWORDS,
    SENIOR_EXCLUDE_KEYWORDS,
    INTERNSHIP_KEYWORDS,
    TOP_COMPANY_NAMES,
    NON_US_COUNTRIES,
    BROAD_BATCH_SIZE,
    PRIORITY_BATCH_SIZE,
    COMPANIES,
    GITHUB_TOKEN,
    SLACK_USER_TOKEN,
    SLACK_CHANNEL_OPPORTUNITIES_ID,
    SLACK_CHANNEL_FT_ID,
)
from db.database import (
    init_db, is_seen, mark_seen,
    enqueue, get_queue_batch, mark_queue_sent, get_queue_depth,
)
from filters import is_swe_adjacent, is_too_senior, is_us_location, should_send_priority
from notifier import send_thread
from sources import remoteok, greenhouse_lever, github_repo, colorstack_slack

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)


def _fetch_all() -> list[dict]:
    all_jobs = []

    try:
        jobs = colorstack_slack.fetch(
            SLACK_USER_TOKEN, SLACK_CHANNEL_OPPORTUNITIES_ID, SLACK_CHANNEL_FT_ID
        )
        log.info(f"colorstack slack: {len(jobs)} fetched")
        all_jobs.extend(jobs)
    except Exception as exc:
        log.error(f"colorstack slack crashed: {exc}")

    try:
        jobs = remoteok.fetch()
        log.info(f"remoteok: {len(jobs)} fetched")
        all_jobs.extend(jobs)
    except Exception as exc:
        log.error(f"remoteok crashed: {exc}")

    try:
        jobs = greenhouse_lever.fetch(COMPANIES)
        log.info(f"greenhouse/lever: {len(jobs)} fetched")
        all_jobs.extend(jobs)
    except Exception as exc:
        log.error(f"greenhouse/lever crashed: {exc}")

    try:
        jobs = github_repo.fetch(github_token=GITHUB_TOKEN)
        log.info(f"github: {len(jobs)} fetched")
        all_jobs.extend(jobs)
    except Exception as exc:
        log.error(f"github crashed: {exc}")

    return all_jobs


def run():
    init_db()

    all_jobs = _fetch_all()
    log.info(f"total fetched: {len(all_jobs)}")

    newly_queued = 0

    for job in all_jobs:
        job_key = job.get("url", "")
        if not job_key:
            continue
        if not is_us_location(job, NON_US_COUNTRIES):
            continue
        if is_too_senior(job, SENIOR_EXCLUDE_KEYWORDS):
            continue
        if is_seen(job_key):
            continue

        broad = is_swe_adjacent(job, SWE_ADJACENT_KEYWORDS)
        priority = broad and should_send_priority(job, INTERNSHIP_KEYWORDS, TOP_COMPANY_NAMES)

        if broad or priority:
            enqueue(job, broad, priority)
            newly_queued += 1

        mark_seen(job, matched_broad=broad, matched_strict=priority)

    depth = get_queue_depth()
    log.info(
        f"queued {newly_queued} new jobs — "
        f"pending: {depth['broad']} broad, {depth['priority']} priority"
    )

    # Drain up to batch limit from each channel
    broad_batch = get_queue_batch("broad", BROAD_BATCH_SIZE)
    priority_batch = get_queue_batch("priority", PRIORITY_BATCH_SIZE)

    if broad_batch:
        send_thread(BROAD_WEBHOOK_URL, broad_batch, "New Jobs")
        mark_queue_sent([j["url"] for j in broad_batch], "broad")

    if priority_batch:
        send_thread(PRIORITY_WEBHOOK_URL, priority_batch, "Priority Picks")
        mark_queue_sent([j["url"] for j in priority_batch], "priority")

    remaining = get_queue_depth()
    log.info(
        f"sent {len(broad_batch)} broad, {len(priority_batch)} priority — "
        f"still queued: {remaining['broad']} broad, {remaining['priority']} priority"
    )


if __name__ == "__main__":
    run()
