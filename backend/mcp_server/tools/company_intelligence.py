"""
MCA company intelligence tool for Candor.

Fetches real Indian company data from two public sources using plain HTTP:
- ZaubaCorp: wraps government MCA filings (charges, directors, status)
- AmbitionBox: employee-reported salary benchmarks

This gives Candor access to legally-filed debt signals and actual
compensation data that Tavily web search cannot surface. Uses httpx
instead of a headless browser — both sites serve server-rendered HTML
that BeautifulSoup can parse directly, and Playwright/Chromium is too
heavy to run reliably on Railway.
"""

import logging
from datetime import datetime, timezone
from typing import Optional

import httpx
from bs4 import BeautifulSoup
from pydantic import BaseModel

from mcp_server.tools.cache import (
    get_cached_intelligence,
    save_intelligence_to_cache,
)

logger = logging.getLogger(__name__)

# ZaubaCorp search URL — {company_name} replaced with hyphenated name
ZAUBA_SEARCH_URL = "https://www.zaubacorp.com/companysearchresults/{company_name}"

# Base URL prepended to relative hrefs found in ZaubaCorp search results
ZAUBA_COMPANY_BASE_URL = "https://www.zaubacorp.com"

# AmbitionBox salary page URL — {company_slug} replaced at runtime
AMBITIONBOX_SALARY_URL = "https://www.ambitionbox.com/salaries/{company_slug}-salaries"

# Seconds to wait for an HTTP response before giving up
REQUEST_TIMEOUT_SECONDS = 15.0

# How many search result rows to inspect before giving up
MAX_SEARCH_RESULTS = 3

# Mimics a real Chrome browser to avoid bot-detection blocks
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

REQUEST_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


class CompanyIntelligenceInput(BaseModel):
    """Input schema for the company intelligence tool."""

    company_name: str  # e.g. "Zepto", "Swiggy", "BYJU's"
    city: Optional[str] = None  # Optional city to narrow search results


async def fetch_html(url: str) -> str:
    """
    Fetch a page's HTML using httpx with browser-like headers.

    No headless browser needed — both ZaubaCorp and AmbitionBox serve
    server-rendered HTML that is fully present in the initial response.
    """
    async with httpx.AsyncClient(
        timeout=REQUEST_TIMEOUT_SECONDS,
        follow_redirects=True,
        headers=REQUEST_HEADERS,
    ) as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.text


async def get_company_intelligence(input_data: CompanyIntelligenceInput) -> dict:
    """
    Fetch real Indian company intelligence from MCA filings and AmbitionBox.

    Checks the 24-hour disk cache first. On cache miss, fetches ZaubaCorp
    HTML for government filing data and AmbitionBox HTML for salary
    benchmarks via plain HTTP requests. Saves the result to cache.

    Returns structured intelligence including registration status, directors,
    charge documents (debt signals), compliance signals, salary benchmarks,
    and pre-analysed red flags and positive signals.
    """
    cached_result = get_cached_intelligence(input_data.company_name)
    if cached_result:
        logger.info("Cache hit for company: %s", input_data.company_name)
        return cached_result

    result = _build_empty_result(input_data.company_name)
    # Source-registry fields — every claim traces back to where/when it came from.
    result["retrieved_at"] = datetime.now(timezone.utc).isoformat()
    result["source_url"] = "mca_filing"

    try:
        company_url = await search_zauba_corp(input_data.company_name, input_data.city)

        if company_url:
            company_data = await extract_company_details(company_url)
            result["registration"] = company_data.get("registration", {})
            result["directors"] = company_data.get("directors", [])
            result["charge_documents"] = company_data.get("charges", [])
            result["compliance_signals"] = company_data.get("compliance", [])
            result["red_flags"] = analyze_red_flags(company_data)
            result["positive_signals"] = analyze_positive_signals(company_data)
        else:
            result["data_quality"] = "not_found"
            result["red_flags"].append(
                "Company not found in MCA registry — "
                "verify company name and registration status"
            )

        salary_data = await scrape_ambitionbox_salaries(input_data.company_name)
        result["salary_benchmarks"] = salary_data

    except Exception as error:
        logger.error(
            "Company intelligence fetch failed for '%s': %s",
            input_data.company_name,
            error,
        )
        result["data_quality"] = "partial"
        result["red_flags"].append(f"Could not fetch complete data: {error}")

    save_intelligence_to_cache(input_data.company_name, result)
    return result


def _build_empty_result(company_name: str) -> dict:
    """
    Construct the default result skeleton used before fetching begins.

    Centralised here so the shape is consistent whether data is found
    or the fetch fails partway through.
    """
    return {
        "company": company_name,
        "source": "ZaubaCorp (MCA filings) + AmbitionBox",
        "registration": {},
        "directors": [],
        "charge_documents": [],
        "compliance_signals": [],
        "salary_benchmarks": {},
        "red_flags": [],
        "positive_signals": [],
        "data_quality": "full",
    }


