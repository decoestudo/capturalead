import asyncio
import logging
import random
import re
from urllib.parse import quote_plus
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
from playwright_stealth import stealth_async

logger = logging.getLogger(__name__)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/121.0.0.0 Safari/537.36"
)

EMAIL_REGEX = re.compile(
    r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}",
    re.IGNORECASE,
)

BOOKING_PLATFORMS = (
    "google.com/intl", "google.pt/intl",
    "buk.pt", "fresha.com", "treatwell", "sheerme.com",
    "instagram.com", "facebook.com", "linktr.ee", "linktree",
    "whatsapp.com", "api.whatsapp", "wa.me", "wa.link",
    "youtube.com", "tiktok.com", "twitter.com", "x.com",
    "salonized.com", "alteg.io", "inventore.net",
    "s-iq.co", "findleads.pt", "zappysoftware", "easyweek",
    "booksy.com", "bio.site", "contate.me", "tinyurl.com",
    "cutt.ly", "resurva.com", "belasis.app",
    "salonsoft.com", "agendaonline", "agendeonline",
    "styluson.pt", "forms.gle", "bit.ly", "avec.beauty",
    "setmore.com", "simplybook.it", "trinks.com", "oelysium.com",
    "localo.site", "localmotors.com.br", "support.google.com",
)


async def _random_delay(min_s: float = 1, max_s: float = 3):
    await asyncio.sleep(random.uniform(min_s, max_s))


def _is_booking_platform(url: str) -> bool:
    if not url:
        return True
    return any(plat in url for plat in BOOKING_PLATFORMS)


async def scrape_google_maps(niche: str, country: str, max_results: int = 20, seen_websites: set = None) -> list[dict]:
    """
    Scrape Google Maps -> visita cada empresa -> extrai emails do site real.
    gl=BR força localização Brasil independente do IP do servidor.
    """
    if seen_websites is None:
        seen_websites = set()

    results = []
    # Força Brasil especificando o país explicitamente na query
    query = f"{niche} {country}" if country.lower() not in ("brasil", "brazil", "br") else f"{niche} Brasil"
    url = f"https://www.google.com/maps/search/{query.replace(' ', '+')}?gl=BR&hl=pt-BR"

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent=USER_AGENT,
            locale="pt-BR",
            viewport={"width": 1280, "height": 900},
            geolocation={"latitude": -23.5505, "longitude": -46.6333},  # São Paulo
            permissions=["geolocation"],
        )
        page = await context.new_page()

        try:
            logger.info(f"[Maps] Buscando: {query}")
            await page.goto(url, wait_until="domcontentloaded", timeout=45000)
            await _random_delay(2, 4)

            try:
                await page.click('button:has-text("Aceitar tudo")', timeout=4000)
                await _random_delay(1, 2)
            except PlaywrightTimeout:
                pass

            results_panel = page.locator('div[role="feed"]')
            for _ in range(8):
                try:
                    await results_panel.evaluate("el => el.scrollBy(0, 800)")
                    await _random_delay(1, 2)
                except Exception:
                    break

            listing_links = await page.locator('a[href*="/maps/place/"]').all()
            hrefs = []
            seen = set()
            for link in listing_links:
                href = await link.get_attribute("href")
                if href and href not in seen:
                    seen.add(href)
                    hrefs.append(href)

            logger.info(f"[Maps] Encontrados {len(hrefs)} lugares para '{query}'")

            for href in hrefs[:max_results]:
                try:
                    detail_page = await context.new_page()
                    await detail_page.goto(href, wait_until="domcontentloaded", timeout=30000)
                    await _random_delay(1, 2)

                    company_name = await _safe_text(detail_page, 'h1')
                    phone = await _safe_text(detail_page, '[data-item-id*="phone"]')
                    address = await _safe_text(detail_page, '[data-item-id="address"]')

                    # Filtra empresas fora do Brasil quando country=Brasil
                    if country.lower() in ("brasil", "brazil", "br"):
                        if address:
                            addr_lower = address.lower()
                            # Descarta se endereço indica Portugal ou outro país
                            if any(pt in addr_lower for pt in ["portugal", "lisboa", "porto,", "braga", "coimbra", "faro,"]):
                                logger.debug(f"[Maps] Ignorando empresa fora do Brasil: {company_name} ({address})")
                                await detail_page.close()
                                continue
                        # Descarta telefones que não são brasileiros (+55 ou 0xx)
                        if phone and phone.startswith("+") and not phone.startswith("+55"):
                            logger.debug(f"[Maps] Ignorando empresa fora do Brasil por telefone: {company_name} ({phone})")
                            await detail_page.close()
                            continue

                    raw_website = await _safe_attr(
                        detail_page,
                        'a[data-item-id="authority"], a[data-tooltip*="Site" i]',
                        "href",
                    )

                    if _is_booking_platform(raw_website or ""):
                        raw_website = None

                    # Cache: pula sites já visitados
                    if raw_website and raw_website in seen_websites:
                        logger.debug(f"[Maps] ⏭️ Site já visitado: {raw_website}")
                        await detail_page.close()
                        continue

                    if raw_website:
                        seen_websites.add(raw_website)

                    # Emails diretos na página do Maps
                    page_text = await detail_page.evaluate("document.body.innerText")
                    _skip = ['sentry', 'example', 'test@', 'noreply', 'no-reply', 'microsoft.com',
                             'bing.com', 'wix', 'wordpress', 'schema', 'zappysoftware', 'google.com',
                             'press@', 'partners@', 'people@', 'support@', 'privacy@', 'legal@']
                    direct_emails = [
                        e.lower() for e in EMAIL_REGEX.findall(page_text)
                        if not any(s in e.lower() for s in _skip)
                    ]

                    if company_name:
                        results.append({
                            "company_name": company_name,
                            "website": raw_website,
                            "phone": phone,
                            "niche": niche,
                            "country": country,
                            "source": "google_maps",
                            "direct_emails": direct_emails,
                        })
                        logger.info(f"[Maps] ✅ {company_name} | site={raw_website} | emails={direct_emails}")

                    await detail_page.close()
                    await _random_delay(1, 2)

                except Exception as e:
                    logger.warning(f"[Maps] Erro em {href}: {e}")
                    try:
                        await detail_page.close()
                    except Exception:
                        pass

        except Exception as e:
            logger.error(f"[Maps] Erro geral: {e}")
        finally:
            await browser.close()

    return results


