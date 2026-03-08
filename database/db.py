import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from config.settings import DATABASE_URL

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
    sent BOOLEAN DEFAULT FALSE
);
"""


def get_connection():
    return psycopg2.connect(DATABASE_URL)


def init_db():
    """Create tables if they don't exist."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(CREATE_TABLE_SQL)
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
    """Insert a lead. Returns True if inserted, False if duplicate."""
    if email_exists(email):
        return False
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO leads (company_name, email, website, phone, source, niche, country)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (company_name, email, website, phone, source, niche, country),
                )
            conn.commit()
        return True
    except psycopg2.IntegrityError:
        return False


def get_unsent_leads(limit: int = 100):
    """Return leads not yet sent."""
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT * FROM leads WHERE sent = FALSE LIMIT %s", (limit,)
            )
            return cur.fetchall()


def get_recent_leads(limit: int = 20, offset: int = 0):
    """Return recently collected leads for display."""
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
            cur.execute("SELECT COUNT(*) FROM leads WHERE sent = FALSE")
            return cur.fetchone()[0]