async def search_zauba_corp(company_name: str, city: Optional[str]) -> Optional[str]:
    """
    Search ZaubaCorp for a company by name.

    Returns the absolute URL of the best-matching company profile page,
    preferring active companies over struck-off ones. Returns None if
    no match is found in the first MAX_SEARCH_RESULTS rows.
    """
    try:
        search_name = company_name.replace(" ", "-")
        search_url = ZAUBA_SEARCH_URL.format(company_name=search_name)

        html = await fetch_html(search_url)
        soup = BeautifulSoup(html, "html.parser")

        result_rows = soup.select("table tbody tr")
        best_match_url = None

        for row in result_rows[:MAX_SEARCH_RESULTS]:
            row_text = row.get_text()
            link_element = row.select_one("a")

            if not link_element:
                continue

            href = link_element.get("href", "")
            if not href:
                continue

            # Active companies are the target — struck-off means dissolved
            is_active = "strike" not in row_text.lower()
            name_matches = company_name.lower() in row_text.lower()

            # ZaubaCorp hrefs are sometimes absolute, sometimes relative
            full_url = href if href.startswith("http") else ZAUBA_COMPANY_BASE_URL + href

            if name_matches and is_active:
                best_match_url = full_url
                break

            # Keep first name-match as fallback even if struck-off
            if name_matches and not best_match_url:
                best_match_url = full_url

        return best_match_url

    except Exception as error:
        logger.warning("ZaubaCorp search failed for '%s': %s", company_name, error)
        return None


async def extract_company_details(company_url: str) -> dict:
    """
    Extract registration, directors, charges, and compliance from a ZaubaCorp page.

    Charge documents are the highest-value signal: each charge means the company
    filed a formal loan/debt instrument with the MCA government registry.
    Multiple unsatisfied charges indicate significant debt burden.
    """
    details = {"registration": {}, "directors": [], "charges": [], "compliance": []}

    try:
        html = await fetch_html(company_url)
        soup = BeautifulSoup(html, "html.parser")

        details["registration"] = extract_registration_details(soup)
        details["directors"] = extract_directors(soup)
        details["charges"] = extract_charge_documents(soup)
        details["compliance"] = extract_compliance_status(soup)

    except Exception as error:
        logger.warning("Failed to extract details from %s: %s", company_url, error)

    return details


def extract_registration_details(soup: BeautifulSoup) -> dict:
    """
    Parse company registration fields from the ZaubaCorp HTML table.

    Extracts CIN, incorporation date, status, paid-up capital,
    authorised capital, and registered address.
    """
    registration = {}

    try:
        info_table = soup.find("table", {"class": "table"})
        if not info_table:
            return registration

        for row in info_table.find_all("tr"):
            cells = row.find_all("td")
            if len(cells) < 2:
                continue

            label = cells[0].get_text(strip=True).lower()
            value = cells[1].get_text(strip=True)

            if "cin" in label:
                registration["cin"] = value
            elif "incorporation" in label or "date of" in label:
                registration["incorporation_date"] = value
            elif "status" in label:
                registration["status"] = value
            elif "paid up" in label or "paid-up" in label:
                registration["paid_up_capital"] = value
            elif "authorized" in label:
                registration["authorized_capital"] = value
            elif "address" in label:
                registration["address"] = value

    except Exception as error:
        logger.warning("Registration extraction failed: %s", error)

    return registration


def extract_directors(soup: BeautifulSoup) -> list:
    """
    Parse director records from the ZaubaCorp company page.

    Multiple directors with very short tenures signals management
    instability — a meaningful risk signal for job seekers.
    """
    directors = []

    try:
        director_section = soup.find("div", {"id": "directors"})
        if not director_section:
            director_section = soup.find("table", {"id": "director_table"})

        if not director_section:
            return directors

        for row in director_section.find_all("tr")[1:]:  # skip header
            cells = row.find_all("td")
            if len(cells) >= 2:
                directors.append({
                    "name": cells[0].get_text(strip=True),
                    "din": cells[1].get_text(strip=True),
                })

    except Exception as error:
        logger.warning("Director extraction failed: %s", error)

    return directors


