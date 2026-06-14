# Job/Internship Alert Bot

Polls job postings hourly from GitHub (SimplifyJobs), Greenhouse, Lever, RemoteOK, and ColorStack Slack. Filters by SWE-adjacent keywords and posts to two Discord channels as threaded runs.

## Setup

### 1. Install dependencies
```
pip install -r requirements.txt
```

### 2. Configure environment
```
cp .env.example .env
```
Edit `.env`:
- `BROAD_WEBHOOK_URL` — Discord webhook for broad channel (all SWE-adjacent roles)
- `PRIORITY_WEBHOOK_URL` — Discord webhook for priority channel (full-time, top companies)
- `GITHUB_TOKEN` — optional, increases GitHub API rate limits
- `SLACK_USER_TOKEN` — ColorStack Slack user token (see below)
- `SLACK_CHANNEL_OPPORTUNITIES_ID` — ColorStack #opportunity channel ID
- `SLACK_CHANNEL_FT_ID` — ColorStack #opportunity-full-time channel ID

### 3. Discord channel setup
Each webhook should point to either a **Forum channel** (recommended — each run becomes a browsable post) or a regular text channel. Both work identically with the code.

### 4. Edit company list
Open `companies.json` and add/remove Greenhouse or Lever companies:
```json
{ "name": "Company Name", "type": "greenhouse", "slug": "company-slug", "priority": true }
```
Find slugs: `boards.greenhouse.io/<slug>` (Greenhouse) or `jobs.lever.co/<slug>` (Lever).

### 5. ColorStack Slack setup
1. Go to [api.slack.com/apps](https://api.slack.com/apps) → Create New App → From scratch → select ColorStack workspace
2. OAuth & Permissions → add user token scopes: `channels:history`, `channels:read`, `groups:history`, `groups:read`
3. Install to Workspace → copy the **User OAuth Token** (`xoxp-...`) into `.env`
4. Get channel IDs: right-click the channel in Slack → Copy Link — the last path segment is the ID (starts with `C`)

### 6. Test run
```
python main.py
```
A thread should appear in each Discord channel showing the job count and a breakdown by source. Run again immediately — nothing should post (deduplication working).

### 7. Clean start after first run
If you ran the bot before setting up threads, delete the old database so previously-seen jobs get re-evaluated:
```
del jobs.db
python main.py
```

---

## Scheduling on Windows (Task Scheduler)

Run every hour automatically:

```
schtasks /create /tn "JobAlertBot" ^
  /tr "\"C:\Users\Chi\Documents\GitHub\job-discord-notis\.venv\Scripts\python.exe\" \"C:\Users\Chi\Documents\GitHub\job-discord-notis\main.py\"" ^
  /sc hourly /mo 1 /st 00:00 /f
```

**Verify it's registered:**
```
schtasks /query /tn "JobAlertBot"
```

**Run it manually right now:**
```
schtasks /run /tn "JobAlertBot"
```

**Remove it:**
```
schtasks /delete /tn "JobAlertBot" /f
```

> Note: Task Scheduler runs the task as your Windows user. Make sure the path to `python.exe` points to the `.venv` inside the project so dependencies are available.

---

## How delivery works

Each hourly run posts **one thread** per channel (if there are new jobs):
- Thread name: `New Jobs — Jun 13, 10:00 AM (12 found)`
- First message: source breakdown (`8 from SimplifyJobs · 3 from Waymo · 1 from RemoteOK`)
- Following messages: job embeds in batches of 5, each showing title (link), company, and location

If no new jobs are found that run, nothing is posted.

---

## Keyword & filter config

All keyword lists are in `config.py`:
- `SWE_ADJACENT_KEYWORDS` — what counts as a broad match (software, ML, quant, EE, etc.)
- `INTERNSHIP_KEYWORDS` — titles containing these are excluded from the priority channel
- `TOP_COMPANY_NAMES` — company name substrings that qualify for the priority channel
- `NON_US_COUNTRIES` — locations containing these are filtered out entirely

---

## Project structure

```
├── main.py                  # entry point
├── config.py                # env vars, keyword lists, company config
├── filters.py               # SWE-adjacent, US location, priority logic
├── notifier.py              # Discord thread sender
├── companies.json           # Greenhouse/Lever company boards
├── sources/
│   ├── remoteok.py
│   ├── greenhouse_lever.py
│   ├── github_repo.py
│   └── colorstack_slack.py
└── db/
    ├── database.py
    └── schema.sql
```
