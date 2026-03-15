import os
from dotenv import load_dotenv

load_dotenv()

# Telegram
TELEGRAM_TOKEN        = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_ADMIN_CHAT_ID = os.getenv("TELEGRAM_ADMIN_CHAT_ID")
TELEGRAM_API_ID       = int(os.getenv("TELEGRAM_API_ID", "0"))
TELEGRAM_API_HASH     = os.getenv("TELEGRAM_API_HASH", "")

# SMTP principal (Hostinger)
SMTP_HOST  = os.getenv("SMTP_HOST", "smtp.hostinger.com")
SMTP_PORT  = int(os.getenv("SMTP_PORT", 465))
SMTP_USER  = os.getenv("SMTP_USER")
SMTP_PASS  = os.getenv("SMTP_PASS")
EMAIL_FROM = os.getenv("EMAIL_FROM")

# SMTP secundário (Brevo) — usado até BREVO_DAILY_LIMIT por dia
BREVO_SMTP_HOST    = os.getenv("BREVO_SMTP_HOST", "smtp-relay.brevo.com")
BREVO_SMTP_PORT    = int(os.getenv("BREVO_SMTP_PORT", 587))
BREVO_SMTP_USER    = os.getenv("BREVO_SMTP_USER", "")
BREVO_SMTP_PASS    = os.getenv("BREVO_SMTP_PASS", "")
BREVO_DAILY_LIMIT  = int(os.getenv("BREVO_DAILY_LIMIT", 280))  # margem de segurança abaixo de 300

# SMTP terciário (Resend) — usado até RESEND_DAILY_LIMIT por dia
RESEND_SMTP_HOST   = os.getenv("RESEND_SMTP_HOST", "smtp.resend.com")
RESEND_SMTP_PORT   = int(os.getenv("RESEND_SMTP_PORT", 465))
RESEND_SMTP_USER   = os.getenv("RESEND_SMTP_USER", "resend")
RESEND_SMTP_PASS   = os.getenv("RESEND_SMTP_PASS", "")
RESEND_DAILY_LIMIT = int(os.getenv("RESEND_DAILY_LIMIT", 95))   # margem abaixo de 100

# SMTP quaternário (Mailjet) — usado até MAILJET_DAILY_LIMIT por dia
MAILJET_SMTP_HOST   = os.getenv("MAILJET_SMTP_HOST", "in-v3.mailjet.com")
MAILJET_SMTP_PORT   = int(os.getenv("MAILJET_SMTP_PORT", 587))
MAILJET_SMTP_USER   = os.getenv("MAILJET_SMTP_USER", "")
MAILJET_SMTP_PASS   = os.getenv("MAILJET_SMTP_PASS", "")
MAILJET_DAILY_LIMIT = int(os.getenv("MAILJET_DAILY_LIMIT", 190))  # margem abaixo de 200

# Database
DATABASE_URL = os.getenv("DATABASE_URL")

# Redis
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")

# Casa dos Dados API
CASADOSDADOS_API_KEY = os.getenv("CASADOSDADOS_API_KEY")

# Scraping
NICHES = [
    "barbearia",
    "salão de beleza",
    "manicure",
    "pedicure",
    "nail designer",
    "designer de sobrancelha",
    "nutricionista",
]

# Delays (seconds)
SCRAPER_MIN_DELAY = 2
SCRAPER_MAX_DELAY = 5
MAILER_MIN_BATCH_SIZE   = int(os.getenv("MAILER_MIN_BATCH_SIZE",   "1"))
MAILER_MAX_BATCH_SIZE   = int(os.getenv("MAILER_MAX_BATCH_SIZE",   "5"))
MAILER_MIN_WAIT_MINUTES = float(os.getenv("MAILER_MIN_WAIT_MINUTES", "1"))
MAILER_MAX_WAIT_MINUTES = float(os.getenv("MAILER_MAX_WAIT_MINUTES", "5"))
MAILER_DAILY_MIN        = int(os.getenv("MAILER_DAILY_MIN", "100"))   # mínimo de envios por dia
MAILER_DAILY_MAX        = int(os.getenv("MAILER_DAILY_MAX", "300"))   # máximo de envios por dia

# Tracking
TRACKING_BASE_URL = os.getenv("TRACKING_BASE_URL", "")  # Ex: https://yourserver.com:8080
TRACKING_PORT     = int(os.getenv("TRACKING_PORT", "8080"))
