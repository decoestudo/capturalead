import asyncio
import logging
import random

from pyrogram import Client, filters
from pyrogram.types import (
    Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton,
)

from config.settings import (
    TELEGRAM_TOKEN, TELEGRAM_ADMIN_CHAT_ID,
    TELEGRAM_API_ID, TELEGRAM_API_HASH,
)

logger = logging.getLogger(__name__)

COUNTRY = "brasil"
_awaiting_qty: set[int] = set()


async def _edit(query: "CallbackQuery", text: str, **kwargs):
    """Edita mensagem ignorando erro de conteúdo idêntico."""
    try:
        await _edit(query,text, **kwargs)
    except Exception as e:
        if "MESSAGE_NOT_MODIFIED" not in str(e):
            raise


# ── client ────────────────────────────────────────────────────────────────────

def create_client() -> Client:
    return Client(
        name="leadbot",
        api_id=TELEGRAM_API_ID,
        api_hash=TELEGRAM_API_HASH,
        bot_token=TELEGRAM_TOKEN,
    )


def _is_admin(chat_id: int) -> bool:
    if not TELEGRAM_ADMIN_CHAT_ID:
        return True
    return str(chat_id) == str(TELEGRAM_ADMIN_CHAT_ID)


# ── helpers visuais ───────────────────────────────────────────────────────────

def _bar(pct: int, size: int = 12) -> str:
    filled = int(pct * size / 100)
    return "▓" * filled + "░" * (size - filled)


