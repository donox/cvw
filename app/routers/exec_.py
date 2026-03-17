from datetime import date, datetime
from typing import Optional

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_permission
from app.models.member import Member
from app.models.officer import Officer, OFFICER_TITLES, OFFICER_CATEGORIES
from app.models.org import OrgEvent, OrgTodo, EVENT_TYPES, TODO_CATEGORIES, TODO_STATUSES, TODO_PRIORITIES
from app.models.event_registration import EventRegistration, Attendance, ATTENDANCE_TYPES

router = APIRouter(prefix="/exec", tags=["exec"])
templates = Jinja2Templates(directory="app/templates")

auth = Depends(require_permission("exec"))


@router.get("/", response_class=HTMLResponse)
def exec_index(request: Request, _=auth, db: Session = Depends(get_db)):
    all_officers = db.query(Officer).filter(Officer.active == True).order_by(Officer.title).all()
    elected   = [o for o in all_officers if o.category == "Elected"]
    volunteers = [o for o in all_officers if o.category == "Volunteer"]
    today = date.today()
    upcoming = (
        db.query(OrgEvent)
        .filter(OrgEvent.date >= today)
        .order_by(OrgEvent.date)
        .limit(5)
        .all()
    )
    open_todos = (
        db.query(OrgTodo)
        .filter(OrgTodo.status != "Done")
        .order_by(OrgTodo.priority.desc(), OrgTodo.due_date)
        .limit(8)
        .all()
    )
    return templates.TemplateResponse("exec/index.html", {
        "request": request,
        "elected": elected, "volunteers": volunteers,
        "upcoming": upcoming, "open_todos": open_todos,
    })


# ── Officers ──────────────────────────────────────────────────────────────────

@router.get("/officers", response_class=HTMLResponse)
def officer_list(request: Request, _=auth, db: Session = Depends(get_db)):
    officers = db.query(Officer).order_by(Officer.active.desc(), Officer.title).all()
    return templates.TemplateResponse("exec/officers.html", {
        "request": request, "officers": officers
    })


@router.get("/officers/new", response_class=HTMLResponse)
def new_officer_form(request: Request, _=auth, db: Session = Depends(get_db)):
    members = db.query(Member).order_by(Member.last_name, Member.first_name).all()
    return templates.TemplateResponse("exec/officer_form.html", {
        "request": request, "officer": None, "members": members,
        "titles": OFFICER_TITLES, "categories": OFFICER_CATEGORIES, "errors": [],
    })


@router.post("/officers", response_class=RedirectResponse)
def create_officer(
    request: Request,
    member_id: Optional[str] = Form(None),
    title: str = Form(...),
    category: str = Form("Elected"),
    notes: Optional[str] = Form(None),
    term_start: Optional[str] = Form(None),
    term_end: Optional[str] = Form(None),
    _=auth,
    db: Session = Depends(get_db),
):
    officer = Officer(
        member_id=int(member_id) if member_id else None,
        title=title,
        category=category,
        notes=notes or None,
        term_start=date.fromisoformat(term_start) if term_start else None,
        term_end=date.fromisoformat(term_end) if term_end else None,
        active=True,
    )
    db.add(officer)
    db.commit()
    return RedirectResponse(url="/exec/officers", status_code=303)


@router.get("/officers/{officer_id}/edit", response_class=HTMLResponse)
def edit_officer_form(officer_id: int, request: Request, _=auth, db: Session = Depends(get_db)):
    officer = db.get(Officer, officer_id)
    if not officer:
        raise HTTPException(status_code=404)
    members = db.query(Member).order_by(Member.last_name, Member.first_name).all()
    return templates.TemplateResponse("exec/officer_form.html", {
        "request": request, "officer": officer, "members": members,
        "titles": OFFICER_TITLES, "categories": OFFICER_CATEGORIES, "errors": [],
    })


