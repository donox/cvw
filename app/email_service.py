"""Email sending via smtplib.  Requires SMTP_HOST to be configured in .env."""
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

from app.database import settings


def _smtp_configured() -> bool:
    return bool(settings.SMTP_HOST and settings.SMTP_FROM)


def send_email(to_addresses: list[str], subject: str, body: str) -> None:
    """Send a plain-text email to a list of addresses.

    Raises RuntimeError if SMTP is not configured.
    Raises smtplib exceptions on connection/auth failures.
    """
    if not _smtp_configured():
        raise RuntimeError(
            "SMTP is not configured. Set SMTP_HOST and SMTP_FROM in .env."
        )

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.SMTP_FROM
    msg["To"] = ", ".join(to_addresses)
    msg.attach(MIMEText(body, "plain"))

    context = ssl.create_default_context()
    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
        if settings.SMTP_STARTTLS:
            server.starttls(context=context)
        if settings.SMTP_USER:
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.sendmail(settings.SMTP_FROM, to_addresses, msg.as_string())


def render_body(template_body: str, member) -> str:
    """Simple {{ variable }} substitution against a Member object."""
    return (
        template_body
        .replace("{{ first_name }}", member.first_name or "")
        .replace("{{ last_name }}", member.last_name or "")
        .replace("{{ full_name }}", f"{member.first_name} {member.last_name}")
        .replace("{{ email }}", member.email or "")
    )


def send_to_members(
    members: list,
    subject: str,
    body_template: str,
    per_member_body: bool = False,
) -> tuple[int, Optional[str]]:
    """Send email to a list of Member objects.

    If per_member_body is True, renders the template for each member individually
    (personalised greeting etc.).  Otherwise sends one combined message.

    Returns (sent_count, error_detail_or_None).
    """
    if not _smtp_configured():
        return 0, "SMTP not configured"

    errors = []
    sent = 0
    for member in members:
        if not member.email:
            continue
        body = render_body(body_template, member) if per_member_body else body_template
        try:
            send_email([member.email], subject, body)
            sent += 1
        except Exception as exc:
            errors.append(f"{member.email}: {exc}")

    error_detail = "; ".join(errors) if errors else None
    return sent, error_detail