def _get_quick_stats() -> dict:
    try:
        from database.db import get_connection
        from psycopg2.extras import RealDictCursor
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT
                        COUNT(*) AS total,
                        SUM(CASE WHEN sent     THEN 1 ELSE 0 END) AS sent,
                        SUM(CASE WHEN NOT sent THEN 1 ELSE 0 END) AS pending
                    FROM leads
                """)
                return dict(cur.fetchone())
    except Exception:
        return {"total": 0, "sent": 0, "pending": 0}


# ── teclados ──────────────────────────────────────────────────────────────────

def kb_main():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔍  Coletar Leads",   callback_data="menu_scrape"),
            InlineKeyboardButton("📤  Enviar Campanha", callback_data="menu_campaign"),
        ],
        [
            InlineKeyboardButton("📋  Ver Leads",       callback_data="leads_p1"),
            InlineKeyboardButton("📊  Estatísticas",    callback_data="menu_stats"),
        ],
        [
            InlineKeyboardButton("📬  Envios Hoje",     callback_data="menu_daily"),
            InlineKeyboardButton("🔄  Resetar Enviados",callback_data="menu_reset"),
        ],
        [
            InlineKeyboardButton("🔃  Atualizar",       callback_data="menu_main"),
        ],
    ])


def kb_quantity():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("  10  ", callback_data="qty_10"),
            InlineKeyboardButton("  50  ", callback_data="qty_50"),
            InlineKeyboardButton(" 100  ", callback_data="qty_100"),
        ],
        [
            InlineKeyboardButton(" 200  ", callback_data="qty_200"),
            InlineKeyboardButton(" 500  ", callback_data="qty_500"),
            InlineKeyboardButton("✏️ Outro", callback_data="qty_custom"),
        ],
        [InlineKeyboardButton("◀️  Voltar ao Menu", callback_data="menu_main")],
    ])


def kb_back():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("◀️  Voltar ao Menu", callback_data="menu_main")]
    ])


def kb_leads_nav(page: int, has_more: bool):
    nav = []
    if page > 1:
        nav.append(InlineKeyboardButton(f"◀️ Pág {page - 1}", callback_data=f"leads_p{page - 1}"))
    if has_more:
        nav.append(InlineKeyboardButton(f"Pág {page + 1} ▶️", callback_data=f"leads_p{page + 1}"))
    rows = ([nav] if nav else []) + [[InlineKeyboardButton("◀️  Voltar ao Menu", callback_data="menu_main")]]
    return InlineKeyboardMarkup(rows)


# ── texto do menu principal (com stats ao vivo) ───────────────────────────────

def _main_menu_text() -> str:
    s = _get_quick_stats()
    total   = s["total"]   or 0
    sent    = s["sent"]    or 0
    pending = s["pending"] or 0
    pct     = int(sent * 100 / total) if total else 0

    return (
        "┌─────────────────────────────┐\n"
        "│   🤖  **TopAgenda Lead Bot**   │\n"
        "└─────────────────────────────┘\n"
        "\n"
        "━━━━━━  📊 Resumo  ━━━━━━\n"
        f"👥  Total de leads:  **{total:,}**\n"
        f"✅  Enviados:        **{sent:,}**\n"
        f"📧  Pendentes:      **{pending:,}**\n"
        f"`{_bar(pct)}` **{pct}%** enviado\n"
        "\n"
        "━━━━━━  Menu  ━━━━━━"
    )


# ── handlers ──────────────────────────────────────────────────────────────────

def register_handlers(client: Client):

    @client.on_message(filters.command("start") & filters.private)
    async def cmd_start(_, message: Message):
        if not _is_admin(message.chat.id):
            await message.reply("⛔ Acesso negado.")
            return
        await message.reply(_main_menu_text(), reply_markup=kb_main())

    @client.on_callback_query()
    async def on_callback(_, query: CallbackQuery):
        if not _is_admin(query.message.chat.id):
            await query.answer("⛔ Acesso negado.", show_alert=True)
            return

        data = query.data
        await query.answer()

        # ── menu principal ────────────────────────────────────────────────
        if data == "menu_main":
            await _edit(query, _main_menu_text(), reply_markup=kb_main())

        # ── coletar leads ─────────────────────────────────────────────────
        elif data == "menu_scrape":
            await _edit(query,
                "┌─────────────────────────────┐\n"
                "│   🔍  **Coletar Leads**         │\n"
                "└─────────────────────────────┘\n"
                "\n"
                "Selecione a quantidade de leads\n"
                "que deseja coletar:\n"
                "\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
                reply_markup=kb_quantity(),
            )

        elif data.startswith("qty_"):
            val = data[4:]
            if val == "custom":
                _awaiting_qty.add(query.message.chat.id)
                await _edit(query,
                    "✏️  **Digite a quantidade desejada:**\n"
                    "__Ex: 300, 1000, 5000__\n\n"
                    "> A coleta para quando atingir o número informado.",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("❌  Cancelar", callback_data="menu_main")]
                    ]),
                )
            else:
                qty = int(val)
                await _edit(query,
                    f"⏳  **Iniciando coleta de {qty} leads...**\n\n"
                    f"Acompanhe as atualizações abaixo.\n"
                    f"__Não é necessário aguardar — o bot avisa quando terminar.__"
                )
                asyncio.create_task(_scraping_task(query._client, query.message.chat.id, qty))

        # ── ver leads ─────────────────────────────────────────────────────
        elif data.startswith("leads_p"):
            await _show_leads_page(query, int(data[7:]))

        # ── estatísticas ──────────────────────────────────────────────────
        elif data == "menu_stats":
            await _show_stats(query)

        # ── envios do dia ─────────────────────────────────────────────────
        elif data == "menu_daily":
            await _show_daily(query)

        # ── campanha ──────────────────────────────────────────────────────
        elif data == "menu_campaign":
            await _show_campaign_confirm(query)

        elif data == "confirm_send":
            await _do_send_campaign(query)

        # ── reset ─────────────────────────────────────────────────────────
        elif data == "menu_reset":
            await _show_reset_confirm(query)

        elif data == "confirm_reset_sent":
            await _do_reset_sent(query)

    @client.on_message(filters.text & filters.private & ~filters.command(["start"]))
    async def on_text(_, message: Message):
        chat_id = message.chat.id
        if not _is_admin(chat_id):
            return
        if chat_id not in _awaiting_qty:
            return

        _awaiting_qty.discard(chat_id)

        try:
            qty = int(message.text.strip())
            if qty <= 0:
                raise ValueError
        except ValueError:
            await message.reply(
                "❌  **Valor inválido.**\nDigite um número inteiro positivo.",
                reply_markup=kb_back(),
            )
            return

        await message.reply(
            f"⏳  **Iniciando coleta de {qty} leads...**\n\n"
            f"__O bot avisa quando terminar.__"
        )
        asyncio.create_task(_scraping_task(message._client, chat_id, qty))


# ── scraping task ─────────────────────────────────────────────────────────────

async def _scraping_task(client: Client, chat_id: int, max_results: int):
    from config.settings import NICHES
    from scraper.receita_scraper import scrape_receita, _check_table_exists
    from scraper.casadosdados_scraper import scrape_casadosdados
    from scraper.google_maps_scraper import scrape_google_maps, scrape_bing_emails
    from scraper.email_extractor import extract_emails
    from database.db import insert_lead

    use_receita = _check_table_exists()
    total_new   = 0
    stop_event  = asyncio.Event()
    seen_websites: set = set()

    async def save_lead(company_name, email, website, phone, source, niche) -> bool:
        nonlocal total_new
        if not email or "@" not in email:
            return False
        inserted = await asyncio.to_thread(
            insert_lead,
            company_name=company_name, email=email.lower(),
            website=website, phone=phone,
            source=source, niche=niche, country=COUNTRY,
        )
        if inserted:
            total_new += 1
            if total_new >= max_results:
                stop_event.set()
        return bool(inserted)

    async def receita_worker(niche):
        if stop_event.is_set():
            return
        try:
            companies = await asyncio.to_thread(scrape_receita, niche, COUNTRY, max_results)
            count = 0
            for c in companies:
                if stop_event.is_set():
                    break
                if await save_lead(c.get("company_name",""), c.get("email",""),
                                   "", c.get("phone",""), "receita_federal", niche):
                    count += 1
            if count:
                await client.send_message(chat_id, f"✅  **{niche}** — {count} leads encontrados")
        except Exception as e:
            logger.error(f"[Receita] {niche}: {e}")

    async def casadosdados_worker(niche):
        if stop_event.is_set():
            return
        try:
            companies = await asyncio.to_thread(scrape_casadosdados, niche, COUNTRY, max_results)
            count = 0
            for c in companies:
                if stop_event.is_set():
                    break
                if await save_lead(c.get("company_name",""), c.get("email",""),
                                   c.get("website",""), "", "casadosdados_api", niche):
                    count += 1
            if count:
                await client.send_message(chat_id, f"✅  **{niche}** — {count} leads encontrados")
        except Exception as e:
            logger.error(f"[CasaDados] {niche}: {e}")

    async def maps_worker(niche):
        if stop_event.is_set():
            return
        try:
            companies = await scrape_google_maps(niche, COUNTRY, max_results=max_results, seen_websites=seen_websites)
            count = 0
            for c in companies:
                if stop_event.is_set():
                    break
                for email in c.get("direct_emails", []):
                    if await save_lead(c.get("company_name",""), email,
                                       c.get("website",""), c.get("phone",""), "google_maps", niche):
                        count += 1
                website = c.get("website")
                if website and not stop_event.is_set():
                    for email in await asyncio.to_thread(extract_emails, website):
                        if stop_event.is_set():
                            break
                        await save_lead(c.get("company_name",""), email, website,
                                        c.get("phone",""), "google_maps_site", niche)
            if count:
                await client.send_message(chat_id, f"✅  **{niche}** — {count} leads encontrados")
        except Exception as e:
            logger.error(f"[Maps] {niche}: {e}")

    async def bing_worker(niche):
        if stop_event.is_set():
            return
        try:
            companies = await scrape_bing_emails(niche, COUNTRY, max_results=max_results)
            count = 0
            for c in companies:
                if stop_event.is_set():
                    break
                for email in c.get("direct_emails", []):
                    if await save_lead(c.get("company_name",""), email,
                                       c.get("website",""), c.get("phone",""), "bing_search", niche):
                        count += 1
            if count:
                await client.send_message(chat_id, f"✅  **{niche}** — {count} leads encontrados")
        except Exception as e:
            logger.error(f"[Bing] {niche}: {e}")

    await client.send_message(
        chat_id,
        f"━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🚀  **Coleta iniciada**\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🏷️   Nichos: **{len(NICHES)}** categorias\n"
        f"🎯  Meta:   **{max_results}** leads\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━",
    )

    for niche in NICHES:
        if stop_event.is_set():
            break
        if use_receita:
            await receita_worker(niche)
        else:
            await casadosdados_worker(niche)
            if not stop_event.is_set():
                await maps_worker(niche)
            if not stop_event.is_set():
                await bing_worker(niche)
        await asyncio.sleep(random.uniform(1, 3))

    from database.db import get_recent_leads
    recent = get_recent_leads(limit=min(total_new, 10)) if total_new > 0 else []

    lines = [
        "━━━━━━━━━━━━━━━━━━━━━━━",
        f"🏁  **Coleta concluída!**",
        f"📥  **{total_new}** novos leads salvos",
        "━━━━━━━━━━━━━━━━━━━━━━━",
    ]
    if recent:
        lines.append("\n📋  **Últimos capturados:**")
        for lead in recent:
            name = (lead["company_name"] or "N/A")[:28]
            lines.append(f"  `{lead['email']}`\n  _{name}_")

    await client.send_message(chat_id, "\n".join(lines), reply_markup=kb_main())


# ── ver leads ─────────────────────────────────────────────────────────────────

async def _show_leads_page(query: CallbackQuery, page: int):
    from database.db import get_recent_leads

    limit = 8
    leads = get_recent_leads(limit=limit + 1, offset=(page - 1) * limit)
    has_more = len(leads) > limit
    leads = leads[:limit]

    if not leads:
        await _edit(query,
            "📭  **Nenhum lead encontrado.**\n\nUse **Coletar Leads** para começar.",
            reply_markup=kb_back(),
        )
        return

    lines = [
        f"┌─────────────────────────────┐",
        f"│  📋  **Leads** — Página {page}        │",
        f"└─────────────────────────────┘",
        "",
    ]
    for i, lead in enumerate(leads, 1):
        icon = "✅" if lead["sent"] else "📧"
        name = (lead["company_name"] or "N/A")[:26]
        lines.append(f"{icon}  **{name}**")
        lines.append(f"    `{lead['email']}`")
        if i < len(leads):
            lines.append("─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─")

    await _edit(query,
        "\n".join(lines),
        reply_markup=kb_leads_nav(page, has_more),
    )


# ── estatísticas ──────────────────────────────────────────────────────────────

async def _show_stats(query: CallbackQuery):
    from database.db import get_connection
    from psycopg2.extras import RealDictCursor
    from worker_queue.email_queue import get_daily_sent, get_daily_limit

    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT
                    COUNT(*) AS total,
                    SUM(CASE WHEN sent     THEN 1 ELSE 0 END) AS sent_count,
                    SUM(CASE WHEN NOT sent THEN 1 ELSE 0 END) AS unsent_count,
                    COUNT(DISTINCT niche)  AS niches,
                    COUNT(DISTINCT source) AS sources
                FROM leads
            """)
            s = cur.fetchone()

    total   = s["total"]        or 0
    sent    = s["sent_count"]   or 0
    pending = s["unsent_count"] or 0
    pct     = int(sent * 100 / total) if total else 0

    daily_sent  = get_daily_sent()
    daily_limit = get_daily_limit()
    daily_pct   = int(daily_sent * 100 / daily_limit) if daily_limit else 0

    await _edit(query,
        "┌─────────────────────────────┐\n"
        "│   📊  **Estatísticas**          │\n"
        "└─────────────────────────────┘\n"
        "\n"
        "━━━━━━  Base de Leads  ━━━━━━\n"
        f"👥  Total:      **{total:,}**\n"
        f"✅  Enviados:   **{sent:,}**\n"
        f"📧  Pendentes:  **{pending:,}**\n"
        f"🏷️   Nichos:     **{s['niches']}** categorias\n"
        f"`{_bar(pct)}` **{pct}%**\n"
        "\n"
        "━━━━━━  Hoje  ━━━━━━\n"
        f"📬  Enviados hoje:  **{daily_sent}** / **{daily_limit}**\n"
        f"`{_bar(daily_pct)}` **{daily_pct}%**",
        reply_markup=kb_back(),
    )