@router.post("/officers/{officer_id}/edit", response_class=RedirectResponse)
def update_officer(
    officer_id: int,
    member_id: Optional[str] = Form(None),
    title: str = Form(...),
    category: str = Form("Elected"),
    notes: Optional[str] = Form(None),
    term_start: Optional[str] = Form(None),
    term_end: Optional[str] = Form(None),
    active: Optional[str] = Form(None),
    _=Depends(require_permission("exec")),
    db: Session = Depends(get_db),
):
    officer = db.get(Officer, officer_id)
    if not officer:
        raise HTTPException(status_code=404)
    officer.member_id = int(member_id) if member_id else None
    officer.title = title
    officer.category = category
    officer.notes = notes or None
    officer.term_start = date.fromisoformat(term_start) if term_start else None
    officer.term_end = date.fromisoformat(term_end) if term_end else None
    officer.active = active == "on"
    db.commit()
    return RedirectResponse(url="/exec/officers", status_code=303)


# ── Schedule ──────────────────────────────────────────────────────────────────

@router.get("/schedule", response_class=HTMLResponse)
def schedule_list(request: Request, _=auth, db: Session = Depends(get_db)):
    events = db.query(OrgEvent).order_by(OrgEvent.date).all()
    today = date.today()
    return templates.TemplateResponse("exec/schedule.html", {
        "request": request, "events": events, "today": today, "event_types": EVENT_TYPES,
    })


@router.get("/schedule/new", response_class=HTMLResponse)
def new_event_form(request: Request, _=auth):
    return templates.TemplateResponse("exec/event_form.html", {
        "request": request, "event": None, "event_types": EVENT_TYPES, "errors": [],
    })


@router.post("/schedule", response_class=RedirectResponse)
def create_event(
    title: str = Form(...),
    event_type: str = Form(...),
    date_: str = Form(..., alias="date"),
    start_time: Optional[str] = Form(None),
    end_time: Optional[str] = Form(None),
    location: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    zoom_url: Optional[str] = Form(None),
    registration_enabled: Optional[str] = Form(None),
    capacity: Optional[str] = Form(None),
    registration_note: Optional[str] = Form(None),
    show_on_public: Optional[str] = Form(None),
    _=Depends(require_permission("exec")),
    db: Session = Depends(get_db),
):
    db.add(OrgEvent(
        title=title, event_type=event_type,
        date=date.fromisoformat(date_),
        start_time=start_time or None, end_time=end_time or None,
        location=location or None, description=description or None,
        zoom_url=zoom_url or None,
        registration_enabled=(registration_enabled == "on"),
        capacity=int(capacity) if capacity and capacity.strip().isdigit() else None,
        registration_note=registration_note or None,
        show_on_public=(show_on_public == "on"),
    ))
    db.commit()
    return RedirectResponse(url="/exec/schedule", status_code=303)


@router.get("/schedule/{event_id}/edit", response_class=HTMLResponse)
def edit_event_form(event_id: int, request: Request, _=auth, db: Session = Depends(get_db)):
    event = db.get(OrgEvent, event_id)
    if not event:
        raise HTTPException(status_code=404)
    return templates.TemplateResponse("exec/event_form.html", {
        "request": request, "event": event, "event_types": EVENT_TYPES, "errors": [],
    })


@router.post("/schedule/{event_id}/edit", response_class=RedirectResponse)
def update_event(
    event_id: int,
    title: str = Form(...),
    event_type: str = Form(...),
    date_: str = Form(..., alias="date"),
    start_time: Optional[str] = Form(None),
    end_time: Optional[str] = Form(None),
    location: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    zoom_url: Optional[str] = Form(None),
    registration_enabled: Optional[str] = Form(None),
    capacity: Optional[str] = Form(None),
    registration_note: Optional[str] = Form(None),
    show_on_public: Optional[str] = Form(None),
    _=Depends(require_permission("exec")),
    db: Session = Depends(get_db),
):
    event = db.get(OrgEvent, event_id)
    if not event:
        raise HTTPException(status_code=404)
    event.title = title
    event.event_type = event_type
    event.date = date.fromisoformat(date_)
    event.start_time = start_time or None
    event.end_time = end_time or None
    event.location = location or None
    event.description = description or None
    event.zoom_url = zoom_url or None
    event.registration_enabled = (registration_enabled == "on")
    event.capacity = int(capacity) if capacity and capacity.strip().isdigit() else None
    event.registration_note = registration_note or None
    event.show_on_public = (show_on_public == "on")
    db.commit()
    return RedirectResponse(url="/exec/schedule", status_code=303)


