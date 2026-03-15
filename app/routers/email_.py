"""Email console router.  Named email_ to avoid shadowing stdlib email package."""
from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_permission
from app.models.email_models import EmailLog, EmailTemplate, ScheduledEmail
from app.models.group import MemberGroup
from app.models.member import Member

router = APIRouter(prefix="/email", tags=["email"])
templates = Jinja2Templates(directory="app/templates")

auth = Depends(require_permission("email"))


# ── Index ─────────────────────────────────────────────────────────────────────

@router.get("/", response_class=HTMLResponse)
def email_index(request: Request, _=auth, db: Session = Depends(get_db)):
    recent_logs = db.query(EmailLog).order_by(EmailLog.sent_at.desc()).limit(10).all()
    return templates.TemplateResponse("email/index.html", {
        "request": request, "recent_logs": recent_logs
    })


# ── Compose & send ────────────────────────────────────────────────────────────

@router.get("/compose", response_class=HTMLResponse)
def compose_form(request: Request, _=auth, db: Session = Depends(get_db)):
    groups = db.query(MemberGroup).order_by(MemberGroup.name).all()
    templates_list = db.query(EmailTemplate).order_by(EmailTemplate.name).all()
    return templates.TemplateResponse("email/compose.html", {
        "request": request, "groups": groups, "email_templates": templates_list,
        "errors": [], "form": {}
    })


@router.post("/compose", response_class=HTMLResponse)
def send_email_now(
    request: Request,
    subject: str = Form(...),
    body: str = Form(...),
    group_id: str = Form(""),      # empty string = all active members
    per_member: str = Form(""),    # checkbox
    _=auth,
    db: Session = Depends(get_db),
):
    from app.email_service import send_to_members
    from app.models.email_models import EmailLog

    gid = int(group_id) if group_id else None
    if gid:
        group = db.get(MemberGroup, gid)
        if not group:
            raise HTTPException(status_code=404)
        members = group.members
    else:
        members = db.query(Member).filter(Member.status == "Active").all()
        group = None

    personalize = per_member == "on"
    sent, error = send_to_members(members, subject, body, per_member_body=personalize)

    user = request.state.user
    log = EmailLog(
        subject=subject,
        recipient_count=sent,
        group_id=gid,
        sent_by=user.username if user else "",
        status="sent" if not error else ("partial" if sent else "failed"),
        error_detail=error,
    )
    db.add(log)
    db.commit()

    groups = db.query(MemberGroup).order_by(MemberGroup.name).all()
    templates_list = db.query(EmailTemplate).order_by(EmailTemplate.name).all()
    return templates.TemplateResponse("email/compose.html", {
        "request": request, "groups": groups, "email_templates": templates_list,
        "errors": [], "form": {},
        "sent_count": sent, "send_error": error,
    })


# ── Email log ─────────────────────────────────────────────────────────────────

@router.get("/log", response_class=HTMLResponse)
def email_log(request: Request, _=auth, db: Session = Depends(get_db)):
    logs = db.query(EmailLog).order_by(EmailLog.sent_at.desc()).all()
    return templates.TemplateResponse("email/log.html", {
        "request": request, "logs": logs
    })


# ── Templates ─────────────────────────────────────────────────────────────────

@router.get("/templates", response_class=HTMLResponse)
def template_list(request: Request, _=auth, db: Session = Depends(get_db)):
    tmpl_list = db.query(EmailTemplate).order_by(EmailTemplate.name).all()
    return templates.TemplateResponse("email/template_list.html", {
        "request": request, "email_templates": tmpl_list
    })


@router.get("/templates/new", response_class=HTMLResponse)
def new_template_form(request: Request, _=auth):
    return templates.TemplateResponse("email/template_form.html", {
        "request": request, "tmpl": None, "errors": []
    })


@router.post("/templates", response_class=RedirectResponse)
def create_template(
    request: Request,
    name: str = Form(...),
    subject: str = Form(...),
    body: str = Form(...),
    _=auth,
    db: Session = Depends(get_db),
):
    errors = []
    if db.query(EmailTemplate).filter(EmailTemplate.name == name.strip()).first():
        errors.append(f"A template named '{name}' already exists.")
    if errors:
        return templates.TemplateResponse("email/template_form.html", {
            "request": request, "tmpl": None, "errors": errors,
            "name": name, "subject": subject, "body": body,
        }, status_code=422)

    user = request.state.user
    tmpl = EmailTemplate(
        name=name.strip(), subject=subject.strip(), body=body,
        created_by=user.username if user else "",
    )
    db.add(tmpl)
    db.commit()
    return RedirectResponse(url="/email/templates", status_code=303)


@router.get("/templates/{tmpl_id}/edit", response_class=HTMLResponse)
def edit_template_form(tmpl_id: int, request: Request, _=auth, db: Session = Depends(get_db)):
    tmpl = db.get(EmailTemplate, tmpl_id)
    if not tmpl:
        raise HTTPException(status_code=404)
    return templates.TemplateResponse("email/template_form.html", {
        "request": request, "tmpl": tmpl, "errors": []
    })


