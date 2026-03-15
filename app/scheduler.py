"""APScheduler wrapper for CVW scheduled emails."""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore

from app.database import settings

scheduler = BackgroundScheduler(
    jobstores={"default": SQLAlchemyJobStore(url=settings.DATABASE_URL)},
    job_defaults={"coalesce": True, "max_instances": 1},
    timezone="America/New_York",
)


def _run_scheduled_email(scheduled_email_id: int) -> None:
    """Execute a ScheduledEmail by id.  Runs inside the scheduler thread."""
    from datetime import datetime, timezone
    from app.database import SessionLocal
    from app.models.email_models import ScheduledEmail, EmailLog
    from app.models.member import Member
    from app.email_service import send_to_members

    db = SessionLocal()
    try:
        se = db.get(ScheduledEmail, scheduled_email_id)
        if not se or not se.active:
            return

        template = se.template
        if se.group_id:
            members = se.group.members
        else:
            members = db.query(Member).filter(Member.status == "Active").all()

        sent, error = send_to_members(
            members, template.subject, template.body,
            per_member_body=True,
            template_type=template.template_type or "simple",
        )
        log = EmailLog(
            subject=template.subject,
            recipient_count=sent,
            group_id=se.group_id,
            template_id=se.template_id,
            sent_by="scheduler",
            status="sent" if not error else ("partial" if sent else "failed"),
            error_detail=error,
        )
        db.add(log)
        se.last_run_at = datetime.now(timezone.utc)
        db.commit()
    except Exception as exc:
        print(f"[scheduler] Error running scheduled email {scheduled_email_id}: {exc}")
    finally:
        db.close()


def _load_all_jobs() -> None:
    """Re-schedule all active ScheduledEmails from the database."""
    from app.database import SessionLocal
    from app.models.email_models import ScheduledEmail

    db = SessionLocal()
    try:
        for se in db.query(ScheduledEmail).filter(ScheduledEmail.active == True).all():
            _upsert_job(se)
    finally:
        db.close()


def _job_id(scheduled_email_id: int) -> str:
    return f"scheduled_email_{scheduled_email_id}"


def _upsert_job(se) -> None:
    """Add or replace an APScheduler cron job for the given ScheduledEmail."""
    jid = _job_id(se.id)
    scheduler.add_job(
        _run_scheduled_email,
        trigger="cron",
        id=jid,
        replace_existing=True,
        args=[se.id],
        minute=se.cron_minute,
        hour=se.cron_hour,
        day=se.cron_day,
        month=se.cron_month,
        day_of_week=se.cron_day_of_week,
    )


def remove_job(scheduled_email_id: int) -> None:
    jid = _job_id(scheduled_email_id)
    if scheduler.get_job(jid):
        scheduler.remove_job(jid)


def start_scheduler(app=None) -> None:
    scheduler.start()
    _load_all_jobs()
