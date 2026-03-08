import asyncio
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


async def main():
    # 1. Banco de dados
    logger.info("Initialising database...")
    from database.db import init_db
    init_db()

    # 2. Fila de email (thread de background)
    logger.info("Starting email queue worker...")
    from worker_queue.email_queue import start_worker
    start_worker()

    # 3. Bot Telegram (Pyrogram)
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