@router.post("/schedule/{event_id}/delete", response_class=RedirectResponse)
def delete_event(event_id: int, _=Depends(require_permission("exec")), db: Session = Depends(get_db)):
    event = db.get(OrgEvent, event_id)
    if event:
        db.delete(event)
        db.commit()
    return RedirectResponse(url="/exec/schedule", status_code=303)


# ── Attendance ─────────────────────────────────────────────────────────────────

@router.get("/schedule/{event_id}/attendance", response_class=HTMLResponse)
def attendance_form(event_id: int, request: Request, _=auth, db: Session = Depends(get_db)):
    event = db.get(OrgEvent, event_id)
    if not event:
        raise HTTPException(status_code=404)
    members = (
        db.query(Member)
        .filter(Member.status == "Active")
        .order_by(Member.last_name, Member.first_name)
        .all()
    )
    existing = db.query(Attendance).filter(Attendance.org_event_id == event_id).all()
    checked_ids = {a.member_id for a in existing if a.member_id}
    visitors = [a for a in existing if not a.member_id]
    return templates.TemplateResponse("exec/event_attendance.html", {
        "request": request, "event": event, "members": members,
        "checked_ids": checked_ids, "visitors": visitors,
        "attendance_types": ATTENDANCE_TYPES,
    })


@router.post("/schedule/{event_id}/attendance", response_class=RedirectResponse)
def save_attendance(
    event_id: int,
    request: Request,
    member_ids: list[int] = Form(default=[]),
    _=auth,
    db: Session = Depends(get_db),
):
    event = db.get(OrgEvent, event_id)
    if not event:
        raise HTTPException(status_code=404)
    user = request.state.user
    # Replace all member attendance records for this event
    db.query(Attendance).filter(
        Attendance.org_event_id == event_id,
        Attendance.member_id.isnot(None),
    ).delete()
    for mid in member_ids:
        db.add(Attendance(
            org_event_id=event_id,
            member_id=mid,
            recorded_by=user.username if user else None,
        ))
    db.commit()
    return RedirectResponse(url=f"/exec/schedule/{event_id}/attendance", status_code=303)


@router.post("/schedule/{event_id}/attendance/visitor/add", response_class=RedirectResponse)
def add_visitor_attendance(
    event_id: int,
    request: Request,
    visitor_name: str = Form(...),
    visitor_email: str = Form(""),
    _=auth,
    db: Session = Depends(get_db),
):
    event = db.get(OrgEvent, event_id)
    if not event:
        raise HTTPException(status_code=404)
    user = request.state.user
    db.add(Attendance(
        org_event_id=event_id,
        visitor_name=visitor_name.strip(),
        visitor_email=visitor_email.strip() or None,
        recorded_by=user.username if user else None,
    ))
    db.commit()
    return RedirectResponse(url=f"/exec/schedule/{event_id}/attendance", status_code=303)


@router.post("/schedule/{event_id}/attendance/{att_id}/delete", response_class=RedirectResponse)
def delete_attendance(event_id: int, att_id: int, _=auth, db: Session = Depends(get_db)):
    att = db.get(Attendance, att_id)
    if att and att.org_event_id == event_id:
        db.delete(att)
        db.commit()
    return RedirectResponse(url=f"/exec/schedule/{event_id}/attendance", status_code=303)


# ── Registrations (officer view) ──────────────────────────────────────────────

@router.get("/schedule/{event_id}/registrations", response_class=HTMLResponse)
def registrations_list(event_id: int, request: Request, _=auth, db: Session = Depends(get_db)):
    event = db.get(OrgEvent, event_id)
    if not event:
        raise HTTPException(status_code=404)
    confirmed = [r for r in event.registrations if r.status == "confirmed"]
    waitlist  = sorted(
        [r for r in event.registrations if r.status == "waitlist"],
        key=lambda r: r.waitlist_position or 0,
    )
    cancelled = [r for r in event.registrations if r.status == "cancelled"]
    return templates.TemplateResponse("exec/event_registrations.html", {
        "request": request, "event": event,
        "confirmed": confirmed, "waitlist": waitlist, "cancelled": cancelled,
    })