def extract_charge_documents(soup: BeautifulSoup) -> list:
    """
    Parse charge documents (formal debt filings) from the ZaubaCorp page.

    A charge is an official MCA filing confirming the company has taken a
    loan secured against its assets. This is more reliable than news articles
    because it is a legally-mandated government disclosure.
    """
    charges = []

    try:
        charge_section = soup.find("div", {"id": "charges"})
        if not charge_section:
            charge_section = soup.find("table", {"id": "charge_table"})

        if not charge_section:
            return charges

        for row in charge_section.find_all("tr")[1:]:  # skip header
            cells = row.find_all("td")
            if len(cells) >= 3:
                charges.append({
                    "charge_holder": cells[0].get_text(strip=True),
                    "amount": cells[1].get_text(strip=True),
                    "date": cells[2].get_text(strip=True),
                    "status": cells[3].get_text(strip=True) if len(cells) > 3 else "Unknown",
                })

    except Exception as error:
        logger.warning("Charge extraction failed: %s", error)

    return charges


def extract_compliance_status(soup: BeautifulSoup) -> list:
    """
    Parse compliance filing signals from the ZaubaCorp page.

    Late or missing annual returns indicate the company is not meeting
    its statutory obligations — a governance risk signal.
    """
    compliance_signals = []

    try:
        compliance_section = soup.find("div", {"id": "filing"})
        if not compliance_section:
            return compliance_signals

        filing_text = compliance_section.get_text()

        if "default" in filing_text.lower():
            compliance_signals.append("Company has compliance defaults on record")

        if "annual return" in filing_text.lower():
            compliance_signals.append("Annual return filing history found")

    except Exception as error:
        logger.warning("Compliance extraction failed: %s", error)

    return compliance_signals


def analyze_red_flags(company_data: dict) -> list:
    """
    Derive red flag signals from raw scraped company data.

    Produces strings the Challenger agent can use as government-backed
    evidence to attack the Advocate's case. Prioritises charge documents
    because they are legally filed facts rather than news claims.
    """
    red_flags = []
    registration = company_data.get("registration", {})
    charges = company_data.get("charges", [])
    directors = company_data.get("directors", [])

    company_status = registration.get("status", "").lower()
    if "strike" in company_status or "dissolved" in company_status:
        red_flags.append(
            "CRITICAL: Company status is struck-off or dissolved per MCA"
        )

    active_charges = [
        charge for charge in charges
        if "satisfied" not in charge.get("status", "").lower()
    ]

    if len(active_charges) >= 3:
        red_flags.append(
            f"HIGH DEBT: {len(active_charges)} active charge documents filed "
            f"with MCA — significant debt burden"
        )
    elif len(active_charges) >= 1:
        red_flags.append(
            f"{len(active_charges)} charge document(s) filed — "
            f"company has taken loans against assets"
        )

    if len(directors) < 2:
        red_flags.append(
            "Fewer than 2 directors on record — potential governance concern"
        )

    return red_flags


def analyze_positive_signals(company_data: dict) -> list:
    """
    Derive positive signals from raw scraped company data.

    Produces strings the Advocate agent can use to build the strongest
    possible case for the opportunity, grounded in government filings.
    """
    positive_signals = []
    registration = company_data.get("registration", {})
    charges = company_data.get("charges", [])

    company_status = registration.get("status", "").lower()
    if "active" in company_status:
        positive_signals.append(
            "Company is active and compliant per MCA registry"
        )

    if len(charges) == 0:
        positive_signals.append(
            "No charge documents filed — company operates debt-free"
        )

    paid_up_capital = registration.get("paid_up_capital", "")
    capital_indicators = ["Cr", "crore", "lakh"]
    if paid_up_capital and any(indicator in paid_up_capital for indicator in capital_indicators):
        positive_signals.append(
            f"Paid-up capital: {paid_up_capital} — "
            f"indicates real capital investment by founders"
        )

    return positive_signals


async def scrape_ambitionbox_salaries(company_name: str) -> dict:
    """
    Fetch salary benchmarks from AmbitionBox for the given company.

    AmbitionBox salary data comes from self-reports by actual employees,
    making it more reliable for compensation benchmarking than general
    web search results. Returns up to 5 role-salary entries.
    """
    salary_data = {
        "source": "AmbitionBox employee reports",
        "roles": [],
        "data_found": False,
    }

    try:
        company_slug = company_name.lower().replace(" ", "-")
        salary_url = AMBITIONBOX_SALARY_URL.format(company_slug=company_slug)

        html = await fetch_html(salary_url)
        soup = BeautifulSoup(html, "html.parser")

        # AmbitionBox uses CSS classes containing "salary" on role salary cards
        salary_items = soup.find_all(
            "div",
            {"class": lambda css_class: css_class and "salary" in css_class.lower()},
        )

        for item in salary_items[:5]:
            text = item.get_text(strip=True)
            if text:
                salary_data["roles"].append(text)
                salary_data["data_found"] = True

    except Exception as error:
        logger.warning("AmbitionBox fetch failed for '%s': %s", company_name, error)
        salary_data["error"] = (
            "Could not fetch salary data — using Tavily search as fallback"
        )

    return salary_data
