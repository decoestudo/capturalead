import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from config.settings import DATABASE_URL
from utils.email_cleaner import clean_email, is_valid_email

logger = logging.getLogger(__name__)

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS leads (
    id SERIAL PRIMARY KEY,
    company_name TEXT,
    email TEXT UNIQUE,
    website TEXT,
    phone TEXT,
    source TEXT,
    niche TEXT,
    country TEXT,
    collected_at TIMESTAMP DEFAULT NOW(),
    sent BOOLEAN DEFAULT FALSE,
    score INTEGER,
    template_id INTEGER,
    subject TEXT,
    opened_at TIMESTAMP,
    clicked_at TIMESTAMP,
    open_device TEXT,
    click_device TEXT
);
"""

DOMAIN_SCORES: dict[str, int] = {
    "gmail.com":        90,
    "outlook.com":      85,
    "hotmail.com":      75,
    "yahoo.com.br":     65,
    "yahoo.com":        65,
    "icloud.com":       60,
    "me.com":           60,
    "live.com":         60,
    "globo.com":        50,
    "oi.com.br":        45,
    "terra.com.br":     35,
    "uol.com.br":       35,
    "ig.com.br":        30,
    "bol.com.br":       30,
    "brturbo.com.br":   25,
    "pop.com.br":       25,
    "click21.com.br":   25,
    "cpovo.net":        25,
    "hipernet.com.br":  25,
    "superig.com.br":   25,
    "oknet.com.br":     25,
    "multynet.com.br":  25,
    "litoral.com.br":   25,
    "netpar.com.br":    25,
    "dialdata.com.br":  25,
    "onda.com.br":      25,
    "directnet.com.br": 25,
    "wciconsultoria.com.br": 25,
}


def score_email(email: str) -> int:
    if not email or "@" not in email:
        return 0
    domain = email.split("@")[1].lower()
    return DOMAIN_SCORES.get(domain, 100)


def get_connection():
    return psycopg2.connect(DATABASE_URL)


def init_db():
    """Create tables and apply migrations if needed."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(CREATE_TABLE_SQL)
            # Migrations para bases existentes
            for col, definition in [
                ("score",          "INTEGER"),
                ("template_id",    "INTEGER"),
                ("subject",        "TEXT"),
                ("opened_at",      "TIMESTAMP"),
                ("clicked_at",     "TIMESTAMP"),
                ("open_device",    "TEXT"),
                ("click_device",   "TEXT"),
                ("email_invalid",  "BOOLEAN DEFAULT FALSE"),
            ]:
                cur.execute(f"ALTER TABLE leads ADD COLUMN IF NOT EXISTS {col} {definition};")
            # Pontua leads antigos sem score
            cur.execute("SELECT id, email FROM leads WHERE score IS NULL")
            rows = cur.fetchall()
            if rows:
                for lead_id, email in rows:
                    cur.execute(
                        "UPDATE leads SET score = %s WHERE id = %s",
                        (score_email(email or ""), lead_id),
                    )
                logger.info(f"Score calculado para {len(rows)} leads existentes.")
        conn.commit()
    logger.info("Database initialized.")


def email_exists(email: str) -> bool:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM leads WHERE email = %s", (email,))
            return cur.fetchone() is not None


def insert_lead(company_name: str, email: str, website: str = None,
                phone: str = None, source: str = None,
                niche: str = None, country: str = None) -> bool:
    email = clean_email(email)
    if not is_valid_email(email):
        return False
    if email_exists(email):
        return False
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO leads (company_name, email, website, phone, source, niche, country, score)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (company_name, email, website, phone, source, niche, country, score_email(email)),
                )
            conn.commit()
        return True
    except psycopg2.IntegrityError:
        return False


def mark_email_invalid(lead_id: int):
    """Marca email como possivelmente inválido — não será enviado novamente."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE leads SET email_invalid = TRUE WHERE id = %s",
                (lead_id,),
            )
        conn.commit()


def record_sent(lead_id: int, template_id: int, subject: str):
    """Registra qual template e assunto foram usados no envio."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE leads SET sent = TRUE, template_id = %s, subject = %s WHERE id = %s",
                (template_id, subject, lead_id),
            )
        conn.commit()


