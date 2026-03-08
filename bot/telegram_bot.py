import asyncio
import logging
import random
import threading
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)
from config.settings import TELEGRAM_TOKEN, TELEGRAM_ADMIN_CHAT_ID

logger = logging.getLogger(__name__)

# ── helpers ──────────────────────────────────────────────────────────────────

def _is_admin(update: Update) -> bool:
    if not TELEGRAM_ADMIN_CHAT_ID:
        return True  # No restriction if not set
    return str(update.effective_chat.id) == str(TELEGRAM_ADMIN_CHAT_ID)


async def _reply(update: Update, text: str, **kwargs):
    await update.effective_message.reply_text(text, **kwargs)


# ── /start ────────────────────────────────────────────────────────────────────

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _reply(
        update,
        "🤖 *TopAgenda Lead Bot*\n\n"
        "Comandos disponíveis:\n"
        "`/start_scraping <pais> <quantidade>` — inicia coleta de leads\n"
        "`/show_leads [pagina]` — lista leads coletados\n"
        "`/send_campaign` — envia campanha por email\n"
        "`/stats` — estatísticas do banco\n"
        "`/daily_stats` — envios de hoje\n"
        "`/reset_sent` — permite reenviar emails já enviados",
        parse_mode="Markdown",
    )


# ── /start_scraping ───────────────────────────────────────────────────────────

async def cmd_start_scraping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _is_admin(update):
        await _reply(update, "Acesso negado.")
        return

    args = context.args
    if len(args) < 2:
        await _reply(update, "Uso: `/start_scraping <pais> <quantidade>`", parse_mode="Markdown")
        return

    country = args[0]
    try:
        max_results = int(args[1])
    except ValueError:
        await _reply(update, "Quantidade deve ser um número inteiro.")
        return

    await _reply(update, f"Iniciando scraping: país=*{country}*, máx=*{max_results}*...", parse_mode="Markdown")

    chat_id = update.effective_chat.id
    app = context.application

    asyncio.create_task(_scraping_task(app, chat_id, country, max_results))


