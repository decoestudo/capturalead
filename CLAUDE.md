# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Lead generation and email marketing automation for TopAgenda (Brazilian scheduling software). Scrapes business emails from Google Maps, Casa dos Dados (CNPJ database), and Bing Search, stores them in PostgreSQL, and sends HTML email campaigns via SMTP — all controlled through a Telegram bot.

## Running the Project

**With Docker (recommended):**
```bash
docker-compose up --build
```

**Locally:**
```bash
pip install -r requirements.txt
playwright install chromium
python main.py
```

## Environment Variables

Copy `.env.example` to `.env` and fill in:
- `TELEGRAM_TOKEN` / `TELEGRAM_ADMIN_CHAT_ID` — bot credentials and admin access control
- `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`, `EMAIL_FROM` — Hostinger SMTP (port 465, SSL)
- `DATABASE_URL` — PostgreSQL connection string
- `REDIS_URL` — Redis connection string (default: `redis://redis:6379`)

## Architecture

**Startup sequence** (`main.py`):
1. Initialize PostgreSQL schema (`database/db.py`)
2. Start Redis queue worker in a background thread (`worker_queue/email_queue.py`)
3. Start Telegram bot polling — blocks (`bot/telegram_bot.py`)

**Scraping pipeline** (triggered by `/start_scraping <country> <quantity>` in Telegram):
- `casadosdados_scraper.py` — uses Playwright + stealth to search Casa dos Dados via Bing, extracts CNPJ records
- `google_maps_scraper.py` — scrapes Google Maps for businesses, visits their websites to find emails
- `email_extractor.py` — regex-based email extraction from raw HTML

**Email pipeline** (triggered by `/send_campaign` in Telegram):
- Leads marked as unsent are pushed to a Redis queue
- `email_queue.py` worker dequeues in random batches (1–5 emails), waits random intervals (1–5 min) between batches
- `smtp_sender.py` sends the HTML template at `templates/email.html` via SMTP_SSL

**Database schema** (`leads` table):
```
id, company_name, email (UNIQUE), website, phone, source, niche, country, collected_at, sent
```

## Key Configuration (`config/settings.py`)

- `NICHES` — list of Brazilian service business types targeted for scraping
- `SCRAPER_MIN/MAX_DELAY` — random delays between scraper requests (seconds)
- `MAILER_MIN/MAX_BATCH_SIZE` and `MAILER_MIN/MAX_WAIT_MINUTES` — email throttling parameters

## Telegram Bot Commands (admin only)

- `/start_scraping <country> <quantity>` — begins async scraping
- `/show_leads [page]` — paginated lead list
- `/send_campaign` — queues unsent leads for emailing
- `/stats` — shows DB counts
