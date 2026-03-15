"""Public-facing website routes — no login required."""
from datetime import date

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.officer import Officer
from app.models.org import OrgEvent
from app.models.program import Program

router = APIRouter(prefix="/site", tags=["public"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
def public_home(request: Request, db: Session = Depends(get_db)):
    today = date.today()
    # Soonest upcoming program flagged for public display
    next_program = (
        db.query(Program)
        .filter(Program.show_on_public == True, Program.date >= today)
        .order_by(Program.date)
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
        "next_program": next_program,
        "upcoming_events": upcoming_events,
    })


@router.get("/about", response_class=HTMLResponse)
def public_about(request: Request):
    return templates.TemplateResponse("public/about.html", {"request": request})


@router.get("/officers", response_class=HTMLResponse)
def public_officers(request: Request, db: Session = Depends(get_db)):
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
    today = date.today()
    events = (
        db.query(OrgEvent)
        .filter(OrgEvent.date >= today)
        .order_by(OrgEvent.date)
        .all()
    )
    return templates.TemplateResponse("public/calendar.html", {
        "request": request, "events": events,
    })


@router.get("/next-meeting", response_class=HTMLResponse)
def public_next_meeting(request: Request, db: Session = Depends(get_db)):
    today = date.today()
    # All upcoming programs marked for public display, ordered by date
    programs = (
        db.query(Program)
        .filter(Program.show_on_public == True, Program.date >= today)
        .order_by(Program.date)
        .all()
    )
    return templates.TemplateResponse("public/next_meeting.html", {
        "request": request, "programs": programs,
    })


@router.get("/skill-center", response_class=HTMLResponse)
def public_skill_center(request: Request):
    return templates.TemplateResponse("public/skill_center.html", {"request": request})


@router.get("/contact", response_class=HTMLResponse)
def public_contact(request: Request, db: Session = Depends(get_db)):
    officers = (
        db.query(Officer)
        .filter(Officer.active == True)
        .order_by(Officer.title)
        .all()
    )
    return templates.TemplateResponse("public/contact.html", {
        "request": request, "officers": officers,
    })
