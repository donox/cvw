from typing import Optional

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.member import Member
from app.models.program import Program, ProgramComment

router = APIRouter(tags=["feedback"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/programs/{program_id}/feedback", response_class=HTMLResponse)
def feedback_form(program_id: int, request: Request, db: Session = Depends(get_db)):
    program = db.get(Program, program_id)
    if not program:
        return HTMLResponse("Program not found.", status_code=404)
    return templates.TemplateResponse("feedback/form.html", {
        "request": request, "program": program, "errors": []
    })


@router.post("/programs/{program_id}/feedback", response_class=HTMLResponse)
def feedback_submit(
    program_id: int,
    request: Request,
    email: Optional[str] = Form(None),
    anonymous: Optional[str] = Form(None),
    rating: Optional[str] = Form(None),
    relevance: Optional[str] = Form(None),
    learned_something: Optional[str] = Form(None),
    improvements: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    program = db.get(Program, program_id)
    if not program:
        return HTMLResponse("Program not found.", status_code=404)

    errors = []
    if not rating:
        errors.append("Please provide a program rating.")
    if not relevance:
        errors.append("Please provide a relevance rating.")
    if not learned_something:
        errors.append("Please answer whether you learned something you expect to use.")

    if errors:
        return templates.TemplateResponse(
            "feedback/form.html",
            {
                "request": request, "program": program, "errors": errors,
                "email": email, "anonymous": anonymous, "rating": rating,
                "relevance": relevance, "learned_something": learned_something,
                "improvements": improvements,
            },
            status_code=422,
        )

    is_anonymous = anonymous == "on"
    member_id = None

    if not is_anonymous and email and email.strip():
        member = db.query(Member).filter(Member.email == email.strip().lower()).first()
        if member:
            member_id = member.id

    comment = ProgramComment(
        program_id=program_id,
        member_id=member_id,
        anonymous=is_anonymous,
        rating=int(rating) if rating else None,
        relevance=int(relevance) if relevance else None,
        learned_something=learned_something == "yes",
        improvements=improvements or None,
    )
    db.add(comment)
    db.commit()

    return RedirectResponse(url=f"/programs/{program_id}/feedback/thanks", status_code=303)


@router.get("/programs/{program_id}/feedback/thanks", response_class=HTMLResponse)
def feedback_thanks(program_id: int, request: Request, db: Session = Depends(get_db)):
    program = db.get(Program, program_id)
    return templates.TemplateResponse("feedback/thanks.html", {
        "request": request, "program": program
    })
