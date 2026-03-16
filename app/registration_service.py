"""Business logic for event registration: waitlist management and confirmation emails."""
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.email_service import send_email
from app.models.event_registration import EventRegistration


# ── Waitlist helpers ───────────────────────────────────────────────────────────

def confirmed_count(event_id: int, db: Session) -> int:
    return (
        db.query(EventRegistration)
        .filter(
            EventRegistration.org_event_id == event_id,
            EventRegistration.status == "confirmed",
        )
        .count()
    )


def next_waitlist_position(event_id: int, db: Session) -> int:
    last = (
        db.query(EventRegistration)
        .filter(
            EventRegistration.org_event_id == event_id,
            EventRegistration.status == "waitlist",
        )
        .order_by(EventRegistration.waitlist_position.desc())
        .first()
    )
    return (last.waitlist_position or 0) + 1 if last else 1


def do_cancel(reg: EventRegistration, db: Session, base_url: str = "") -> None:
    """Cancel a registration and promote the next person off the waitlist if needed."""
    was_confirmed = reg.status == "confirmed"
    reg.status = "cancelled"
    reg.waitlist_position = None

    if was_confirmed:
        next_up = (
            db.query(EventRegistration)
            .filter(
                EventRegistration.org_event_id == reg.org_event_id,
                EventRegistration.status == "waitlist",
            )
            .order_by(EventRegistration.waitlist_position)
            .first()
        )
        if next_up:
            next_up.status = "confirmed"
            next_up.waitlist_position = None
            next_up.confirmed_at = datetime.utcnow()
            # Renumber remaining waitlist
            remaining = (
                db.query(EventRegistration)
                .filter(
                    EventRegistration.org_event_id == reg.org_event_id,
                    EventRegistration.status == "waitlist",
                    EventRegistration.id != next_up.id,
                )
                .order_by(EventRegistration.waitlist_position)
                .all()
            )
            for i, r in enumerate(remaining, 1):
                r.waitlist_position = i
            db.flush()
            _send_promotion_email(next_up, base_url)

    db.commit()


# ── Email helpers ─────────────────────────────────────────────────────────────

def _fmt_event(event) -> str:
    lines = [f"  {event.title}"]
    date_str = event.date.strftime("%A, %B %-d, %Y") if event.date else ""
    time_str = event.start_time or ""
    if event.end_time:
        time_str += f" – {event.end_time}"
    if date_str:
        lines.append(f"  {date_str}" + (f" at {time_str}" if time_str else ""))
    if event.location:
        lines.append(f"  {event.location}")
    return "\n".join(lines)


def send_confirmation_email(reg: EventRegistration, base_url: str = "") -> None:
    event = reg.org_event
    cancel_url = f"{base_url}/site/register/cancel/{reg.cancel_token}" if reg.cancel_token else ""

    zoom_line = ""
    if reg.attendance_type == "Remote" and event.zoom_url:
        zoom_line = f"\n  Zoom link: {event.zoom_url}"

    body = (
        f"Hi {reg.name},\n\n"
        f"You're confirmed for:\n{_fmt_event(event)}{zoom_line}\n\n"
        f"To cancel if your plans change:\n  {cancel_url}\n\n"
        f"See you there!\nCentral Virginia Woodturners"
    )
    try:
        send_email([reg.email], f"You're registered: {event.title}", body)
    except Exception:
        pass  # Don't let email failure block registration


def send_waitlist_email(reg: EventRegistration, base_url: str = "") -> None:
    event = reg.org_event
    cancel_url = f"{base_url}/site/register/cancel/{reg.cancel_token}" if reg.cancel_token else ""

    body = (
        f"Hi {reg.name},\n\n"
        f"This event is currently full. You've been added to the waitlist at "
        f"position #{reg.waitlist_position}.\n\n"
        f"{_fmt_event(event)}\n\n"
        f"You'll receive an email if a spot opens up.\n\n"
        f"To remove yourself from the waitlist:\n  {cancel_url}\n\n"
        f"Central Virginia Woodturners"
    )
    try:
        send_email([reg.email], f"Waitlist #{reg.waitlist_position}: {event.title}", body)
    except Exception:
        pass


def _send_promotion_email(reg: EventRegistration, base_url: str = "") -> None:
    event = reg.org_event
    cancel_url = f"{base_url}/site/register/cancel/{reg.cancel_token}" if reg.cancel_token else ""

    zoom_line = ""
    if reg.attendance_type == "Remote" and event.zoom_url:
        zoom_line = f"\n  Zoom link: {event.zoom_url}"

    body = (
        f"Hi {reg.name},\n\n"
        f"Good news — a spot opened up and you're now confirmed for:\n"
        f"{_fmt_event(event)}{zoom_line}\n\n"
        f"To cancel if your plans change:\n  {cancel_url}\n\n"
        f"See you there!\nCentral Virginia Woodturners"
    )
    try:
        send_email([reg.email], f"You're confirmed: {event.title}", body)
    except Exception:
        pass