async def _scraping_task(app, chat_id: int, country: str, max_results: int):
    from config.settings import NICHES
    from scraper.receita_scraper import scrape_receita, _check_table_exists
    from scraper.casadosdados_scraper import scrape_casadosdados
    from scraper.google_maps_scraper import scrape_google_maps, scrape_bing_emails
    from scraper.email_extractor import extract_emails
    from database.db import insert_lead
    import asyncio

    use_receita = _check_table_exists()

    total_new = 0
    stop_event = asyncio.Event()
    seen_websites: set = set()

    async def save_lead(company_name: str, email: str, website: str, phone: str, source: str, niche: str) -> bool:
        nonlocal total_new
        if not email or "@" not in email:
            return False
        inserted = await asyncio.to_thread(
            insert_lead,
            company_name=company_name,
            email=email.lower(),
            website=website,
            phone=phone,
            source=source,
            niche=niche,
            country=country,
        )
        if inserted:
            total_new += 1
            logger.info(f"💾 Lead salvo: {company_name} <{email}>")
            if total_new >= max_results:
                stop_event.set()
        return bool(inserted)

    async def receita_worker(niche: str):
        """Consulta direto na tabela local da Receita Federal — sem API, sem limite."""
        if stop_event.is_set():
            return
        try:
            companies = await asyncio.to_thread(scrape_receita, niche, country, max_results)
            count = 0
            for company in companies:
                if stop_event.is_set():
                    break
                if await save_lead(company.get("company_name", ""), company.get("email", ""), "", company.get("phone", ""), "receita_federal", niche):
                    count += 1
            status = f"✅ Receita [{niche}]: {count} leads salvos." if count > 0 else f"ℹ️ Receita [{niche}]: nenhum lead novo."
            await app.bot.send_message(chat_id, status)
        except Exception as e:
            logger.error(f"[Receita worker] {niche}: {e}")
            await app.bot.send_message(chat_id, f"⚠️ Erro Receita [{niche}]: {e}")

    async def casadosdados_worker(niche: str):
        """API Casa dos Dados — fallback quando tabela Receita não está disponível."""
        if stop_event.is_set():
            return
        try:
            companies = await asyncio.to_thread(scrape_casadosdados, niche, country, max_results)
            count = 0
            for company in companies:
                if stop_event.is_set():
                    break
                if await save_lead(company.get("company_name", ""), company.get("email", ""), company.get("website", ""), "", "casadosdados_api", niche):
                    count += 1
            status = f"✅ CasaDados [{niche}]: {count} emails salvos." if count > 0 else f"ℹ️ CasaDados [{niche}]: nenhum email encontrado."
            await app.bot.send_message(chat_id, status)
        except Exception as e:
            logger.error(f"[CasaDados worker] {niche}: {e}")
            await app.bot.send_message(chat_id, f"⚠️ Erro CasaDados [{niche}]: {e}")

    async def maps_worker(niche: str):
        """Google Maps → visita sites das empresas → extrai emails."""
        if stop_event.is_set():
            return
        try:
            companies = await scrape_google_maps(niche, country, max_results=max_results, seen_websites=seen_websites)
            count = 0
            for company in companies:
                if stop_event.is_set():
                    break
                # Emails diretos encontrados na página do Maps
                for email in company.get("direct_emails", []):
                    if await save_lead(company.get("company_name", ""), email, company.get("website", ""), company.get("phone", ""), "google_maps", niche):
                        count += 1

                # Visita o site da empresa para buscar mais emails
                website = company.get("website")
                if website and not stop_event.is_set():
                    emails_from_site = await asyncio.to_thread(extract_emails, website)
                    for email in emails_from_site:
                        if stop_event.is_set():
                            break
                        if await save_lead(company.get("company_name", ""), email, website, company.get("phone", ""), "google_maps_site", niche):
                            count += 1

            status = f"✅ Maps [{niche}]: {count} emails salvos." if count > 0 else f"ℹ️ Maps [{niche}]: nenhum email encontrado."
            await app.bot.send_message(chat_id, status)
        except Exception as e:
            logger.error(f"[Maps worker] {niche}: {e}")
            await app.bot.send_message(chat_id, f"⚠️ Erro Maps [{niche}]: {e}")

    async def bing_worker(niche: str):
        """Bing Search — busca emails diretamente nos snippets de resultado."""
        if stop_event.is_set():
            return
        try:
            companies = await scrape_bing_emails(niche, country, max_results=max_results)
            count = 0
            for company in companies:
                if stop_event.is_set():
                    break
                for email in company.get("direct_emails", []):
                    if await save_lead(company.get("company_name", ""), email, company.get("website", ""), company.get("phone", ""), "bing_search", niche):
                        count += 1

            status = f"✅ Bing [{niche}]: {count} emails salvos." if count > 0 else f"ℹ️ Bing [{niche}]: nenhum email encontrado."
            await app.bot.send_message(chat_id, status)
        except Exception as e:
            logger.error(f"[Bing worker] {niche}: {e}")
            await app.bot.send_message(chat_id, f"⚠️ Erro Bing [{niche}]: {e}")

    fonte = "Receita Federal (local)" if use_receita else "Casa dos Dados API + Google Maps"
    await app.bot.send_message(
        chat_id,
        f"🚀 Iniciando coleta via {fonte} para {len(NICHES)} nichos...\n"
        f"  Limite total: {max_results} leads"
    )

    for niche in NICHES:
        if stop_event.is_set():
            break
        if use_receita:
            # Fonte principal: banco local da Receita Federal (rápido, ilimitado)
            await receita_worker(niche)
        else:
            # Fallback: APIs externas
            await casadosdados_worker(niche)
            if not stop_event.is_set():
                await maps_worker(niche)
            if not stop_event.is_set():
                await bing_worker(niche)
        await asyncio.sleep(random.uniform(1, 3))

    # Mensagem final em texto puro (sem Markdown) para evitar crashes
    from database.db import get_recent_leads
    recent = get_recent_leads(limit=min(total_new, 30)) if total_new > 0 else []

    lines = [f"🏁 Scraping concluído! {total_new} leads salvos (limite: {max_results})"]
    if recent:
        lines.append("\n📋 Leads capturados:")
        for lead in recent:
            name = (lead['company_name'] or 'N/A')[:30]
            email = lead['email'] or ''
            lines.append(f"  • {name} → {email}")
        lines.append("\n👉 Para enviar a campanha: /send_campaign")

    await app.bot.send_message(chat_id, "\n".join(lines))



# ── /show_leads ───────────────────────────────────────────────────────────────

async def cmd_show_leads(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _is_admin(update):
        await _reply(update, "Acesso negado.")
        return

    from database.db import get_recent_leads

    page = 0
    if context.args:
        try:
            page = max(0, int(context.args[0]) - 1)
        except ValueError:
            pass

    leads = get_recent_leads(limit=20, offset=page * 20)

    if not leads:
        await _reply(update, "Nenhum lead encontrado.")
        return

    lines = [f"📋 *Leads* (página {page + 1}):\n"]
    for lead in leads:
        status = "✅" if lead["sent"] else "📧"
        lines.append(
            f"{status} *{lead['company_name'] or 'N/A'}*\n"
            f"   `{lead['email']}`\n"
            f"   Nicho: {lead['niche'] or '—'} | País: {lead['country'] or '—'}"
        )

    await _reply(update, "\n".join(lines), parse_mode="Markdown")


# ── /send_campaign ────────────────────────────────────────────────────────────

async def cmd_send_campaign(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _is_admin(update):
        await _reply(update, "Acesso negado.")
        return

    from database.db import count_unsent

    unsent = count_unsent()
    if unsent == 0:
        await _reply(update, "Não há leads para enviar.")
        return

    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton(f"✅ Autorizar envio para {unsent} leads", callback_data="confirm_send")]]
    )
    await _reply(
        update,
        f"📤 Há *{unsent}* leads aguardando envio.\nDeseja iniciar a campanha?",
        parse_mode="Markdown",
        reply_markup=keyboard,
    )