@router.post("/schedule/{event_id}/registrations/{reg_id}/cancel", response_class=RedirectResponse)
def officer_cancel_registration(
    event_id: int, reg_id: int,
    request: Request,
    _=auth,
    db: Session = Depends(get_db),
):
    from app.registration_service import do_cancel
    reg = db.get(EventRegistration, reg_id)
    if reg and reg.org_event_id == event_id and reg.status != "cancelled":
        base_url = str(request.base_url).rstrip("/")
        do_cancel(reg, db, base_url)
    return RedirectResponse(url=f"/exec/schedule/{event_id}/registrations", status_code=303)


# ── Todo ──────────────────────────────────────────────────────────────────────

@router.get("/todo", response_class=HTMLResponse)
def todo_list(
    request: Request,
    status_filter: Optional[str] = None,
    _=auth,
    db: Session = Depends(get_db),
):
    q = db.query(OrgTodo)
    if status_filter and status_filter in TODO_STATUSES:
        q = q.filter(OrgTodo.status == status_filter)
    else:
        q = q.filter(OrgTodo.status != "Done")
    todos = q.order_by(OrgTodo.priority.desc(), OrgTodo.due_date).all()
    return templates.TemplateResponse("exec/todo.html", {
        "request": request, "todos": todos,
        "status_filter": status_filter, "statuses": TODO_STATUSES,
    })


@router.get("/todo/new", response_class=HTMLResponse)
def new_todo_form(request: Request, _=auth):
    return templates.TemplateResponse("exec/todo_form.html", {
        "request": request, "todo": None, "errors": [],
        "categories": TODO_CATEGORIES, "priorities": TODO_PRIORITIES,
    })


@router.post("/todo", response_class=RedirectResponse)
def create_todo(
    title: str = Form(...),
    description: Optional[str] = Form(None),
    category: Optional[str] = Form(None),
    owner: Optional[str] = Form(None),
    priority: str = Form("Normal"),
    due_date: Optional[str] = Form(None),
    _=Depends(require_permission("exec")),
    db: Session = Depends(get_db),
):
    db.add(OrgTodo(
        title=title, description=description or None,
        category=category or None, owner=owner or None,
        priority=priority, status="Open",
        due_date=date.fromisoformat(due_date) if due_date else None,
    ))
    db.commit()
    return RedirectResponse(url="/exec/todo", status_code=303)


@router.get("/todo/{todo_id}/edit", response_class=HTMLResponse)
def edit_todo_form(todo_id: int, request: Request, _=auth, db: Session = Depends(get_db)):
    todo = db.get(OrgTodo, todo_id)
    if not todo:
        raise HTTPException(status_code=404)
    return templates.TemplateResponse("exec/todo_form.html", {
        "request": request, "todo": todo, "errors": [],
        "categories": TODO_CATEGORIES, "priorities": TODO_PRIORITIES,
        "statuses": TODO_STATUSES,
    })


@router.post("/todo/{todo_id}/edit", response_class=RedirectResponse)
def update_todo(
    todo_id: int,
    title: str = Form(...),
    description: Optional[str] = Form(None),
    category: Optional[str] = Form(None),
    owner: Optional[str] = Form(None),
    priority: str = Form("Normal"),
    status: str = Form("Open"),
    due_date: Optional[str] = Form(None),
    _=Depends(require_permission("exec")),
    db: Session = Depends(get_db),
):
    todo = db.get(OrgTodo, todo_id)
    if not todo:
        raise HTTPException(status_code=404)
    todo.title = title
    todo.description = description or None
    todo.category = category or None
    todo.owner = owner or None
    todo.priority = priority
    todo.status = status
    todo.due_date = date.fromisoformat(due_date) if due_date else None
    if status == "Done" and not todo.completed_at:
        todo.completed_at = datetime.now()
    elif status != "Done":
        todo.completed_at = None
    db.commit()
    return RedirectResponse(url="/exec/todo", status_code=303)


@router.post("/todo/{todo_id}/delete", response_class=RedirectResponse)
def delete_todo(todo_id: int, _=Depends(require_permission("exec")), db: Session = Depends(get_db)):
    todo = db.get(OrgTodo, todo_id)
    if todo:
        db.delete(todo)
        db.commit()
    return RedirectResponse(url="/exec/todo", status_code=303)
