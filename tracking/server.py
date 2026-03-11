"""
Servidor de rastreamento de abertura e clique de emails.
Requer TRACKING_BASE_URL configurado no .env para funcionar externamente.
"""
import logging
from aiohttp import web
from database.db import record_open, record_click

logger = logging.getLogger(__name__)

# GIF transparente 1x1 pixel
_PIXEL = (
    b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00'
    b'\xff\xff\xff\x00\x00\x00\x21\xf9\x04\x01\x00\x00\x00'
    b'\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02'
    b'\x44\x01\x00\x3b'
)

TOPAGENDA_URL = "https://topagenda.online"

_BOT_SIGNATURES = (
    "googleimageproxy",
    "googlebot",
    "bingbot",
    "yahoo! slurp",
    "mailjet",
    "brevo",
    "sendgrid",
    "amazonses",
    "preview",
    "spider",
    "crawler",
    "bot/",
    "scrapy",
    "python-requests",
    "curl/",
    "wget/",
)


def _is_bot(user_agent: str) -> bool:
    ua = (user_agent or "").lower()
    return any(sig in ua for sig in _BOT_SIGNATURES)


def _detect_device(user_agent: str) -> str:
    ua = (user_agent or "").lower()
    if any(k in ua for k in ("android", "iphone", "ipad", "mobile", "blackberry", "windows phone")):
        return "mobile"
    return "desktop"


async def handle_open(request: web.Request) -> web.Response:
    try:
        lead_id = int(request.match_info["lead_id"])
        ua = request.headers.get("User-Agent", "")
        if _is_bot(ua):
            logger.debug(f"[Track] Abertura ignorada (bot): lead_id={lead_id} ua={ua[:60]}")
        else:
            device = _detect_device(ua)
            record_open(lead_id, device)
            logger.debug(f"[Track] Abertura: lead_id={lead_id} device={device}")
    except Exception:
        pass
    return web.Response(body=_PIXEL, content_type="image/gif",
                        headers={"Cache-Control": "no-store, no-cache"})


async def handle_click(request: web.Request) -> web.Response:
    try:
        lead_id = int(request.match_info["lead_id"])
        device = _detect_device(request.headers.get("User-Agent", ""))
        record_click(lead_id, device)
        logger.debug(f"[Track] Clique: lead_id={lead_id} device={device}")
    except Exception:
        pass
    raise web.HTTPFound(location=TOPAGENDA_URL)


async def handle_health(request: web.Request) -> web.Response:
    return web.Response(text="ok")


def create_app() -> web.Application:
    app = web.Application()
    app.router.add_get("/t/o/{lead_id}", handle_open)
    app.router.add_get("/t/c/{lead_id}", handle_click)
    app.router.add_get("/health", handle_health)
    return app


async def start_tracking_server(port: int = 8080):
    from config.settings import TRACKING_BASE_URL
    if not TRACKING_BASE_URL:
        logger.warning("[Track] TRACKING_BASE_URL não configurado — rastreamento desativado.")
        return
    app = create_app()
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info(f"[Track] Servidor de rastreamento em porta {port} | URL pública: {TRACKING_BASE_URL}")