def record_open(lead_id: int, device: str = None):
    """Registra abertura do email (apenas a primeira vez)."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE leads SET opened_at = NOW(), open_device = %s WHERE id = %s AND opened_at IS NULL",
                (device, lead_id),
            )
        conn.commit()


def record_click(lead_id: int, device: str = None):
    """Registra clique no link (apenas o primeiro)."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE leads SET clicked_at = NOW(), click_device = %s WHERE id = %s AND clicked_at IS NULL",
                (device, lead_id),
            )
        conn.commit()


def get_email_stats() -> dict:
    """Retorna estatísticas gerais de abertura e clique."""
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT
                    COUNT(*)                                             AS total,
                    SUM(CASE WHEN sent        THEN 1 ELSE 0 END)        AS sent,
                    SUM(CASE WHEN opened_at IS NOT NULL THEN 1 ELSE 0 END) AS opened,
                    SUM(CASE WHEN clicked_at IS NOT NULL THEN 1 ELSE 0 END) AS clicked
                FROM leads
            """)
            return dict(cur.fetchone())


def get_domain_stats() -> list[dict]:
    """Retorna performance por domínio de email (top 8 por volume enviado)."""
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT
                    SPLIT_PART(email, '@', 2)                                AS domain,
                    COUNT(*)                                                  AS enviados,
                    SUM(CASE WHEN opened_at  IS NOT NULL THEN 1 ELSE 0 END)  AS abertos,
                    SUM(CASE WHEN clicked_at IS NOT NULL THEN 1 ELSE 0 END)  AS clicados
                FROM leads
                WHERE sent = TRUE
                GROUP BY domain
                ORDER BY enviados DESC
                LIMIT 8
            """)
            return [dict(r) for r in cur.fetchall()]


def get_template_stats() -> list[dict]:
    """Retorna performance por template (abertura e clique)."""
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT
                    template_id,
                    COUNT(*)                                               AS enviados,
                    SUM(CASE WHEN opened_at  IS NOT NULL THEN 1 ELSE 0 END) AS abertos,
                    SUM(CASE WHEN clicked_at IS NOT NULL THEN 1 ELSE 0 END) AS clicados
                FROM leads
                WHERE template_id IS NOT NULL
                GROUP BY template_id
                ORDER BY
                    ROUND(SUM(CASE WHEN opened_at IS NOT NULL THEN 1 ELSE 0 END) * 100.0 / NULLIF(COUNT(*),0), 1) DESC
            """)
            return [dict(r) for r in cur.fetchall()]


def get_device_stats() -> dict:
    """Retorna contagem de dispositivos por abertura e clique."""
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT
                    SUM(CASE WHEN open_device  = 'mobile'  THEN 1 ELSE 0 END) AS open_mobile,
                    SUM(CASE WHEN open_device  = 'desktop' THEN 1 ELSE 0 END) AS open_desktop,
                    SUM(CASE WHEN click_device = 'mobile'  THEN 1 ELSE 0 END) AS click_mobile,
                    SUM(CASE WHEN click_device = 'desktop' THEN 1 ELSE 0 END) AS click_desktop
                FROM leads
            """)
            return dict(cur.fetchone())


def get_unsent_leads(limit: int = 100):
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT * FROM leads
                WHERE sent = FALSE AND (email_invalid IS NULL OR email_invalid = FALSE)
                ORDER BY score DESC NULLS LAST
                LIMIT %s
                """,
                (limit,),
            )
            return cur.fetchall()


def get_recent_leads(limit: int = 20, offset: int = 0):
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT * FROM leads ORDER BY collected_at DESC LIMIT %s OFFSET %s",
                (limit, offset),
            )
            return cur.fetchall()


def mark_sent(lead_id: int):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE leads SET sent = TRUE WHERE id = %s", (lead_id,))
        conn.commit()


def count_unsent() -> int:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) FROM leads WHERE sent = FALSE AND (email_invalid IS NULL OR email_invalid = FALSE)"
            )
            return cur.fetchone()[0]


def count_invalid() -> int:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM leads WHERE email_invalid = TRUE")
            return cur.fetchone()[0]
