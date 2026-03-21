"""Public-facing website routes — no login required."""
from datetime import date

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from collections import defaultdict

import markdown as md_lib

from app.database import get_db
from app.models.event_registration import EventRegistration, ATTENDANCE_TYPES
from app.models.member import Member
from app.models.officer import Officer
from app.models.org import OrgEvent
from app.models.program import Program
from app.models.resource import Resource
from app.models.site_content import SiteSetting, ContentBlock, PublicPage


def _settings(db: Session) -> dict:
    return {r.key: r.value or "" for r in db.query(SiteSetting).all()}


def _block(key: str, db: Session) -> str:
    b = db.get(ContentBlock, key)
    return md_lib.markdown(b.body or "", extensions=["nl2br"]) if b else ""


def _member_check(slug: str, request: Request, db: Session):
    """Return a RedirectResponse if the page is members-only and visitor is not authenticated.
    Internal officers (request.state.user) bypass the check automatically."""
    if request.state.member_site_authed or request.state.user:
        return None
    page = db.get(PublicPage, slug)
    if page and page.members_only:
        return RedirectResponse(f"/site/login?next=/site/{slug}", status_code=302)
    return None


router = APIRouter(prefix="/site", tags=["public"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/login", response_class=HTMLResponse)
def member_login_form(request: Request, next: str = "/site/"):
    if request.state.member_site_authed or request.state.user:
        return RedirectResponse(url=next, status_code=302)
    return templates.TemplateResponse("public/member_login.html", {
        "request": request, "next": next, "error": None,
    })


@router.post("/login", response_class=HTMLResponse)
def member_login_submit(
    request: Request,
    password: str = Form(""),
    next: str = Form("/site/"),
    db: Session = Depends(get_db),
):
    setting = db.get(SiteSetting, "member_site_password")
    correct = (setting.value or "").strip() if setting else ""
    if not correct:
        error = "Member login is not yet configured. Please contact the administrator."
    elif password.strip() != correct:
        error = "Incorrect password. Please try again."
    else:
        error = None

    if error:
        return templates.TemplateResponse("public/member_login.html", {
            "request": request, "next": next, "error": error,
        }, status_code=401)

    request.session["member_site_authed"] = True
    safe_next = next if next.startswith("/site") else "/site/"
    return RedirectResponse(url=safe_next, status_code=303)


@router.get("/logout")
def member_logout(request: Request):
    request.session.pop("member_site_authed", None)
    return RedirectResponse(url="/site/", status_code=302)


@router.get("/", response_class=HTMLResponse)
def public_home(request: Request, db: Session = Depends(get_db)):
    if redir := _member_check("home", request, db):
        return redir
    today = date.today()
    # Soonest upcoming event flagged for public display
    next_event = (
        db.query(OrgEvent)
        .filter(OrgEvent.show_on_public == True, OrgEvent.date >= today)
        .order_by(OrgEvent.date)
        .first()
    )
    # Up to 6 upcoming events for the teaser calendar
    upcoming_events = (
        db.query(OrgEvent)
        .filter(OrgEvent.date >= today)
        .order_by(OrgEvent.date)
        .limit(6)
        .all()
    )
    return templates.TemplateResponse("public/home.html", {
        "request": request,
        "next_event": next_event,
        "upcoming_events": upcoming_events,
    })


@router.get("/about", response_class=HTMLResponse)
def public_about(request: Request, db: Session = Depends(get_db)):
    if redir := _member_check("about", request, db):
        return redir
    s = _settings(db)
    return templates.TemplateResponse("public/about.html", {
        "request": request,
        "s": s,
        "block_who_we_are":       _block("about_who_we_are", db),
        "block_membership_intro": _block("about_membership_intro", db),
    })


@router.get("/officers", response_class=HTMLResponse)
def public_officers(request: Request, db: Session = Depends(get_db)):
    if redir := _member_check("officers", request, db):
        return redir
    all_officers = (
        db.query(Officer)
        .filter(Officer.active == True)
        .order_by(Officer.title)
        .all()
    )
    elected = [o for o in all_officers if o.category == "Elected"]
    volunteers = [o for o in all_officers if o.category == "Volunteer"]
    return templates.TemplateResponse("public/officers.html", {
        "request": request, "elected": elected, "volunteers": volunteers,
    })


@router.get("/calendar", response_class=HTMLResponse)
def public_calendar(request: Request, db: Session = Depends(get_db)):
    if redir := _member_check("calendar", request, db):
        return redir
    today = date.today()
    events = (
        db.query(OrgEvent)
        .filter(OrgEvent.date >= today)
        .order_by(OrgEvent.date)
        .all()
    )
    s = _settings(db)
    return templates.TemplateResponse("public/calendar.html", {
        "request": request, "events": events, "s": s,
    })


@router.get("/upcoming-events", response_class=HTMLResponse)
def public_upcoming_events(request: Request, db: Session = Depends(get_db)):
    if redir := _member_check("upcoming-events", request, db):
        return redir
    today = date.today()
    events = (
        db.query(OrgEvent)
        .filter(OrgEvent.show_on_public == True, OrgEvent.date >= today)
        .order_by(OrgEvent.date)
        .all()
    )
    return templates.TemplateResponse("public/upcoming_events.html", {
        "request": request, "events": events,
    })


@router.get("/skill-center", response_class=HTMLResponse)
def public_skill_center(request: Request, db: Session = Depends(get_db)):
    if redir := _member_check("skill-center", request, db):
        return redir
    return templates.TemplateResponse("public/skill_center.html", {
        "request": request,
        "block_what":   _block("skill_center_what", db),
        "block_expect": _block("skill_center_expect", db),
    })


@router.get("/events/{event_id}/register", response_class=HTMLResponse)
def register_form(event_id: int, request: Request, db: Session = Depends(get_db)):
    from app.registration_service import confirmed_count as _confirmed_count
    event = db.get(OrgEvent, event_id)
    if not event or not event.registration_enabled:
        raise HTTPException(status_code=404)
    count = _confirmed_count(event_id, db)
    spots_left = (event.capacity - count) if event.capacity else None
    return templates.TemplateResponse("public/event_register.html", {
        "request": request, "event": event,
        "spots_left": spots_left, "attendance_types": ATTENDANCE_TYPES,
        "restriction": event.registration_restriction or "",
        "errors": [], "form": {},
    })


@router.post("/events/{event_id}/register", response_class=HTMLResponse)
def submit_registration(
    event_id: int,
    request: Request,
    registrant_type:  str = Form("member"),
    member_email:     str = Form(""),
    visitor_name:     str = Form(""),
    visitor_email:    str = Form(""),
    attendance_type:  str = Form("In Person"),
    notes:            str = Form(""),
    db: Session = Depends(get_db),
):
    from app.registration_service import (
        confirmed_count as _confirmed_count,
        next_waitlist_position,
        send_confirmation_email,
        send_waitlist_email,
    )
    event = db.get(OrgEvent, event_id)
    if not event or not event.registration_enabled:
        raise HTTPException(status_code=404)

    restriction = event.registration_restriction or ""
    errors = []
    name = ""
    email = ""
    member_id = None
    form_data = {
        "registrant_type": registrant_type,
        "member_email": member_email,
        "visitor_name": visitor_name,
        "visitor_email": visitor_email,
        "attendance_type": attendance_type,
        "notes": notes,
    }

    # Enforce registration restriction before processing fields
    if restriction == "members_only" and registrant_type == "visitor":
        errors.append(
            "Registration for this event is limited to CVW members. "
            "If you are a member, please use the member path above."
        )
    elif restriction == "zoom_members_only" and registrant_type == "visitor" and attendance_type == "Remote":
        errors.append(
            "Remote (Zoom) attendance is available to CVW members only. "
            "Visitors are welcome to attend in person at the venue."
        )

    if not errors:
        if registrant_type == "member":
            me = member_email.strip().lower()
            if not me:
                errors.append("Please enter your email address.")
            else:
                member = db.query(Member).filter(Member.email.ilike(me)).first()
                if not member:
                    errors.append(
                        "That email isn't in our member records. "
                        "Please check the address or use the Visitor form."
                    )
                else:
                    name = f"{member.first_name or ''} {member.last_name or ''}".strip()
                    email = member.email
                    member_id = member.id
        else:
            if not visitor_name.strip():
                errors.append("Please enter your name.")
            if not visitor_email.strip():
                errors.append("Please enter your email address.")
            if not errors:
                name = visitor_name.strip()
                email = visitor_email.strip().lower()

    if not errors:
        # Check for duplicate registration
        existing = (
            db.query(EventRegistration)
            .filter(
                EventRegistration.org_event_id == event_id,
                EventRegistration.email == email,
                EventRegistration.status != "cancelled",
            )
            .first()
        )
        if existing:
            errors.append(
                f"There is already a registration for {email} for this event "
                f"(status: {existing.status})."
            )

    if errors:
        count = _confirmed_count(event_id, db)
        spots_left = (event.capacity - count) if event.capacity else None
        return templates.TemplateResponse("public/event_register.html", {
            "request": request, "event": event,
            "spots_left": spots_left, "attendance_types": ATTENDANCE_TYPES,
            "restriction": restriction,
            "errors": errors, "form": form_data,
        }, status_code=422)

    count = _confirmed_count(event_id, db)
    is_full = event.capacity is not None and count >= event.capacity
    status = "waitlist" if is_full else "confirmed"
    wl_pos = next_waitlist_position(event_id, db) if is_full else None

    reg = EventRegistration(
        org_event_id=event_id,
        member_id=member_id,
        name=name,
        email=email,
        attendance_type=attendance_type,
        status=status,
        waitlist_position=wl_pos,
        cancel_token=EventRegistration.new_token(),
        notes=notes.strip() or None,
    )
    db.add(reg)
    db.commit()
    db.refresh(reg)

    base_url = str(request.base_url).rstrip("/")
    if status == "confirmed":
        send_confirmation_email(reg, base_url)
    else:
        send_waitlist_email(reg, base_url)

    return templates.TemplateResponse("public/event_register_done.html", {
        "request": request, "event": event, "reg": reg,
    })


@router.get("/register/cancel/{token}", response_class=HTMLResponse)
def cancel_form(token: str, request: Request, db: Session = Depends(get_db)):
    reg = db.query(EventRegistration).filter(EventRegistration.cancel_token == token).first()
    return templates.TemplateResponse("public/event_cancel.html", {
        "request": request,
        "reg": reg,
        "event": reg.org_event if reg else None,
        "already_done": (not reg or reg.status == "cancelled"),
    })


@router.post("/register/cancel/{token}", response_class=HTMLResponse)
def confirm_cancel(token: str, request: Request, db: Session = Depends(get_db)):
    from app.registration_service import do_cancel
    reg = db.query(EventRegistration).filter(EventRegistration.cancel_token == token).first()
    event = reg.org_event if reg else None
    if reg and reg.status != "cancelled":
        base_url = str(request.base_url).rstrip("/")
        do_cancel(reg, db, base_url)
    return templates.TemplateResponse("public/event_cancel.html", {
        "request": request, "reg": reg, "event": event,
        "already_done": False, "cancelled": True,
    })


@router.get("/resources", response_class=HTMLResponse)
def public_resources(request: Request, db: Session = Depends(get_db)):
    if redir := _member_check("resources", request, db):
        return redir
    resources = (
        db.query(Resource)
        .filter(Resource.active == True)
        .order_by(Resource.category, Resource.sort_order, Resource.title)
        .all()
    )
    by_category: dict[str, list] = defaultdict(list)
    for r in resources:
        by_category[r.category].append(r)
    return templates.TemplateResponse("public/resources.html", {
        "request": request,
        "by_category": dict(sorted(by_category.items())),
    })


@router.get("/contact", response_class=HTMLResponse)
def public_contact(request: Request, db: Session = Depends(get_db)):
    if redir := _member_check("contact", request, db):
        return redir
    officers = (
        db.query(Officer)
        .filter(Officer.active == True, Officer.category == "Elected")
        .order_by(Officer.title)
        .all()
    )
    return templates.TemplateResponse("public/contact.html", {
        "request": request, "officers": officers,
    })
