import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from config.settings import SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, EMAIL_FROM

logger = logging.getLogger(__name__)

TEMPLATE_PATH = Path(__file__).parent.parent / "templates" / "email.html"


def _load_template() -> str:
    if TEMPLATE_PATH.exists():
        return TEMPLATE_PATH.read_text(encoding="utf-8")
    return "<p>Olá! Conheça o <strong>TopAgenda</strong>, o melhor sistema de agendamento para o seu negócio.</p>"


def send_email(to: str, subject: str, html_body: str | None = None,
               company_name: str = "") -> bool:
    """
    Send an HTML email via SMTP_SSL.
    Returns True on success, False on failure.
    """
    if html_body is None:
        template = _load_template()
        html_body = template.replace("{{company_name}}", company_name or "")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = EMAIL_FROM
    msg["To"] = to

    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as server:
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(EMAIL_FROM, [to], msg.as_string())
        logger.info(f"Email sent to {to}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email to {to}: {e}")
        return False
