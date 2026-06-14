# Job/Internship Alert Bot — Project Plan

## Overview
A Python script that checks multiple job-posting sources hourly, filters new postings against two keyword sets (broad + strict), deduplicates against previously-seen postings, and sends matches to two separate Discord channels via webhooks.

- **Broad channel:** any new-grad / entry-level SWE-type posting
- **Strict channel:** postings that also match specific keywords (Detroit, Michigan, robotics, embedded, etc.)

No Discord bot login needed here — webhooks are sufficient since this is one-way posting, and it runs as a scheduled script (cron) rather than a persistent process.

## Tech Stack
- **Language:** Python 3.11+
- **HTTP:** `requests` or `httpx`
- **Database:** SQLite (dedup storage)
- **Scheduling:** cron job (runs `main.py` every hour) — or `tasks.loop` if later merged into the sports bot project
- **Config/secrets:** `.env` file with `python-dotenv`

## Sources

1. **GitHub "New Grad Positions" repo** (e.g. SimplifyJobs/New-Grad-Positions)
   - Fetch via GitHub API (`raw.githubusercontent.com` or repo contents endpoint) — parse the README table or `.json`/`.listings.json` if available
   - Each row = company, role, location, link, date posted

2. **Greenhouse / Lever company boards**
   - Maintain a config list of company slugs you care about
   - Greenhouse: `https://boards-api.greenhouse.io/v1/boards/{company}/jobs`
   - Lever: `https://api.lever.co/v0/postings/{company}`
   - Both return clean JSON — no scraping needed

3. **RemoteOK API**
   - `https://remoteok.com/api` returns JSON array of current postings
   - Filter by tags/title for SWE-related roles

## Folder Structure
```
job-alert-bot/
├── main.py                  # entry point — runs one full check cycle
├── sources/
│   ├── github_repo.py       # fetch + parse SimplifyJobs-style repo
│   ├── greenhouse_lever.py  # fetch from configured company boards
│   └── remoteok.py          # fetch + parse RemoteOK API
├── filters.py                # broad/strict keyword matching logic
├── notifier.py               # sends formatted messages to Discord webhooks
├── db/
│   ├── database.py           # SQLite helper (init, check-seen, mark-seen)
│   └── schema.sql
├── config.py                  # loads env vars, keyword lists, company slugs
├── companies.json             # list of Greenhouse/Lever company slugs to track
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## Database Schema (SQLite)
**seen_jobs**
| column      | type    | notes                                  |
|-------------|---------|------------------------------------------|
| id          | INTEGER | primary key, autoincrement               |
| source      | TEXT    | "github" / "greenhouse" / "lever" / "remoteok" |
| job_key     | TEXT    | unique identifier (URL or source-specific ID), UNIQUE |
| title       | TEXT    |                                            |
| company     | TEXT    |                                            |
| location    | TEXT    |                                            |
| matched_broad  | BOOLEAN |                                         |
| matched_strict | BOOLEAN |                                        |
| seen_at     | TIMESTAMP | when first seen                        |

## Keyword Config (config.py or .env)
**Broad keywords** (any match = broad channel):
`new grad`, `entry level`, `junior`, `associate software engineer`, `swe i`, `graduate software engineer`, `university grad`

**Strict keywords** (must ALSO match for strict channel):
`detroit`, `michigan`, `robotics`, `embedded`, `ann arbor`

Matching should be case-insensitive and check title + location fields. Easy to extend later.

## Flow (main.py)
1. Load config (keywords, company slugs, webhook URLs)
2. Fetch postings from all three sources
3. For each posting:
   - Build a `job_key` (URL or unique ID)
   - Skip if already in `seen_jobs`
   - Run through `filters.py`:
     - If matches broad keywords → send to broad webhook
     - If ALSO matches strict keywords → send to strict webhook too
   - Insert into `seen_jobs` regardless (so it's not reprocessed)
4. Log summary (X new postings checked, Y sent to broad, Z sent to strict)

## Discord Message Format
Each posting sent as an embed:
- Title: Job title
- Description: Company — Location
- URL: link to apply
- Color: different per source (optional nice touch)

## Implementation Phases

### Phase 1 — Foundation
1. Scaffold project structure, `.env.example`, `requirements.txt`, `.gitignore`
2. Set up SQLite schema + `database.py` (init db, `is_seen(job_key)`, `mark_seen(...)`)
3. Set up `config.py` — load env vars, keyword lists, company slugs from `companies.json`

### Phase 2 — Sources
4. Implement `sources/remoteok.py` (simplest — single JSON endpoint)
5. Implement `sources/greenhouse_lever.py` (loop over `companies.json`, handle both API shapes)
6. Implement `sources/github_repo.py` (fetch + parse SimplifyJobs repo)

### Phase 3 — Filtering & Notification
7. Implement `filters.py` — broad/strict matching functions
8. Implement `notifier.py` — send embed to a given webhook URL

### Phase 4 — Wiring + Scheduling
9. Implement `main.py` — orchestrate fetch → dedupe → filter → notify → store
10. Add cron setup instructions to README (e.g. `0 * * * * cd /path && python3 main.py`)
11. Logging (so you can debug if a source breaks or returns nothing)

### Phase 5 — Polish (optional)
12. Add more companies to `companies.json` over time
13. Add more sources (e.g. Workday-based boards, Lever variants)
14. Daily digest summary message (count of postings seen that day) in addition to real-time alerts

## Notes for Claude Code
- Keep each source module returning a normalized dict shape: `{title, company, location, url, source}` — makes filtering/notifying source-agnostic
- Wrap each source fetch in try/except so one broken source doesn't crash the whole run
- `companies.json` should be easy to edit by hand — just a list of `{ "name": "...", "type": "greenhouse" | "lever", "slug": "..." }`
- Two webhook URLs go in `.env`: `BROAD_WEBHOOK_URL` and `STRICT_WEBHOOK_URL`
- Start with Phase 1 + RemoteOK source to get an end-to-end pipeline working before adding the other sources
