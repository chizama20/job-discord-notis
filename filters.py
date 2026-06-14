def _title(job: dict) -> str:
    return job.get("title", "").lower()


def _title_location(job: dict) -> str:
    return f"{job.get('title', '')} {job.get('location', '')}".lower()


def is_too_senior(job: dict, senior_keywords: list[str]) -> bool:
    """Returns True if the title indicates a senior/leadership role to skip."""
    title = _title(job)
    return any(kw.lower() in title for kw in senior_keywords)


def is_swe_adjacent(job: dict, keywords: list[str]) -> bool:
    """Returns True if the job title/location contains any SWE-adjacent keyword."""
    text = _title_location(job)
    return any(kw.lower() in text for kw in keywords)


def is_internship(job: dict, internship_keywords: list[str]) -> bool:
    """Returns True if the job appears to be an internship/co-op/fellowship."""
    text = _title_location(job)
    return any(kw.lower() in text for kw in internship_keywords)


def is_top_company(job: dict, top_company_names: set[str]) -> bool:
    """Returns True if the company matches the priority list."""
    # Check explicit flag set by greenhouse_lever source
    if job.get("priority"):
        return True
    company = job.get("company", "").lower()
    return any(name in company for name in top_company_names)


def is_us_location(job: dict, non_us_countries: set[str]) -> bool:
    """Returns False only if the location explicitly names a non-US country."""
    location = job.get("location", "").lower().strip()
    # Empty/remote with no country context → assume US remote
    if not location:
        return True
    return not any(country in location for country in non_us_countries)


def should_send_priority(
    job: dict,
    internship_keywords: list[str],
    top_company_names: set[str],
) -> bool:
    """
    Priority channel = full-time role at a top company,
    OR anything from the ColorStack #opportunity-full-time Slack channel.
    """
    if job.get("source") == "colorstack_ft":
        return True
    if is_internship(job, internship_keywords):
        return False
    return is_top_company(job, top_company_names)
