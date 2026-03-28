"""Email sending via Mailgun API (preferred) or smtplib fallback."""
import smtplib
import ssl
import urllib.parse
import urllib.request
from base64 import b64encode
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

from app.database import settings

# Variables available to every template, keyed by the token/variable name.
# Used both for rendering and for the UI help text.
TEMPLATE_VARS = {
    "first_name":      "Recipient's first name",
    "last_name":       "Recipient's last name",
    "full_name":       "First and last name combined",
    "email":           "Recipient's email address",
    "membership_type": "Individual / Family / Affiliated / Honorary / Life",
    "status":          "Active / Prospective / Former",
    "dues_paid":       "True or False — whether dues are paid for this year",
}


def _mailgun_configured() -> bool:
    return bool(settings.MAILGUN_API_KEY and settings.MAILGUN_DOMAIN)


def _smtp_configured() -> bool:
    return bool(settings.SMTP_HOST and settings.SMTP_FROM)


def _from_address() -> str:
    if _mailgun_configured() and settings.MAILGUN_FROM:
        return settings.MAILGUN_FROM
    return settings.SMTP_FROM


def _send_via_mailgun(to_addresses: list[str], subject: str, body: str) -> None:
    from_addr = settings.MAILGUN_FROM or f"info@{settings.MAILGUN_DOMAIN}"
    params = {
        "from": from_addr,
        "to": ", ".join(to_addresses),
        "subject": subject,
        "text": body,
    }
    if settings.MAILGUN_REPLY_TO:
        params["h:Reply-To"] = settings.MAILGUN_REPLY_TO
    data = urllib.parse.urlencode(params).encode()
    credentials = b64encode(f"api:{settings.MAILGUN_API_KEY}".encode()).decode()
    url = f"https://api.mailgun.net/v3/{settings.MAILGUN_DOMAIN}/messages"
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Authorization", f"Basic {credentials}")
    with urllib.request.urlopen(req, timeout=15) as resp:
        if resp.status not in (200, 201):
            raise RuntimeError(f"Mailgun API error: {resp.status}")


def send_email(to_addresses: list[str], subject: str, body: str) -> None:
    """Send a plain-text email. Uses Mailgun API if configured, else SMTP."""
    if _mailgun_configured():
        _send_via_mailgun(to_addresses, subject, body)
        return

    if not _smtp_configured():
        raise RuntimeError(
            "Email is not configured. Set MAILGUN_API_KEY/MAILGUN_DOMAIN or SMTP_HOST in .env."
        )

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.SMTP_FROM
    msg["To"] = ", ".join(to_addresses)
    if settings.MAILGUN_REPLY_TO:
        msg["Reply-To"] = settings.MAILGUN_REPLY_TO
    msg.attach(MIMEText(body, "plain"))

    context = ssl.create_default_context()
    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
        if settings.SMTP_STARTTLS:
            server.starttls(context=context)
        if settings.SMTP_USER:
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.sendmail(settings.SMTP_FROM, to_addresses, msg.as_string())


def dummy_member(send_to_email: str):
    """Return a SimpleNamespace that looks like a Member, for test sends.

    Uses clearly labelled sample values so every substitution is visible
    in the rendered output.
    """
    from types import SimpleNamespace
    return SimpleNamespace(
        first_name="Jane",
        last_name="Sample",
        email=send_to_email,
        membership_type="Individual",
        status="Active",
        dues_paid=True,
    )


def _member_context(member) -> dict:
    """Build the variable dict for a single member."""
    return {
        "first_name":      member.first_name or "",
        "last_name":       member.last_name or "",
        "full_name":       f"{member.first_name or ''} {member.last_name or ''}".strip(),
        "email":           member.email or "",
        "membership_type": member.membership_type or "",
        "status":          member.status or "",
        "dues_paid":       bool(member.dues_paid),
    }


def render_body(template_body: str, member, template_type: str = "simple") -> str:
    """Render an email body for a single member.

    template_type="simple"  — {{ variable }} literal substitution only.
    template_type="jinja2"  — full Jinja2 rendering (if/for/filters etc.).

    All recipients are members, so the context is always populated.
    Members with no email are skipped before this is called.
    Members with empty fields (e.g. no membership_type) produce empty strings.
    """
    ctx = _member_context(member)

    if template_type == "jinja2":
        try:
            from jinja2 import Environment, Undefined
            env = Environment(undefined=Undefined)
            return env.from_string(template_body).render(**ctx)
        except Exception as exc:
            # Return body with an error header so a broken template is visible
            return f"[Template error: {exc}]\n\n{template_body}"

    # Simple mode: straight string replacement, {{ variable }} only
    result = template_body
    for key, value in ctx.items():
        result = result.replace("{{ " + key + " }}", str(value))
        result = result.replace("{{" + key + "}}", str(value))   # no-space variant
    return result


def send_to_members(
    members: list,
    subject: str,
    body_template: str,
    per_member_body: bool = False,
    template_type: str = "simple",
) -> tuple[int, Optional[str]]:
    """Send email to a list of Member objects.

    All recipients must be members (no arbitrary addresses).
    Members without an email address are silently skipped.

    Returns (sent_count, error_detail_or_None).
    """
    if not _mailgun_configured() and not _smtp_configured():
        return 0, "Email not configured"

    errors = []
    sent = 0
    for member in members:
        if not member.email:
            continue
        body = (render_body(body_template, member, template_type)
                if per_member_body else body_template)
        try:
            send_email([member.email], subject, body)
            sent += 1
        except Exception as exc:
            errors.append(f"{member.email}: {exc}")

    return sent, "; ".join(errors) if errors else None
