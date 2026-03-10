import re
import smtplib
import logging
from datetime import date
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from config.settings import (
    SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, EMAIL_FROM, TRACKING_BASE_URL,
    BREVO_SMTP_HOST, BREVO_SMTP_PORT, BREVO_SMTP_USER, BREVO_SMTP_PASS, BREVO_DAILY_LIMIT,
    RESEND_SMTP_HOST, RESEND_SMTP_PORT, RESEND_SMTP_USER, RESEND_SMTP_PASS, RESEND_DAILY_LIMIT,
    MAILJET_SMTP_HOST, MAILJET_SMTP_PORT, MAILJET_SMTP_USER, MAILJET_SMTP_PASS, MAILJET_DAILY_LIMIT,
)

logger = logging.getLogger(__name__)

UNSUBSCRIBE_URL = "https://topagenda.online/unsubscribe"


def _get_redis():
    import redis as redis_lib
    from config.settings import REDIS_URL
    return redis_lib.from_url(REDIS_URL, decode_responses=True)


def _count_today(prefix: str) -> int:
    try:
        r = _get_redis()
        val = r.get(f"{prefix}{date.today().isoformat()}")
        return int(val) if val else 0
    except Exception:
        return 0


def _increment_today(prefix: str) -> None:
    try:
        r = _get_redis()
        key = f"{prefix}{date.today().isoformat()}"
        pipe = r.pipeline()
        pipe.incr(key)
        pipe.expire(key, 90000)  # 25 horas
        pipe.execute()
    except Exception:
        pass


def _send_via_resend(msg_str: str, from_addr: str, to_addr: str) -> None:
    """Envia via Resend usando SMTP_SSL (porta 465)."""
    with smtplib.SMTP_SSL(RESEND_SMTP_HOST, RESEND_SMTP_PORT) as server:
        server.login(RESEND_SMTP_USER, RESEND_SMTP_PASS)
        server.sendmail(from_addr, [to_addr], msg_str)


def _send_via_brevo(msg_str: str, from_addr: str, to_addr: str) -> None:
    """Envia via Brevo usando STARTTLS (porta 587)."""
    with smtplib.SMTP(BREVO_SMTP_HOST, BREVO_SMTP_PORT) as server:
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(BREVO_SMTP_USER, BREVO_SMTP_PASS)
        server.sendmail(from_addr, [to_addr], msg_str)


def _send_via_mailjet(msg_str: str, from_addr: str, to_addr: str) -> None:
    """Envia via Mailjet usando STARTTLS (porta 587)."""
    with smtplib.SMTP(MAILJET_SMTP_HOST, MAILJET_SMTP_PORT) as server:
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(MAILJET_SMTP_USER, MAILJET_SMTP_PASS)
        server.sendmail(from_addr, [to_addr], msg_str)


def _send_via_hostinger(msg_str: str, from_addr: str, to_addr: str) -> None:
    """Envia via Hostinger usando SMTP_SSL (porta 465)."""
    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as server:
        server.login(SMTP_USER, SMTP_PASS)
        server.sendmail(from_addr, [to_addr], msg_str)


def _html_to_text(html: str) -> str:
    """Converte HTML para texto puro simples (para MIME multipart/alternative)."""
    text = re.sub(r"<br\s*/?>", "\n", html, flags=re.IGNORECASE)
    text = re.sub(r"</p>|</tr>|</div>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"&nbsp;", " ", text)
    text = re.sub(r"&amp;", "&", text)
    text = re.sub(r"&lt;", "<", text)
    text = re.sub(r"&gt;", ">", text)
    text = re.sub(r" {2,}", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def send_email(to: str, subject: str, company_name: str = "",
               template_id: int = 1, lead_id: int = None) -> bool:
    """
    Renderiza e envia um email HTML com versão texto puro.
    Injeta pixel de rastreamento e link de clique se TRACKING_BASE_URL estiver configurado.
    """
    from mailer.templates import render_template

    pixel_url = f"{TRACKING_BASE_URL}/t/o/{lead_id}" if (TRACKING_BASE_URL and lead_id) else ""
    click_url = f"{TRACKING_BASE_URL}/t/c/{lead_id}" if (TRACKING_BASE_URL and lead_id) else "https://topagenda.online"

    html_body = render_template(
        variant_id=template_id,
        company_name=company_name,
        tracking_pixel_url=pixel_url,
        click_url=click_url,
    )
    text_body = _html_to_text(html_body)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"Top Agenda <{EMAIL_FROM}>"
    msg["To"] = to
    msg["List-Unsubscribe"] = f"<{UNSUBSCRIBE_URL}>"
    msg["List-Unsubscribe-Post"] = "List-Unsubscribe=One-Click"
    msg.attach(MIMEText(text_body, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    msg_str = msg.as_string()

    # Escolhe provedor: Resend → Brevo → Mailjet → Hostinger
    resend_count  = _count_today("resend_sent:")
    brevo_count   = _count_today("brevo_sent:")
    mailjet_count = _count_today("mailjet_sent:")
    use_resend  = RESEND_SMTP_PASS   and resend_count  < RESEND_DAILY_LIMIT
    use_brevo   = BREVO_SMTP_USER    and brevo_count   < BREVO_DAILY_LIMIT
    use_mailjet = MAILJET_SMTP_USER  and mailjet_count < MAILJET_DAILY_LIMIT

    providers = []
    if use_resend:
        providers.append(("Resend",    _send_via_resend,    lambda: _increment_today("resend_sent:")))
    if use_brevo:
        providers.append(("Brevo",     _send_via_brevo,     lambda: _increment_today("brevo_sent:")))
    if use_mailjet:
        providers.append(("Mailjet",   _send_via_mailjet,   lambda: _increment_today("mailjet_sent:")))
    providers.append(    ("Hostinger", _send_via_hostinger, lambda: None))

    for provider_name, send_fn, inc_fn in providers:
        try:
            send_fn(msg_str, EMAIL_FROM, to)
            inc_fn()
            logger.info(f"Email sent via {provider_name} to {to} (template={template_id})")
            return True
        except Exception as e:
            logger.warning(f"{provider_name} failed for {to}: {e} — trying next provider")

    logger.error(f"All SMTP providers failed for {to}")
    return False
