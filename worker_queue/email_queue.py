import logging
import random
import time
import threading
from datetime import date
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

logger = logging.getLogger(__name__)

QUEUE_KEY = "email_queue"
DAILY_COUNT_KEY = "email_daily_count"   # Redis key: email_daily_count:YYYY-MM-DD
DAILY_LIMIT_KEY = "email_daily_limit"   # Redis key: email_daily_limit:YYYY-MM-DD

EMAIL_SUBJECTS = [
    "Sua barbearia ainda agenda pelo WhatsApp?",
    "Enquanto você corta cabelo, clientes estão tentando marcar",
    "3 motivos pelos quais você perde clientes sem perceber",
    "Acabou o horário marcado que não apareceu — veja como",
    "Seu concorrente já automatizou. E você?",
    "Agenda cheia todo dia — sem responder WhatsApp",
    "Chega de cliente faltando sem avisar",
    "Como salões estão lotando a agenda no piloto automático",
]

_stop_event = threading.Event()


def get_redis():
    return redis_lib.from_url(REDIS_URL, decode_responses=True)


def _daily_key(suffix: str) -> str:
    return f"{suffix}:{date.today().isoformat()}"


def get_daily_limit() -> int:
    """Retorna o limite do dia (sorteia uma vez por dia e persiste no Redis)."""
    r = get_redis()
    key = _daily_key(DAILY_LIMIT_KEY)
    val = r.get(key)
    if val is None:
        limit = random.randint(MAILER_DAILY_MIN, MAILER_DAILY_MAX)
        r.setex(key, 86400, limit)  # expira em 24h
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
    """Push lead IDs onto the Redis queue."""
    r = get_redis()
    for lead_id in lead_ids:
        r.rpush(QUEUE_KEY, str(lead_id))
    logger.info(f"Enqueued {len(lead_ids)} leads.")


def queue_length() -> int:
    r = get_redis()
    return r.llen(QUEUE_KEY)


def reset_daily_count():
    """Zera o contador diário (para testes ou reset manual)."""
    r = get_redis()
    r.delete(_daily_key(DAILY_COUNT_KEY))
    r.delete(_daily_key(DAILY_LIMIT_KEY))
    logger.info("Contador diário resetado.")


def _process_batch():
    """Dequeue a random-sized batch and send emails, respecting daily limit."""
    from database.db import mark_sent, get_connection
    from mailer.smtp_sender import send_email
    import psycopg2
    from psycopg2.extras import RealDictCursor

    if daily_limit_reached():
        sent = get_daily_sent()
        limit = get_daily_limit()
        logger.info(f"Limite diário atingido ({sent}/{limit}). Aguardando amanhã.")
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
        subject = random.choice(EMAIL_SUBJECTS)
        success = send_email(
            to=lead["email"],
            subject=subject,
            company_name=lead.get("company_name", ""),
        )
        if success:
            mark_sent(lead["id"])
            sent_count += 1

    if sent_count:
        increment_daily_sent(sent_count)
        logger.info(f"Lote concluído: {sent_count} enviados. Total hoje: {get_daily_sent()}/{get_daily_limit()}")


def worker_loop():
    """Background worker that processes the queue continuously."""
    logger.info("Email queue worker started.")
    while not _stop_event.is_set():
        try:
            if daily_limit_reached():
                # Aguarda até meia-noite verificando a cada 10 min
                _stop_event.wait(timeout=600)
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
