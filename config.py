import json
import os
from dotenv import load_dotenv

load_dotenv()

BROAD_WEBHOOK_URL = os.getenv("BROAD_WEBHOOK_URL", "")
PRIORITY_WEBHOOK_URL = os.getenv("PRIORITY_WEBHOOK_URL", "")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")

SLACK_USER_TOKEN = os.getenv("SLACK_USER_TOKEN", "")
SLACK_CHANNEL_OPPORTUNITIES_ID = os.getenv("SLACK_CHANNEL_OPPORTUNITIES_ID", "")
SLACK_CHANNEL_FT_ID = os.getenv("SLACK_CHANNEL_FT_ID", "")

# Broad: anything software-adjacent hits the broad channel
SWE_ADJACENT_KEYWORDS = [
    "software engineer", "software developer", "swe", "sde",
    "backend", "frontend", "full stack", "fullstack", "full-stack",
    "data engineer", "ml engineer", "machine learning", "ai engineer",
    "devops", "platform engineer", "site reliability", "sre",
    "mobile engineer", "ios engineer", "android engineer",
    "electrical engineer", "embedded", "firmware", "hardware engineer",
    "quant", "quantitative", "research scientist", "research engineer",
    "trading", "algorithmic", "data scientist",
    "new grad", "entry level", "junior", "associate engineer",
    "university grad", "graduate engineer",
    "intern", "internship", "co-op", "coop", "fellowship",
]

# Title prefixes/words that mark a role as too senior — excluded from all channels
SENIOR_EXCLUDE_KEYWORDS = [
    "senior", "sr.", "sr ",
    "staff engineer", "staff software",
    "principal",
    "director",
    "vice president", " vp ",
    "manager",
    "head of",
    "chief",
    "distinguished",
]

# Keywords that mark a posting as an internship/co-op (excludes from priority)
INTERNSHIP_KEYWORDS = [
    "intern", "internship", "co-op", "coop", "co op",
    "fellowship", "summer", "part-time", "part time",
]

# Top company names used to match GitHub/RemoteOK results by company name
TOP_COMPANY_NAMES = {
    "google", "meta", "amazon", "apple", "microsoft", "netflix",
    "nvidia", "tesla", "stripe", "airbnb", "uber", "lyft",
    "openai", "anthropic", "spacex", "anduril", "palantir",
    "citadel", "two sigma", "jane street", "d.e. shaw", "hudson river trading",
    "jump trading", "optiver", "virtu", "imc trading", "susquehanna",
    "rivian", "waymo", "aurora", "zoox", "cruise", "nuro",
    "ford", "gm", "general motors",
}

# Max jobs sent per channel per hourly run
BROAD_BATCH_SIZE = 20
PRIORITY_BATCH_SIZE = 10

NON_US_COUNTRIES = {
    "canada", "uk", "united kingdom", "england", "scotland", "wales",
    "germany", "france", "india", "australia", "brazil", "mexico",
    "spain", "italy", "netherlands", "sweden", "norway", "denmark",
    "finland", "switzerland", "ireland", "poland", "portugal", "austria",
    "belgium", "czech republic", "singapore", "japan", "china",
    "south korea", "taiwan", "hong kong", "new zealand", "south africa",
    "nigeria", "kenya", "ghana", "argentina", "chile", "colombia", "peru",
    "pakistan", "bangladesh", "philippines", "indonesia", "malaysia",
    "thailand", "vietnam", "egypt", "israel", "turkey", "uae",
    "united arab emirates", "saudi arabia", "qatar",
}

_companies_path = os.path.join(os.path.dirname(__file__), "companies.json")
with open(_companies_path, "r") as _f:
    COMPANIES = json.load(_f)