async def callback_confirm_send(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    from database.db import get_unsent_leads
    from worker_queue.email_queue import enqueue_leads

    leads = get_unsent_leads(limit=500)
    if not leads:
        await query.edit_message_text("Não há leads para enviar.")
        return

    lead_ids = [lead["id"] for lead in leads]
    enqueue_leads(lead_ids)

    await query.edit_message_text(
        f"🚀 *{len(lead_ids)}* leads adicionados à fila de envio!\nO envio ocorrerá em lotes automáticos.",
        parse_mode="Markdown",
    )


# ── /stats ────────────────────────────────────────────────────────────────────

async def cmd_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _is_admin(update):
        await _reply(update, "Acesso negado.")
        return

    from database.db import get_connection
    from psycopg2.extras import RealDictCursor

    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT
                    COUNT(*) AS total,
                    SUM(CASE WHEN sent THEN 1 ELSE 0 END) AS sent_count,
                    SUM(CASE WHEN NOT sent THEN 1 ELSE 0 END) AS unsent_count
                FROM leads
                """
            )
            stats = cur.fetchone()

    await _reply(
        update,
        f"📊 *Estatísticas*:\n"
        f"  Total de leads: *{stats['total']}*\n"
        f"  Enviados: *{stats['sent_count']}*\n"
        f"  Pendentes: *{stats['unsent_count']}*",
        parse_mode="Markdown",
    )


# ── /daily_stats ──────────────────────────────────────────────────────────────

async def cmd_daily_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _is_admin(update):
        await _reply(update, "Acesso negado.")
        return

    from worker_queue.email_queue import get_daily_sent, get_daily_limit, queue_length

    sent = get_daily_sent()
    limit = get_daily_limit()
    queue = queue_length()
    pct = int(sent * 100 / limit) if limit else 0

    bar_filled = int(pct / 10)
    bar = "█" * bar_filled + "░" * (10 - bar_filled)

    await _reply(
        update,
        f"📬 *Envios de hoje*\n\n"
        f"`{bar}` {pct}%\n"
        f"Enviados: *{sent}* / *{limit}*\n"
        f"Na fila: *{queue}*\n"
        f"Restante hoje: *{max(0, limit - sent)}*",
        parse_mode="Markdown",
    )


# ── /reset_sent ────────────────────────────────────────────────────────────────

async def cmd_reset_sent(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _is_admin(update):
        await _reply(update, "Acesso negado.")
        return

    from database.db import get_connection
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM leads WHERE sent = TRUE")
            count = cur.fetchone()[0]

    if count == 0:
        await _reply(update, "Nenhum lead marcado como enviado.")
        return

    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton(f"✅ Confirmar reset de {count} leads", callback_data="confirm_reset_sent")
    ]])
    await _reply(
        update,
        f"⚠️ Isso vai marcar *{count}* leads como não enviados.\n"
        f"Eles poderão receber email novamente na próxima campanha.",
        parse_mode="Markdown",
        reply_markup=keyboard,
    )


async def callback_confirm_reset_sent(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    from database.db import get_connection
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE leads SET sent = FALSE")
            count = cur.rowcount
        conn.commit()

    from worker_queue.email_queue import reset_daily_count
    reset_daily_count()

    await query.edit_message_text(
        f"✅ *{count}* leads resetados para não enviado.\n"
        f"Contador diário zerado. Use /send_campaign para reenviar.",
        parse_mode="Markdown",
    )


# ── Application factory ───────────────────────────────────────────────────────

def build_application() -> Application:
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("start_scraping", cmd_start_scraping))
    app.add_handler(CommandHandler("show_leads", cmd_show_leads))
    app.add_handler(CommandHandler("send_campaign", cmd_send_campaign))
    app.add_handler(CommandHandler("stats", cmd_stats))
    app.add_handler(CommandHandler("daily_stats", cmd_daily_stats))
    app.add_handler(CommandHandler("reset_sent", cmd_reset_sent))
    app.add_handler(CallbackQueryHandler(callback_confirm_send, pattern="^confirm_send$"))
    app.add_handler(CallbackQueryHandler(callback_confirm_reset_sent, pattern="^confirm_reset_sent$"))
    return app
