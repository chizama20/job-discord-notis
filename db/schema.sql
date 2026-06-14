CREATE TABLE IF NOT EXISTS seen_jobs (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    source        TEXT NOT NULL,
    job_key       TEXT NOT NULL UNIQUE,
    title         TEXT,
    company       TEXT,
    location      TEXT,
    matched_broad  INTEGER DEFAULT 0,
    matched_strict INTEGER DEFAULT 0,
    seen_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS job_queue (
    job_key       TEXT PRIMARY KEY,
    source        TEXT,
    title         TEXT,
    company       TEXT,
    location      TEXT,
    url           TEXT,
    send_broad    INTEGER DEFAULT 0,
    send_priority INTEGER DEFAULT 0,
    broad_sent    INTEGER DEFAULT 0,
    priority_sent INTEGER DEFAULT 0,
    queued_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
