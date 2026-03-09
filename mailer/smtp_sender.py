import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from config.settings import SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, EMAIL_FROM, TRACKING_BASE_URL

logger = logging.getLogger(__name__)


def send_email(to: str, subject: str, company_name: str = "",
               template_id: int = 1, lead_id: int = None) -> bool:
    """
    Renderiza e envia um email HTML.
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

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"Top Agenda <{EMAIL_FROM}>"
    msg["To"] = to
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
