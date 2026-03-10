import re
import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from config.settings import SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, EMAIL_FROM, TRACKING_BASE_URL

logger = logging.getLogger(__name__)

UNSUBSCRIBE_URL = "https://topagenda.online/unsubscribe"


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

    try:
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as server:
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(EMAIL_FROM, [to], msg.as_string())
        logger.info(f"Email sent to {to} (template={template_id})")
        return True
    except Exception as e:
        logger.error(f"Failed to send email to {to}: {e}")
        return False