# ── envios do dia ─────────────────────────────────────────────────────────────

async def _show_daily(query: CallbackQuery):
    from worker_queue.email_queue import get_daily_sent, get_daily_limit, queue_length

    sent  = get_daily_sent()
    limit = get_daily_limit()
    queue = queue_length()
    pct   = int(sent * 100 / limit) if limit else 0

    status = "🟢 Ativo" if sent < limit else "🔴 Limite atingido"

    await _edit(query,
        "┌─────────────────────────────┐\n"
        "│   📬  **Envios de Hoje**        │\n"
        "└─────────────────────────────┘\n"
        "\n"
        f"Status:   {status}\n"
        f"`{_bar(pct, 14)}` **{pct}%**\n"
        "\n"
        f"✉️   Enviados:   **{sent}** / **{limit}**\n"
        f"⏳  Na fila:    **{queue}**\n"
        f"🕐  Restante:   **{max(0, limit - sent)}**\n"
        "\n"
        "_Os emails são enviados em lotes aleatórios\nao longo do dia para evitar bloqueios._",
        reply_markup=kb_back(),
    )


# ── campanha ──────────────────────────────────────────────────────────────────

async def _show_campaign_confirm(query: CallbackQuery):
    from database.db import count_unsent

    unsent = count_unsent()
    if unsent == 0:
        await _edit(query,
            "📭  **Nenhum lead pendente.**\n\nTodos os leads já foram contactados.\nUse **Coletar Leads** para adicionar mais.",
            reply_markup=kb_back(),
        )
        return

    await _edit(query,
        "┌─────────────────────────────┐\n"
        "│   📤  **Enviar Campanha**       │\n"
        "└─────────────────────────────┘\n"
        "\n"
        f"📧  **{unsent:,}** leads aguardando envio\n"
        f"📅  Limite diário: **100–300** emails\n"
        f"⏱️   Envio em lotes com intervalos aleatórios\n"
        "\n"
        "> Confirme para adicionar todos à fila.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(f"✅  Confirmar — Enviar para {unsent:,} leads", callback_data="confirm_send")],
            [InlineKeyboardButton("❌  Cancelar", callback_data="menu_main")],
        ]),
    )


