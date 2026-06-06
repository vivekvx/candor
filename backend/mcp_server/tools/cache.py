"""
Disk-based cache for company intelligence data.

Caching is mandatory because scraping ZaubaCorp takes 5-10 seconds
per company, and MCA filing data does not change day-to-day.
Cache entries expire after 24 hours.
"""

import hashlib
import json
import time
from pathlib import Path
from typing import Optional

# Directory where cached intelligence JSON files are stored
CACHE_DIR = Path("intelligence_cache")
CACHE_DIR.mkdir(exist_ok=True)

# 24 hours in seconds — MCA data changes infrequently
CACHE_DURATION_SECONDS = 86400


def get_cache_key(company_name: str) -> str:
    """
    Generate a consistent, filesystem-safe cache key from a company name.

    Normalises to lowercase and strips whitespace so 'Zepto', 'zepto',
    and 'ZEPTO ' all map to the same cache entry.
    """
    normalized_name = company_name.lower().strip()
    return hashlib.md5(normalized_name.encode()).hexdigest()


def get_cached_intelligence(company_name: str) -> Optional[dict]:
    """
    Return cached intelligence data if it exists and is still fresh.

    Returns None on cache miss or when the entry is older than
    CACHE_DURATION_SECONDS, so the caller knows to re-scrape.
    """
    cache_key = get_cache_key(company_name)
    cache_file = CACHE_DIR / f"{cache_key}.json"

    if not cache_file.exists():
        return None

    cached_entry = json.loads(cache_file.read_text())
    cache_age_seconds = time.time() - cached_entry.get("cached_at", 0)

    if cache_age_seconds > CACHE_DURATION_SECONDS:
        return None

    return cached_entry.get("data")


def save_intelligence_to_cache(company_name: str, data: dict) -> None:
    """
    Persist scraped intelligence to disk with a timestamp.

    The timestamp is used by get_cached_intelligence to decide
    whether the entry is still fresh on future reads.
    """
    cache_key = get_cache_key(company_name)
    cache_file = CACHE_DIR / f"{cache_key}.json"

    cache_entry = {
        "cached_at": time.time(),
        "company_name": company_name,
        "data": data,
    }

    cache_file.write_text(json.dumps(cache_entry, indent=2))
