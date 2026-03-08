import re
import logging
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

logger = logging.getLogger(__name__)

EMAIL_REGEX = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-z]{2,}")

# Patterns to filter out false positives
INVALID_EMAIL_PATTERNS = re.compile(
    r"\.(png|jpg|jpeg|gif|svg|webp|pdf|css|js|woff|ttf)$"
    r"|@sentry\.|@example\.|@test\.|@domain\.|@email\."
    r"|noreply@|no-reply@",
    re.IGNORECASE,
)

CONTACT_PATHS = ["/contato", "/contact", "/sobre", "/about", "/fale-conosco", "/atendimento"]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/121.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
}


def _fetch_html(url: str, timeout: int = 10) -> str | None:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout, allow_redirects=True)
        if resp.status_code == 200:
            return resp.text
    except Exception as e:
        logger.debug(f"Failed to fetch {url}: {e}")
    return None


def _extract_emails_from_html(html: str) -> set[str]:
    emails = set()
    soup = BeautifulSoup(html, "lxml")

    # Check mailto links first
    for tag in soup.find_all("a", href=True):
        href = tag["href"]
        if href.startswith("mailto:"):
            email = href[7:].split("?")[0].strip()
            if email and not INVALID_EMAIL_PATTERNS.search(email):
                emails.add(email.lower())

    # Full text regex scan
    text = soup.get_text(separator=" ")
    for match in EMAIL_REGEX.finditer(text):
        email = match.group().lower()
        if not INVALID_EMAIL_PATTERNS.search(email):
            emails.add(email)

    return emails


def extract_emails(website_url: str) -> list[str]:
    """
    Given a company website URL, attempt to extract public email addresses.
    Checks homepage and common contact pages.
    """
    if not website_url:
        return []

    # Normalise URL
    if not website_url.startswith(("http://", "https://")):
        website_url = "https://" + website_url

    parsed = urlparse(website_url)
    base_url = f"{parsed.scheme}://{parsed.netloc}"

    urls_to_check = [website_url] + [urljoin(base_url, path) for path in CONTACT_PATHS]

    all_emails: set[str] = set()
    for url in urls_to_check:
        html = _fetch_html(url)
        if html:
            found = _extract_emails_from_html(html)
            all_emails.update(found)
            if found:
                logger.debug(f"Found {len(found)} email(s) at {url}")

    return list(all_emails)