async def _do_send_campaign(query: CallbackQuery):
    from database.db import get_unsent_leads
    from worker_queue.email_queue import enqueue_leads

    leads = get_unsent_leads(limit=500)
    if not leads:
        await _edit(query,"📭  Não há leads para enviar.", reply_markup=kb_back())
        return

    lead_ids = [lead["id"] for lead in leads]
    enqueue_leads(lead_ids)

    await _edit(query,
        "┌─────────────────────────────┐\n"
        "│   🚀  **Campanha Iniciada!**    │\n"
        "└─────────────────────────────┘\n"
        "\n"
        f"📨  **{len(lead_ids):,}** leads adicionados à fila\n"
        f"📅  Envio: **100–300** por dia\n"
        f"⏱️   Lotes automáticos com pausas aleatórias\n"
        "\n"
        "_Acompanhe o progresso em **Envios Hoje**._",
        reply_markup=kb_back(),
    )


# ── reset enviados ────────────────────────────────────────────────────────────

async def _show_reset_confirm(query: CallbackQuery):
    from database.db import get_connection

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM leads WHERE sent = TRUE")
            count = cur.fetchone()[0]

    if count == 0:
        await _edit(query,
            "ℹ️  **Nenhum lead enviado ainda.**",
            reply_markup=kb_back(),
        )
        return

    await _edit(query,
        "┌─────────────────────────────┐\n"
        "│   🔄  **Resetar Enviados**      │\n"
        "└─────────────────────────────┘\n"
        "\n"
        f"⚠️  **{count:,}** leads serão marcados como\n"
        f"__não enviados__ e poderão receber email\n"
        f"novamente na próxima campanha.\n"
        "\n"
        "> Esta ação não pode ser desfeita.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(f"⚠️  Confirmar reset de {count:,} leads", callback_data="confirm_reset_sent")],
            [InlineKeyboardButton("❌  Cancelar", callback_data="menu_main")],
        ]),
    )


async def _do_reset_sent(query: CallbackQuery):
    from database.db import get_connection
    from worker_queue.email_queue import reset_daily_count

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE leads SET sent = FALSE")
            count = cur.rowcount
        conn.commit()

    reset_daily_count()

    await _edit(query,
        f"✅  **Reset concluído!**\n\n"
        f"**{count:,}** leads marcados como não enviados.\n"
        f"Contador diário zerado.",
        reply_markup=kb_back(),
    )
