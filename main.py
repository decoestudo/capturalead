import io
import logging
import sys

# Força UTF-8 no stdout para suportar emojis no Windows
if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger(__name__)


def main():
    # 1. Initialise database
    logger.info("Initialising database...")
    from database.db import init_db
    init_db()

    # 2. Start email queue worker
    logger.info("Starting email queue worker...")
    from worker_queue.email_queue import start_worker
    start_worker()

    # 3. Start Telegram bot (blocking)
    logger.info("Starting Telegram bot...")
    from bot.telegram_bot import build_application
    app = build_application()
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
