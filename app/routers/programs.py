import io
from datetime import date
from typing import Optional

import qrcode
from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db, settings
from app.dependencies import require_permission
from app.models.program import Program, ProgramComment

router = APIRouter(prefix="/programs", tags=["programs"])
templates = Jinja2Templates(directory="app/templates")

auth = Depends(require_permission("programs"))


def _get_or_404(db: Session, program_id: int) -> Program:
    program = db.get(Program, program_id)
    if not program:
        raise HTTPException(status_code=404, detail="Program not found")
    return program


def _summary(comments: list) -> dict:
    rated = [c for c in comments if c.rating is not None]
    relevant = [c for c in comments if c.relevance is not None]
    learned = [c for c in comments if c.learned_something is not None]
    return {
        "count": len(comments),
        "avg_rating": round(sum(c.rating for c in rated) / len(rated), 1) if rated else None,
        "avg_relevance": round(sum(c.relevance for c in relevant) / len(relevant), 1) if relevant else None,
        "pct_learned": round(sum(1 for c in learned if c.learned_something) / len(learned) * 100) if learned else None,
    }


@router.get("/", response_class=HTMLResponse)
def list_programs(request: Request, _=auth, db: Session = Depends(get_db)):
    programs = db.query(Program).order_by(Program.date.desc()).all()
    return templates.TemplateResponse("programs/list.html", {"request": request, "programs": programs})


@router.get("/new", response_class=HTMLResponse)
def new_program_form(request: Request, _=auth):
    return templates.TemplateResponse("programs/form.html", {
        "request": request, "program": None, "errors": []
    })


@router.post("/", response_class=RedirectResponse)
def create_program(
    request: Request,
    date_: str = Form(..., alias="date"),
    subject: str = Form(...),
    presenter: Optional[str] = Form(None),
    cost: Optional[str] = Form(None),
    attendee_count: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    errors = []
    try:
        parsed_date = date.fromisoformat(date_)
    except ValueError:
        errors.append("Invalid date.")
        parsed_date = None

    if not subject.strip():
        errors.append("Subject is required.")

    if errors:
        return templates.TemplateResponse(
            "programs/form.html",
            {"request": request, "program": None, "errors": errors,
             "date": date_, "subject": subject, "presenter": presenter,
             "cost": cost, "attendee_count": attendee_count, "notes": notes},
            status_code=422,
        )

    program = Program(
        date=parsed_date,
        subject=subject.strip(),
        presenter=presenter or None,
        cost=float(cost) if cost else None,
        attendee_count=int(attendee_count) if attendee_count else None,
        notes=notes or None,
    )
    db.add(program)
    db.commit()
    return RedirectResponse(url="/programs/", status_code=303)


@router.get("/{program_id}", response_class=HTMLResponse)
def program_detail(program_id: int, request: Request, _=auth, db: Session = Depends(get_db)):
    program = _get_or_404(db, program_id)
    summary = _summary(program.comments)
    return templates.TemplateResponse("programs/detail.html", {
        "request": request, "program": program, "summary": summary
    })


@router.get("/{program_id}/edit", response_class=HTMLResponse)
def edit_program_form(program_id: int, request: Request, _=auth, db: Session = Depends(get_db)):
    program = _get_or_404(db, program_id)
    return templates.TemplateResponse("programs/form.html", {
        "request": request, "program": program, "errors": []
    })


@router.post("/{program_id}/edit", response_class=RedirectResponse)
def update_program(
    program_id: int,
    request: Request,
    date_: str = Form(..., alias="date"),
    subject: str = Form(...),
    presenter: Optional[str] = Form(None),
    cost: Optional[str] = Form(None),
    attendee_count: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    program = _get_or_404(db, program_id)
    errors = []
    try:
        parsed_date = date.fromisoformat(date_)
    except ValueError:
        errors.append("Invalid date.")
        parsed_date = None

    if not subject.strip():
        errors.append("Subject is required.")

    if errors:
        return templates.TemplateResponse(
            "programs/form.html",
            {"request": request, "program": program, "errors": errors},
            status_code=422,
        )

    program.date = parsed_date
    program.subject = subject.strip()
    program.presenter = presenter or None
    program.cost = float(cost) if cost else None
    program.attendee_count = int(attendee_count) if attendee_count else None
    program.notes = notes or None
    db.commit()
    return RedirectResponse(url=f"/programs/{program_id}", status_code=303)


@router.post("/{program_id}/delete", response_class=RedirectResponse)
def delete_program(program_id: int, db: Session = Depends(get_db)):
    program = _get_or_404(db, program_id)
    db.delete(program)
    db.commit()
    return RedirectResponse(url="/programs/", status_code=303)


@router.post("/{program_id}/comments/{comment_id}/delete", response_class=RedirectResponse)
def delete_comment(program_id: int, comment_id: int, db: Session = Depends(get_db)):
    comment = db.get(ProgramComment, comment_id)
    if comment and comment.program_id == program_id:
        db.delete(comment)
        db.commit()
    return RedirectResponse(url=f"/programs/{program_id}", status_code=303)


def _feedback_url(program_id: int) -> str:
    return f"{settings.BASE_URL.rstrip('/')}/programs/{program_id}/feedback"


def _generate_qr_png(url: str) -> bytes:
    img = qrcode.make(url, error_correction=qrcode.constants.ERROR_CORRECT_M)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


@router.get("/{program_id}/qr.png")
def program_qr_png(program_id: int, _=auth, db: Session = Depends(get_db)):
    _get_or_404(db, program_id)
    png = _generate_qr_png(_feedback_url(program_id))
    return Response(content=png, media_type="image/png",
                    headers={"Cache-Control": "max-age=3600"})


@router.get("/{program_id}/qr", response_class=HTMLResponse)
def program_qr_page(program_id: int, request: Request, _=auth, db: Session = Depends(get_db)):
    program = _get_or_404(db, program_id)
    url = _feedback_url(program_id)
    return templates.TemplateResponse("programs/qr.html", {
        "request": request, "program": program, "feedback_url": url,
    })
