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
        await query.message.edit_text(text, **kwargs)
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
                        SUM(CASE WHEN sent THEN 1 ELSE 0 END) AS sent,
                        SUM(CASE WHEN NOT sent AND (email_invalid IS NULL OR email_invalid = FALSE)
                            THEN 1 ELSE 0 END) AS pending,
                        SUM(CASE WHEN email_invalid = TRUE THEN 1 ELSE 0 END) AS invalid
                    FROM leads
                """)
                return dict(cur.fetchone())
    except Exception:
        return {"total": 0, "sent": 0, "pending": 0, "invalid": 0}


# ── teclados ──────────────────────────────────────────────────────────────────

def kb_main():
    from worker_queue.email_queue import is_paused
    paused = is_paused()
    pause_btn = (
        InlineKeyboardButton("▶️  Retomar Envios", callback_data="menu_resume")
        if paused else
        InlineKeyboardButton("⏸  Pausar Envios",  callback_data="menu_pause")
    )
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
            InlineKeyboardButton("🔁  Novo Limite Diário", callback_data="menu_reset_limit"),
        ],
        [
            InlineKeyboardButton("📡  Monitor Campanhas", callback_data="menu_monitor"),
        ],
        [pause_btn],
        [
            InlineKeyboardButton("🔃  Atualizar",          callback_data="menu_main"),
            InlineKeyboardButton("🧪  Email Teste",        callback_data="menu_test_email"),
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
    invalid = s["invalid"] or 0
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
        f"⚠️   Inválidos:      **{invalid:,}**\n"
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

        elif data == "menu_test_email":
            await _send_test_email(query)

        elif data == "menu_reset_limit":
            await _do_reset_daily_limit(query)

        elif data == "menu_monitor":
            await _show_monitor(query)

        elif data == "menu_pause":
            await _do_pause(query)

        elif data == "menu_resume":
            await _do_resume(query)

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
    from database.db import insert_lead

    use_receita = _check_table_exists()
    total_new   = 0
    stop_event  = asyncio.Event()

    # Embaralha os nichos para variar a ordem a cada coleta
    niches_ordered = NICHES[:]
    random.shuffle(niches_ordered)

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

    niche_results: dict[str, int] = {}

    async def receita_worker(niche, quota):
        if stop_event.is_set():
            return
        try:
            companies = await asyncio.to_thread(scrape_receita, niche, COUNTRY, quota)
            count = 0
            for c in companies:
                if stop_event.is_set():
                    break
                if await save_lead(c.get("company_name",""), c.get("email",""),
                                   "", c.get("phone",""), "receita_federal", niche):
                    count += 1
            niche_results[niche] = count
        except Exception as e:
            logger.error(f"[Receita] {niche}: {e}")
            niche_results[niche] = 0

    async def casadosdados_worker(niche, quota):
        if stop_event.is_set():
            return
        try:
            companies = await asyncio.to_thread(scrape_casadosdados, niche, COUNTRY, quota)
            count = 0
            for c in companies:
                if stop_event.is_set():
                    break
                if await save_lead(c.get("company_name",""), c.get("email",""),
                                   c.get("website",""), "", "casadosdados_api", niche):
                    count += 1
            niche_results[niche] = niche_results.get(niche, 0) + count
        except Exception as e:
            logger.error(f"[CasaDados] {niche}: {e}")

    progress_msg = await client.send_message(
        chat_id,
        "┌─────────────────────────────┐\n"
        "│   🚀  **Coleta em andamento...**  │\n"
        "└─────────────────────────────┘\n"
        "\n"
        f"🎯  Meta:  **{max_results:,}** emails\n"
        f"📥  Coletados: **0**\n"
        "\n"
        "_Iniciando..._",
    )

    # Distribui cota igualmente entre os nichos.
    # Nichos que retornam menos do esperado "devolvem" o saldo
    # para os próximos via recálculo dinâmico da cota.
    niches_remaining = list(niches_ordered)  # cópia para iterar com índice dinâmico
    for i, niche in enumerate(niches_ordered, 1):
        if stop_event.is_set():
            break
        remaining = max_results - total_new
        if remaining <= 0:
            break
        # Cota = saldo restante dividido pelos nichos ainda não processados
        niches_left = len(niches_ordered) - (i - 1)
        niche_quota = max(1, -(-remaining // niches_left))  # divisão com teto (ceiling)
        if use_receita:
            await receita_worker(niche, niche_quota)
        else:
            await casadosdados_worker(niche, niche_quota)

        # atualiza progresso
        done_txt = "\n".join(
            f"  ✅  {n.capitalize()}: **{niche_results[n]:,}**"
            for n in niches_ordered[:i]
            if niche_results.get(n, 0) > 0
        ) or "  _Processando..._"
        pct = int(i * 100 / len(niches_ordered))
        try:
            await progress_msg.edit_text(
                "┌─────────────────────────────┐\n"
                "│   🚀  **Coleta em andamento...**  │\n"
                "└─────────────────────────────┘\n"
                "\n"
                f"`{_bar(pct, 14)}` **{pct}%** ({i}/{len(niches_ordered)})\n"
                f"📥  Coletados: **{total_new:,}** / **{max_results:,}**\n"
                "\n"
                f"{done_txt}",
            )
        except Exception:
            pass

        await asyncio.sleep(random.uniform(1, 3))

    # ── resumo final ──────────────────────────────────────────────────────────
    from database.db import get_recent_leads
    s = _get_quick_stats()
    base_total = s["total"] or 0
    recent = get_recent_leads(limit=8) if total_new > 0 else []

    # por nicho com resultado
    niche_lines = "\n".join(
        f"  {'✅' if v > 0 else '⬜'}  {n.capitalize()}: **{v:,}**"
        for n, v in niche_results.items()
        if v > 0
    )

    # amostra de leads capturados
    sample_lines = ""
    if recent:
        sample_lines = "\n\n━━━━━━  Amostra  ━━━━━━\n"
        for lead in recent:
            name = (lead["company_name"] or "—")[:24].strip()
            email = lead["email"]
            sample_lines += f"▸ **{name}**\n  `{email}`\n"

    result_icon = "🏁" if not stop_event.is_set() else "⏹️"
    status_text = "Coleta concluída!" if not stop_event.is_set() else "Coleta interrompida"

    summary = (
        "┌─────────────────────────────┐\n"
        f"│  {result_icon}  **{status_text}**\n"
        "└─────────────────────────────┘\n"
        "\n"
        f"✨  **+{total_new:,}** novos leads salvos\n"
        f"👥  Base total: **{base_total:,}** leads\n"
    )
    if niche_lines:
        summary += f"\n━━━━━━  Por categoria  ━━━━━━\n{niche_lines}"
    summary += sample_lines

    try:
        await progress_msg.edit_text(summary, reply_markup=kb_main())
    except Exception:
        await client.send_message(chat_id, summary, reply_markup=kb_main())


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
    from worker_queue.email_queue import enqueue_leads, get_redis, QUEUE_KEY

    # Limpa fila existente para evitar duplicatas ao re-enfileirar
    r = get_redis()
    r.delete(QUEUE_KEY)

    leads = get_unsent_leads(limit=10_000)  # pega todos os não enviados
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


async def _send_test_email(query: CallbackQuery):
    from mailer.smtp_sender import send_email
    from mailer.templates import SUBJECTS

    TEST_EMAIL = "decopt10@gmail.com"
    subject = random.choice(SUBJECTS)

    await _edit(query,
        "⏳  **Enviando email de teste...**\n\n"
        f"Para: `{TEST_EMAIL}`",
        reply_markup=None,
    )

    success = await asyncio.to_thread(
        send_email,
        to=TEST_EMAIL,
        subject=subject,
        company_name="TopAgenda Teste",
        template_id=random.randint(1, 20),
    )

    if success:
        await query.message.reply(
            "✅  **Email de teste enviado!**\n\n"
            f"📬  Para: `{TEST_EMAIL}`\n"
            f"📝  Assunto: __{subject}__\n\n"
            "Verifique sua caixa de entrada.",
            reply_markup=kb_back(),
        )
    else:
        await query.message.reply(
            "❌  **Falha ao enviar email de teste.**\n\n"
            "Verifique as configurações de SMTP nos logs.",
            reply_markup=kb_back(),
        )


async def _show_monitor(query: CallbackQuery):
    from database.db import get_email_stats, get_template_stats, get_domain_stats, get_device_stats
    from worker_queue.email_queue import (
        get_daily_sent, get_daily_limit, queue_length, is_paused, _is_sending_window,
    )

    qs      = _get_quick_stats()
    s       = get_email_stats()
    sent    = s["sent"]    or 0
    opened  = s["opened"]  or 0
    clicked = s["clicked"] or 0
    devices = get_device_stats()

    total   = qs["total"]   or 0
    pending = qs["pending"] or 0
    invalid = qs["invalid"] or 0
    sent_pct = int(sent * 100 / total) if total else 0

    open_rate     = round(opened  * 100 / sent,   1) if sent   else 0.0
    click_rate    = round(clicked * 100 / sent,   1) if sent   else 0.0
    click_on_open = round(clicked * 100 / opened, 1) if opened else 0.0

    daily_sent  = get_daily_sent()
    daily_limit = get_daily_limit()
    daily_pct   = int(daily_sent * 100 / daily_limit) if daily_limit else 0
    na_fila     = queue_length()
    paused      = is_paused()
    in_window   = _is_sending_window()

    templates = get_template_stats()
    domains   = get_domain_stats()

    if paused:
        status = "⏸  Pausado"
    elif not in_window:
        status = "🌙  Fora do horário (7h–22h BRT)"
    elif daily_sent >= daily_limit:
        status = "🔴  Limite diário atingido"
    else:
        status = "🟢  Enviando"

    # ── Seção 1 — hoje ───────────────────────────────────────────────────────
    txt = (
        "📡  **Monitor de Campanhas**\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "\n"
        f"**📅  Hoje** — {status}\n"
        f"`{_bar(daily_pct, 18)}`  **{daily_pct}%**\n"
        f"📨  **{daily_sent:,}** / **{daily_limit:,}** enviados   ·   ⏳ **{na_fila:,}** na fila\n"
    )

    # ── Seção 2 — base de leads ──────────────────────────────────────────────
    txt += (
        "\n"
        "**👥  Base de Leads**\n"
        f"Total       **{total:,}**\n"
        f"`{_bar(sent_pct, 18)}`  **{sent_pct}%** enviado\n"
        f"✅  Enviados   **{sent:,}**\n"
        f"📧  Pendentes  **{pending:,}**\n"
        f"⚠️   Inválidos  **{invalid:,}**\n"
    )

    # ── Seção 3 — funil ──────────────────────────────────────────────────────
    txt += (
        "\n"
        "**📊  Funil de Conversão**\n"
        f"📨  Enviados  **{sent:,}**\n"
        f"👁  Abertos   **{opened:,}**  `{_bar(int(open_rate), 12)}`  **{open_rate}%**\n"
        f"🖱  Clicados  **{clicked:,}**  `{_bar(int(click_rate), 12)}`  **{click_rate}%**\n"
        f"🎯  Click/Open  **{click_on_open}%**\n"
    )

    # ── Seção 4 — top templates ───────────────────────────────────────────────
    medals = {0: "🥇", 1: "🥈", 2: "🥉"}
    txt += "\n**🏆  Top Templates**\n"
    if templates:
        for i, t in enumerate(templates[:5]):
            tid = t["template_id"] or "?"
            env = t["enviados"]  or 0
            ab  = t["abertos"]   or 0
            cl  = t["clicados"]  or 0
            pct = round(ab * 100 / env, 1) if env else 0.0
            icon = medals.get(i, "▸ ")
            txt += f"{icon}  T#{tid:02d}  `{_bar(int(pct), 12)}`  **{pct}%**  _{env:,}env · {ab}ab · {cl}cli_\n"
    else:
        txt += "_Nenhum dado disponível_\n"

    # ── Seção 5 — provedores ──────────────────────────────────────────────────
    txt += "\n**📮  Por Provedor**\n"
    if domains:
        for d in domains[:6]:
            dom   = (d["domain"] or "outros")[:18]
            env_d = d["enviados"]  or 0
            ab_d  = d["abertos"]   or 0
            cl_d  = d["clicados"]  or 0
            pct_d = round(ab_d * 100 / env_d, 1) if env_d else 0.0
            bar_d = _bar(int(pct_d), 8)
            txt += f"`{dom:<18}`  {env_d:,}env  `{bar_d}`  **{pct_d}%**  🖱{cl_d}\n"
    else:
        txt += "_Nenhum dado disponível_\n"

    # ── Seção 6 — dispositivos ────────────────────────────────────────────────
    open_mob  = devices.get("open_mobile",   0) or 0
    open_desk = devices.get("open_desktop",  0) or 0
    clk_mob   = devices.get("click_mobile",  0) or 0
    clk_desk  = devices.get("click_desktop", 0) or 0
    open_total = open_mob + open_desk
    clk_total  = clk_mob  + clk_desk
    open_mob_pct  = round(open_mob  * 100 / open_total, 1) if open_total else 0.0
    clk_mob_pct   = round(clk_mob   * 100 / clk_total,  1) if clk_total  else 0.0

    txt += (
        "\n**📱  Dispositivos**\n"
        f"Aberturas  📱 **{open_mob}** ({open_mob_pct}%)  🖥 **{open_desk}** ({100-open_mob_pct if open_total else 0}%)\n"
        f"Cliques    📱 **{clk_mob}** ({clk_mob_pct}%)  🖥 **{clk_desk}** ({100-clk_mob_pct if clk_total else 0}%)\n"
        "\n_Atualizado em tempo real._"
    )

    await _edit(query, txt,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄  Atualizar", callback_data="menu_monitor")],
            [InlineKeyboardButton("◀️  Voltar",    callback_data="menu_main")],
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


async def _do_reset_daily_limit(query: CallbackQuery):
    """Zera apenas o limite diário do Redis — sorteia novo valor pelo .env."""
    from worker_queue.email_queue import reset_daily_count, get_daily_limit
    from config.settings import MAILER_DAILY_MIN, MAILER_DAILY_MAX

    reset_daily_count()
    new_limit = get_daily_limit()  # sorteia e persiste novo valor

    await _edit(query,
        "✅  **Novo limite diário sorteado!**\n\n"
        f"📅  Limite hoje: **{new_limit}** emails\n"
        f"📊  Faixa configurada: **{MAILER_DAILY_MIN} – {MAILER_DAILY_MAX}**\n\n"
        "_O contador de envios foi zerado.\n"
        "Os leads já enviados continuam marcados._",
        reply_markup=kb_back(),
    )


# ── pausar / retomar envios ───────────────────────────────────────────────────

async def _do_pause(query: CallbackQuery):
    from worker_queue.email_queue import set_paused, queue_length

    set_paused(True)
    na_fila = queue_length()

    await _edit(query,
        "⏸  **Envios pausados!**\n\n"
        f"📨  Emails na fila: **{na_fila}**\n\n"
        "_O worker vai terminar o lote atual (se houver) e parar.\n"
        "Clique em **Retomar Envios** quando quiser continuar._",
        reply_markup=kb_back(),
    )


async def _do_resume(query: CallbackQuery):
    from worker_queue.email_queue import set_paused, queue_length, get_daily_sent, get_daily_limit

    set_paused(False)
    na_fila  = queue_length()
    enviados = get_daily_sent()
    limite   = get_daily_limit()

    await _edit(query,
        "▶️  **Envios retomados!**\n\n"
        f"📨  Emails na fila: **{na_fila}**\n"
        f"📅  Enviados hoje: **{enviados}/{limite}**\n\n"
        "_O worker retoma automaticamente em até 30 segundos._",
        reply_markup=kb_back(),
    )
