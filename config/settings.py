import os
from dotenv import load_dotenv

load_dotenv()

# Telegram
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_ADMIN_CHAT_ID = os.getenv("TELEGRAM_ADMIN_CHAT_ID")

# SMTP
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.hostinger.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 465))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")
EMAIL_FROM = os.getenv("EMAIL_FROM")

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
    "lava jato",
]

# Delays (seconds)
SCRAPER_MIN_DELAY = 2
SCRAPER_MAX_DELAY = 5
MAILER_MIN_BATCH_SIZE = 1
MAILER_MAX_BATCH_SIZE = 5
MAILER_MIN_WAIT_MINUTES = 1
MAILER_MAX_WAIT_MINUTES = 5
MAILER_DAILY_MIN = 100   # mínimo de envios por dia
MAILER_DAILY_MAX = 300   # máximo de envios por dia
