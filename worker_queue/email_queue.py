import logging
import random
import time
import threading
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo
import redis as redis_lib
from config.settings import (
    REDIS_URL,
    MAILER_MIN_BATCH_SIZE,
    MAILER_MAX_BATCH_SIZE,
    MAILER_MIN_WAIT_MINUTES,
    MAILER_MAX_WAIT_MINUTES,
    MAILER_DAILY_MIN,
    MAILER_DAILY_MAX,
)
from mailer.templates import SUBJECTS

logger = logging.getLogger(__name__)

QUEUE_KEY        = "email_queue"
DAILY_COUNT_KEY  = "email_daily_count"
DAILY_LIMIT_KEY  = "email_daily_limit"
PAUSED_KEY       = "email_paused"

_stop_event = threading.Event()

_BRT = ZoneInfo("America/Sao_Paulo")
_SEND_HOUR_START = 7   # 07:00 BRT
_SEND_HOUR_END   = 22  # 22:00 BRT


def _is_sending_window() -> bool:
    """Retorna True se o horário atual em BRT está entre 7h e 22h."""
    hour = datetime.now(_BRT).hour
    return _SEND_HOUR_START <= hour < _SEND_HOUR_END


def _seconds_until_window_opens() -> int:
    """Retorna quantos segundos faltam para 7h BRT (hoje ou amanhã)."""
    now = datetime.now(_BRT)
    if now.hour < _SEND_HOUR_START:
        next_open = now.replace(hour=_SEND_HOUR_START, minute=0, second=0, microsecond=0)
    else:
        tomorrow = now + timedelta(days=1)
        next_open = tomorrow.replace(hour=_SEND_HOUR_START, minute=0, second=0, microsecond=0)
    return max(0, int((next_open - now).total_seconds()))


def get_redis():
    return redis_lib.from_url(REDIS_URL, decode_responses=True)


def _daily_key(suffix: str) -> str:
    return f"{suffix}:{date.today().isoformat()}"


def get_daily_limit() -> int:
    r = get_redis()
    key = _daily_key(DAILY_LIMIT_KEY)
    val = r.get(key)
    if val is None:
        limit = random.randint(MAILER_DAILY_MIN, MAILER_DAILY_MAX)
        r.setex(key, 86400, limit)
        logger.info(f"Limite diário sorteado: {limit} emails")
        return limit
    return int(val)


def get_daily_sent() -> int:
    r = get_redis()
    val = r.get(_daily_key(DAILY_COUNT_KEY))
    return int(val) if val else 0


def increment_daily_sent(n: int = 1):
    r = get_redis()
    key = _daily_key(DAILY_COUNT_KEY)
    r.incrby(key, n)
    r.expire(key, 86400)


def daily_limit_reached() -> bool:
    return get_daily_sent() >= get_daily_limit()


def enqueue_leads(lead_ids: list[int]):
    r = get_redis()
    for lead_id in lead_ids:
        r.rpush(QUEUE_KEY, str(lead_id))
    logger.info(f"Enqueued {len(lead_ids)} leads.")


def queue_length() -> int:
    r = get_redis()
    return r.llen(QUEUE_KEY)


def reset_daily_count():
    r = get_redis()
    r.delete(_daily_key(DAILY_COUNT_KEY))
    r.delete(_daily_key(DAILY_LIMIT_KEY))
    logger.info("Contador diário resetado.")


def is_paused() -> bool:
    return get_redis().exists(PAUSED_KEY) == 1


def set_paused(paused: bool):
    r = get_redis()
    if paused:
        r.set(PAUSED_KEY, "1")
        logger.info("Envios pausados.")
    else:
        r.delete(PAUSED_KEY)
        logger.info("Envios retomados.")


def _process_batch():
    from database.db import record_sent, mark_email_invalid, get_connection
    from mailer.smtp_sender import send_email
    from utils.email_cleaner import clean_email, is_valid_email
    import psycopg2
    from psycopg2.extras import RealDictCursor

    if daily_limit_reached():
        return

    remaining = get_daily_limit() - get_daily_sent()
    batch_size = min(
        random.randint(MAILER_MIN_BATCH_SIZE, MAILER_MAX_BATCH_SIZE),
        remaining,
    )

    r = get_redis()
    lead_ids = []
    for _ in range(batch_size):
        val = r.lpop(QUEUE_KEY)
        if val is None:
            break
        lead_ids.append(int(val))

    if not lead_ids:
        return

    logger.info(f"Processando lote de {len(lead_ids)} emails ({get_daily_sent()}/{get_daily_limit()} hoje).")

    with psycopg2.connect(__import__("config.settings", fromlist=["DATABASE_URL"]).DATABASE_URL) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM leads WHERE id = ANY(%s)", (lead_ids,))
            leads = cur.fetchall()

    sent_count = 0
    for lead in leads:
        email = clean_email((lead["email"] or "").strip().lower())

        # Valida email antes de enviar
        if not is_valid_email(email):
            logger.warning(f"[PreSend] Email inválido descartado: {lead['email']!r} (id={lead['id']})")
            mark_email_invalid(lead["id"])
            continue

        template_id = random.randint(1, 20)
        subject     = random.choice(SUBJECTS)
        success = send_email(
            to=email,
            subject=subject,
            company_name=lead.get("company_name", ""),
            template_id=template_id,
            lead_id=lead["id"],
        )
        if success:
            record_sent(lead["id"], template_id, subject)
            sent_count += 1

    if sent_count:
        increment_daily_sent(sent_count)
        logger.info(f"Lote concluído: {sent_count} enviados. Total hoje: {get_daily_sent()}/{get_daily_limit()}")


def worker_loop():
    logger.info("Email queue worker started.")
    while not _stop_event.is_set():
        try:
            if is_paused():
                _stop_event.wait(timeout=30)
                continue

            if not _is_sending_window():
                secs = _seconds_until_window_opens()
                h, m = divmod(secs // 60, 60)
                logger.info(f"Fora do horário de envio (7h–22h BRT). Retomando em {h}h{m:02d}m.")
                # Dorme em fatias de 5 min para não travar o processo
                _stop_event.wait(timeout=min(secs, 300))
                continue

            if daily_limit_reached():
                secs = _seconds_until_window_opens()
                h, m = divmod(secs // 60, 60)
                logger.info(f"Limite diário atingido. Retomando amanhã às 7h BRT (em {h}h{m:02d}m).")
                _stop_event.wait(timeout=min(secs, 300))
                continue

            if queue_length() > 0:
                _process_batch()
                wait_minutes = random.uniform(MAILER_MIN_WAIT_MINUTES, MAILER_MAX_WAIT_MINUTES)
                logger.info(f"Aguardando {wait_minutes:.1f} min antes do próximo lote.")
                _stop_event.wait(timeout=wait_minutes * 60)
            else:
                _stop_event.wait(timeout=30)
        except Exception as e:
            logger.error(f"Queue worker error: {e}")
            _stop_event.wait(timeout=10)
    logger.info("Email queue worker stopped.")


def start_worker() -> threading.Thread:
    t = threading.Thread(target=worker_loop, daemon=True, name="email-queue-worker")
    t.start()
    return t


def stop_worker():
    _stop_event.set()