async def scrape_bing_emails(niche: str, country: str, max_results: int = 20) -> list[dict]:
    """
    Usa Bing Search com 'dorks' para encontrar emails de negócios no Instagram e Facebook.
    Bing tem menor restrição anti-bot que o Google.
    """
    results = []
    seen_emails: set = set()

    # Queries estratégicas: busca direta de emails no Bing
    # Não inclui country na query para não restringir demais os resultados
    queries = [
        f'{niche} contato email site:br',
        f'"{niche}" "@gmail.com" OR "@hotmail.com" OR "@yahoo.com.br" contato',
        f'"{niche}" email contato -instagram -facebook site:br',
        f'site:instagram.com "{niche}" email OR contato',
    ]

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent=USER_AGENT,
            locale="pt-BR",
            viewport={"width": 1280, "height": 900},
        )

        for query in queries:
            if len(results) >= max_results:
                break

            page = await context.new_page()
            await stealth_async(page)
            try:
                url = f"https://www.bing.com/search?q={quote_plus(query)}&count=50&setlang=pt-BR&cc=BR"
                logger.info(f"[Bing] Pesquisando: {query[:80]}...")
                await page.goto(url, wait_until="networkidle", timeout=30000)
                await _random_delay(2, 3)

                # Rola suavemente para carregar mais resultados
                try:
                    for _ in range(3):
                        await page.evaluate("window.scrollBy(0, 1200)")
                        await _random_delay(0.8, 1.5)
                    # Aguarda estabilizar após scroll
                    await page.wait_for_load_state("networkidle", timeout=5000)
                except Exception:
                    pass  # Ignora erros de scroll/navigation

                # Extrai tudo da página de forma segura
                try:
                    page_text = await page.evaluate("document.body.innerText")
                except Exception:
                    logger.warning("[Bing] Falha ao extrair texto, pulando query")
                    continue

                found_emails = EMAIL_REGEX.findall(page_text)
                logger.info(f"[Bing] {len(found_emails)} emails no texto da página")

                for email in found_emails:
                    if len(results) >= max_results:
                        break
                    email_lower = email.lower()
                    if any(skip in email_lower for skip in ['sentry', 'example', 'test@', 'noreply', 'no-reply', 'microsoft.com', 'bing.com', 'wix', 'wordpress', 'schema', 'zappysoftware', 'google.com', 'press@', 'partners@', 'people@', 'support@', 'privacy@', 'legal@']):
                        continue
                    if email_lower not in seen_emails:
                        seen_emails.add(email_lower)
                        results.append({
                            "company_name": f"{niche.title()} - {country}",
                            "email": email_lower,
                            "website": "",
                            "phone": "",
                            "niche": niche,
                            "country": country,
                            "source": "bing_search",
                            "direct_emails": [email_lower],
                        })
                        logger.info(f"[Bing] ✅ Email encontrado: {email_lower}")

            except Exception as e:
                logger.warning(f"[Bing] Erro na query: {e}")
            finally:
                try:
                    await page.close()
                except Exception:
                    pass
                await _random_delay(1, 2)

        await browser.close()

    return results


async def _safe_text(page, selector: str) -> str | None:
    try:
        el = page.locator(selector).first
        return (await el.inner_text(timeout=3000)).strip() or None
    except Exception:
        return None


async def _safe_attr(page, selector: str, attr: str) -> str | None:
    try:
        el = page.locator(selector).first
        value = await el.get_attribute(attr, timeout=3000)
        return value.strip() if value else None
    except Exception:
        return None
