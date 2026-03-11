from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.member import Member

router = APIRouter(tags=["apply"])
templates = Jinja2Templates(directory="app/templates")

MEMBERSHIP_TYPES = ["Individual", "Family", "Secondary/Affiliate"]
SKILL_LEVELS = ["Beginner", "Intermediate", "Advanced", "Professional"]
YEARS_TURNING = ["Less than 1", "1-3", "3-5", "5-10", "10-20", "20+"]


def _form_context():
    return {
        "membership_types": MEMBERSHIP_TYPES,
        "skill_levels": SKILL_LEVELS,
        "years_turning_options": YEARS_TURNING,
    }


@router.get("/apply", response_class=HTMLResponse)
def apply_form(request: Request):
    return templates.TemplateResponse("apply.html", {
        "request": request, "errors": [], **_form_context()
    })


@router.post("/apply", response_class=HTMLResponse)
def apply_submit(
    request: Request,
    first_name: str = Form(...),
    last_name: str = Form(...),
    email: str = Form(...),
    nickname: Optional[str] = Form(None),
    birthday: Optional[str] = Form(None),
    significant_other: Optional[str] = Form(None),
    address: Optional[str] = Form(None),
    city: Optional[str] = Form(None),
    state: Optional[str] = Form(None),
    zip_code: Optional[str] = Form(None),
    home_phone: Optional[str] = Form(None),
    work_phone: Optional[str] = Form(None),
    mobile_phone: Optional[str] = Form(None),
    membership_type: Optional[str] = Form(None),
    skill_level: Optional[str] = Form(None),
    years_turning: Optional[str] = Form(None),
    volunteer_interest: Optional[str] = Form(None),
    volunteer_area: Optional[str] = Form(None),
    how_heard: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    errors = []
    if not first_name.strip():
        errors.append("First name is required.")
    if not last_name.strip():
        errors.append("Last name is required.")
    if not email.strip():
        errors.append("Email is required.")
    elif db.query(Member).filter(Member.email == email.strip()).first():
        errors.append("An application with that email address already exists.")

    if errors:
        return templates.TemplateResponse(
            "apply.html",
            {
                "request": request, "errors": errors,
                "first_name": first_name, "last_name": last_name, "email": email,
                "nickname": nickname, "birthday": birthday, "significant_other": significant_other,
                "address": address, "city": city, "state": state, "zip_code": zip_code,
                "home_phone": home_phone, "work_phone": work_phone, "mobile_phone": mobile_phone,
                "membership_type": membership_type, "skill_level": skill_level,
                "years_turning": years_turning, "volunteer_interest": volunteer_interest,
                "volunteer_area": volunteer_area, "how_heard": how_heard,
                **_form_context(),
            },
            status_code=422,
        )

    parsed_birthday = None
    if birthday:
        try:
            parsed_birthday = date.fromisoformat(birthday)
        except ValueError:
            pass

    member = Member(
        first_name=first_name.strip(),
        last_name=last_name.strip(),
        nickname=nickname or None,
        email=email.strip(),
        birthday=parsed_birthday,
        significant_other=significant_other or None,
        address=address or None,
        city=city or None,
        state=state or None,
        zip_code=zip_code or None,
        home_phone=home_phone or None,
        work_phone=work_phone or None,
        mobile_phone=mobile_phone or None,
        membership_type=membership_type or None,
        skill_level=skill_level or None,
        years_turning=years_turning or None,
        status="Prospective",
        dues_paid=False,
        volunteer_interest=True if volunteer_interest == "yes" else (False if volunteer_interest == "no" else None),
        volunteer_area=volunteer_area or None,
        how_heard=how_heard or None,
    )
    db.add(member)
    db.commit()

    return RedirectResponse(url="/apply/thanks", status_code=303)


@router.get("/apply/thanks", response_class=HTMLResponse)
def apply_thanks(request: Request):
    return templates.TemplateResponse("apply_thanks.html", {"request": request})
