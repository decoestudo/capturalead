import asyncio
import io
import logging
import sys

if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger(__name__)


async def main():
    logger.info("Initialising database...")
    from database.db import init_db
    init_db()

    logger.info("Starting email queue worker...")
    from worker_queue.email_queue import start_worker
    start_worker()

    logger.info("Starting tracking server...")
    from tracking.server import start_tracking_server
    from config.settings import TRACKING_PORT
    await start_tracking_server(port=TRACKING_PORT)

    logger.info("Starting Telegram bot (Pyrogram)...")
    from bot.telegram_bot import create_client, register_handlers
    from pyrogram import idle

    client = create_client()
    register_handlers(client)

    await client.start()
    logger.info("Bot online! Aguardando mensagens...")
    await idle()
    await client.stop()


if __name__ == "__main__":
    asyncio.run(main())