@router.post("/templates/{tmpl_id}/edit", response_class=RedirectResponse)
def update_template(
    tmpl_id: int,
    name: str = Form(...),
    subject: str = Form(...),
    body: str = Form(...),
    _=auth,
    db: Session = Depends(get_db),
):
    tmpl = db.get(EmailTemplate, tmpl_id)
    if not tmpl:
        raise HTTPException(status_code=404)
    tmpl.name = name.strip()
    tmpl.subject = subject.strip()
    tmpl.body = body
    db.commit()
    return RedirectResponse(url="/email/templates", status_code=303)


@router.post("/templates/{tmpl_id}/delete", response_class=RedirectResponse)
def delete_template(tmpl_id: int, _=auth, db: Session = Depends(get_db)):
    tmpl = db.get(EmailTemplate, tmpl_id)
    if not tmpl:
        raise HTTPException(status_code=404)
    db.delete(tmpl)
    db.commit()
    return RedirectResponse(url="/email/templates", status_code=303)


# ── Scheduled emails ─────────────────────────────────────────────────────────

@router.get("/scheduled", response_class=HTMLResponse)
def scheduled_list(request: Request, _=auth, db: Session = Depends(get_db)):
    scheduled = db.query(ScheduledEmail).order_by(ScheduledEmail.name).all()
    return templates.TemplateResponse("email/scheduled_list.html", {
        "request": request, "scheduled": scheduled
    })


@router.get("/scheduled/new", response_class=HTMLResponse)
def new_scheduled_form(request: Request, _=auth, db: Session = Depends(get_db)):
    tmpl_list = db.query(EmailTemplate).order_by(EmailTemplate.name).all()
    groups = db.query(MemberGroup).order_by(MemberGroup.name).all()
    return templates.TemplateResponse("email/scheduled_form.html", {
        "request": request, "se": None, "email_templates": tmpl_list,
        "groups": groups, "errors": []
    })


@router.post("/scheduled", response_class=RedirectResponse)
def create_scheduled(
    name: str = Form(...),
    template_id: int = Form(...),
    group_id: str = Form(""),
    cron_minute: str = Form("0"),
    cron_hour: str = Form("8"),
    cron_day: str = Form("*"),
    cron_month: str = Form("*"),
    cron_day_of_week: str = Form("*"),
    _=auth,
    db: Session = Depends(get_db),
):
    gid = int(group_id) if group_id else None
    se = ScheduledEmail(
        name=name.strip(),
        template_id=template_id,
        group_id=gid,
        cron_minute=cron_minute.strip(),
        cron_hour=cron_hour.strip(),
        cron_day=cron_day.strip(),
        cron_month=cron_month.strip(),
        cron_day_of_week=cron_day_of_week.strip(),
        active=True,
    )
    db.add(se)
    db.commit()
    db.refresh(se)
    from app.scheduler import _upsert_job
    _upsert_job(se)
    return RedirectResponse(url="/email/scheduled", status_code=303)


@router.get("/scheduled/{se_id}/edit", response_class=HTMLResponse)
def edit_scheduled_form(se_id: int, request: Request, _=auth, db: Session = Depends(get_db)):
    se = db.get(ScheduledEmail, se_id)
    if not se:
        raise HTTPException(status_code=404)
    tmpl_list = db.query(EmailTemplate).order_by(EmailTemplate.name).all()
    groups = db.query(MemberGroup).order_by(MemberGroup.name).all()
    return templates.TemplateResponse("email/scheduled_form.html", {
        "request": request, "se": se, "email_templates": tmpl_list,
        "groups": groups, "errors": []
    })


@router.post("/scheduled/{se_id}/edit", response_class=RedirectResponse)
def update_scheduled(
    se_id: int,
    name: str = Form(...),
    template_id: int = Form(...),
    group_id: str = Form(""),
    cron_minute: str = Form("0"),
    cron_hour: str = Form("8"),
    cron_day: str = Form("*"),
    cron_month: str = Form("*"),
    cron_day_of_week: str = Form("*"),
    active: str = Form(""),
    _=auth,
    db: Session = Depends(get_db),
):
    se = db.get(ScheduledEmail, se_id)
    if not se:
        raise HTTPException(status_code=404)
    gid = int(group_id) if group_id else None
    se.name = name.strip()
    se.template_id = template_id
    se.group_id = gid
    se.cron_minute = cron_minute.strip()
    se.cron_hour = cron_hour.strip()
    se.cron_day = cron_day.strip()
    se.cron_month = cron_month.strip()
    se.cron_day_of_week = cron_day_of_week.strip()
    se.active = active == "on"
    db.commit()
    db.refresh(se)
    from app.scheduler import _upsert_job, remove_job
    if se.active:
        _upsert_job(se)
    else:
        remove_job(se_id)
    return RedirectResponse(url="/email/scheduled", status_code=303)


@router.post("/scheduled/{se_id}/delete", response_class=RedirectResponse)
def delete_scheduled(se_id: int, _=auth, db: Session = Depends(get_db)):
    se = db.get(ScheduledEmail, se_id)
    if not se:
        raise HTTPException(status_code=404)
    from app.scheduler import remove_job
    remove_job(se_id)
    db.delete(se)
    db.commit()
    return RedirectResponse(url="/email/scheduled", status_code=303)
