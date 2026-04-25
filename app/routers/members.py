import csv
import io
from datetime import date, datetime
from typing import Optional

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response, StreamingResponse
from fastapi.templating import Jinja2Templates
from fpdf import FPDF
from sqlalchemy import asc, case, desc as desc_
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_permission
from app.models.group import MemberGroup, member_group_assoc
from app.models.member import Member

router = APIRouter(prefix="/members", tags=["members"])
templates = Jinja2Templates(directory="app/templates")

auth = Depends(require_permission("members"))

MEMBERSHIP_TYPES = ["Individual", "Family", "Secondary/Affiliate", "Life"]
SKILL_LEVELS = ["Beginner", "Intermediate", "Advanced", "Professional"]
YEARS_TURNING = ["Less than 1", "1-3", "3-5", "5-10", "10-20", "20+"]
STATUSES = ["Prospective", "Active", "Former"]


def _get_or_404(db: Session, member_id: int) -> Member:
    member = db.get(Member, member_id)
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    return member


def _form_context():
    return {
        "membership_types": MEMBERSHIP_TYPES,
        "skill_levels": SKILL_LEVELS,
        "years_turning_options": YEARS_TURNING,
        "statuses": STATUSES,
    }


def _parse_member_form(
    first_name, last_name, email, nickname, birthday, significant_other,
    address, city, state, zip_code, home_phone, work_phone, mobile_phone,
    membership_type, skill_level, years_turning, status,
    dues_paid, dues_paid_date,
    volunteer_interest, volunteer_area, how_heard,
) -> dict:
    parsed_birthday = None
    if birthday:
        try:
            parsed_birthday = date.fromisoformat(birthday)
        except ValueError:
            pass

    parsed_dues_date = None
    if dues_paid_date:
        try:
            parsed_dues_date = date.fromisoformat(dues_paid_date)
        except ValueError:
            pass

    return dict(
        first_name=first_name,
        last_name=last_name,
        nickname=nickname or None,
        email=email,
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
        status=status or "Prospective",
        dues_paid=dues_paid == "on",
        dues_paid_date=parsed_dues_date,
        volunteer_interest=True if volunteer_interest == "yes" else (False if volunteer_interest == "no" else None),
        volunteer_area=volunteer_area or None,
        how_heard=how_heard or None,
    )


SORT_COLUMNS = {
    "last_name":       (Member.last_name, Member.first_name),
    "email":           (Member.email,),
    "membership_type": (Member.membership_type, Member.last_name),
    "status":          (Member.status, Member.last_name),
}

# Years Turning values in logical order for sorting
_YEARS_ORDER = case(
    (Member.years_turning == "Less than 1", 0),
    (Member.years_turning == "1-3", 1),
    (Member.years_turning == "3-5", 2),
    (Member.years_turning == "5-10", 3),
    (Member.years_turning == "10-20", 4),
    (Member.years_turning == "20+", 5),
    else_=99,
)

QUERY_SORT_COLUMNS = {
    "last_name":       [Member.last_name, Member.first_name],
    "first_name":      [Member.first_name, Member.last_name],
    "email":           [Member.email],
    "status":          [Member.status, Member.last_name],
    "membership_type": [Member.membership_type, Member.last_name],
    "dues_paid":       [Member.dues_paid, Member.last_name],
    "skill_level":     [Member.skill_level, Member.last_name],
    "years_turning":   [_YEARS_ORDER, Member.last_name],
    "volunteer":       [Member.volunteer_interest, Member.last_name],
    "created_at":      [Member.created_at],
}


def _apply_query_filters(q, status, membership_type, dues_paid, skill_level,
                          volunteer_interest, years_turning, name_search):
    if name_search:
        q = q.filter(
            (Member.last_name.ilike(f"%{name_search}%")) |
            (Member.first_name.ilike(f"%{name_search}%"))
        )
    if status:
        q = q.filter(Member.status == status)
    if membership_type:
        q = q.filter(Member.membership_type == membership_type)
    if dues_paid == "yes":
        q = q.filter(Member.dues_paid == True)
    elif dues_paid == "no":
        q = q.filter(Member.dues_paid == False)
    if skill_level:
        q = q.filter(Member.skill_level == skill_level)
    if volunteer_interest == "yes":
        q = q.filter(Member.volunteer_interest == True)
    elif volunteer_interest == "no":
        q = q.filter(Member.volunteer_interest == False)
    if years_turning:
        q = q.filter(Member.years_turning == years_turning)
    return q


@router.get("/", response_class=HTMLResponse)
def list_members(
    request: Request,
    _=auth,
    db: Session = Depends(get_db),
    search: Optional[str] = None,
    sort: Optional[str] = None,
    dir: Optional[str] = None,
):
    sort_key = sort if sort in SORT_COLUMNS else "last_name"
    direction = "desc" if dir == "desc" else "asc"
    q = db.query(Member)
    if search:
        q = q.filter(Member.last_name.ilike(f"{search}%"))
    cols = SORT_COLUMNS[sort_key]
    if direction == "desc":
        cols = [desc_(c) for c in cols]
    members = q.order_by(*cols).all()
    return templates.TemplateResponse("members/list.html", {
        "request": request,
        "members": members,
        "search": search or "",
        "sort": sort_key,
        "dir": direction,
    })


@router.get("/query")
def member_query(
    request: Request,
    _=auth,
    db: Session = Depends(get_db),
    name_search:       Optional[str] = None,
    status:            Optional[str] = None,
    membership_type:   Optional[str] = None,
    dues_paid:         Optional[str] = None,
    skill_level:       Optional[str] = None,
    volunteer_interest: Optional[str] = None,
    years_turning:     Optional[str] = None,
    sort:              Optional[str] = None,
    dir:               Optional[str] = None,
    format:            Optional[str] = None,
):
    sort_key = sort if sort in QUERY_SORT_COLUMNS else "last_name"
    direction = "desc" if dir == "desc" else "asc"

    q = db.query(Member)
    q = _apply_query_filters(q, status, membership_type, dues_paid,
                              skill_level, volunteer_interest, years_turning, name_search)
    cols = QUERY_SORT_COLUMNS[sort_key]
    if direction == "desc":
        cols = [desc_(c) for c in cols]
    members = q.order_by(*cols).all()

    if format == "csv":
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(["Last Name", "First Name", "Email", "Type", "Status",
                         "Dues Paid", "Skill Level", "Years Turning", "Volunteer",
                         "Phone", "City"])
        for m in members:
            phone = m.mobile_phone or m.home_phone or m.work_phone or ""
            writer.writerow([
                m.last_name, m.first_name, m.email or "",
                m.membership_type or "", m.status or "",
                "Yes" if m.dues_paid else "No",
                m.skill_level or "", m.years_turning or "",
                "Yes" if m.volunteer_interest else ("No" if m.volunteer_interest is False else ""),
                phone, m.city or "",
            ])
        buf.seek(0)
        return StreamingResponse(
            iter([buf.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=members_query.csv"},
        )

    filters = {k: v for k, v in {
        "status": status, "membership_type": membership_type,
        "dues_paid": dues_paid, "skill_level": skill_level,
        "volunteer_interest": volunteer_interest, "years_turning": years_turning,
        "name_search": name_search,
    }.items() if v}

    return templates.TemplateResponse("members/query.html", {
        "request": request,
        "members": members,
        "filters": filters,
        "sort": sort_key,
        "dir": direction,
        "now": datetime.utcnow(),
        "statuses": STATUSES,
        "membership_types": MEMBERSHIP_TYPES,
        "skill_levels": SKILL_LEVELS,
        "years_turning_options": YEARS_TURNING,
        "f_name": name_search or "",
        "f_status": status or "",
        "f_membership_type": membership_type or "",
        "f_dues_paid": dues_paid or "",
        "f_skill_level": skill_level or "",
        "f_volunteer_interest": volunteer_interest or "",
        "f_years_turning": years_turning or "",
    })


@router.get("/new", response_class=HTMLResponse)
def new_member_form(request: Request, _=auth):
    return templates.TemplateResponse("members/form.html", {
        "request": request, "member": None, "errors": [], **_form_context()
    })


@router.post("/", response_class=RedirectResponse)
def create_member(
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
    status: Optional[str] = Form("Prospective"),
    dues_paid: Optional[str] = Form(None),
    dues_paid_date: Optional[str] = Form(None),
    volunteer_interest: Optional[str] = Form(None),
    volunteer_area: Optional[str] = Form(None),
    how_heard: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    errors = []
    if db.query(Member).filter(Member.email == email).first():
        errors.append(f"Email '{email}' is already registered.")
    if errors:
        fields = _parse_member_form(
            first_name, last_name, email, nickname, birthday, significant_other,
            address, city, state, zip_code, home_phone, work_phone, mobile_phone,
            membership_type, skill_level, years_turning, status,
            dues_paid, dues_paid_date, volunteer_interest, volunteer_area, how_heard,
        )
        return templates.TemplateResponse(
            "members/form.html",
            {"request": request, "member": None, "errors": errors, **fields, **_form_context()},
            status_code=422,
        )
    fields = _parse_member_form(
        first_name, last_name, email, nickname, birthday, significant_other,
        address, city, state, zip_code, home_phone, work_phone, mobile_phone,
        membership_type, skill_level, years_turning, status,
        dues_paid, dues_paid_date, volunteer_interest, volunteer_area, how_heard,
    )
    db.add(Member(**fields))
    db.commit()
    return RedirectResponse(url="/members/", status_code=303)


@router.get("/{member_id}", response_class=HTMLResponse)
def member_detail(member_id: int, request: Request, _=auth, db: Session = Depends(get_db)):
    member = _get_or_404(db, member_id)
    activity_groups = db.query(MemberGroup).filter(MemberGroup.is_activity == True).order_by(MemberGroup.name).all()
    opted_in_ids = set()
    for ag in activity_groups:
        row = db.execute(
            member_group_assoc.select().where(
                member_group_assoc.c.group_id == ag.id,
                member_group_assoc.c.member_id == member_id,
            )
        ).first()
        if row:
            opted_in_ids.add(ag.id)
    # Only show the opt-in section if the logged-in user is viewing their own profile
    viewer = request.state.user
    is_own_profile = viewer and viewer.member_id == member_id
    return templates.TemplateResponse("members/detail.html", {
        "request": request,
        "member": member,
        "activity_groups": activity_groups,
        "opted_in_ids": opted_in_ids,
        "is_own_profile": is_own_profile,
    })


@router.get("/{member_id}/edit", response_class=HTMLResponse)
def edit_member_form(member_id: int, request: Request, _=auth, db: Session = Depends(get_db)):
    member = _get_or_404(db, member_id)
    return templates.TemplateResponse("members/form.html", {
        "request": request, "member": member, "errors": [], **_form_context()
    })


@router.post("/{member_id}/edit", response_class=RedirectResponse)
def update_member(
    member_id: int,
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
    status: Optional[str] = Form("Prospective"),
    dues_paid: Optional[str] = Form(None),
    dues_paid_date: Optional[str] = Form(None),
    volunteer_interest: Optional[str] = Form(None),
    volunteer_area: Optional[str] = Form(None),
    how_heard: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    member = _get_or_404(db, member_id)
    errors = []
    duplicate = db.query(Member).filter(Member.email == email, Member.id != member_id).first()
    if duplicate:
        errors.append(f"Email '{email}' is already registered.")
    if errors:
        return templates.TemplateResponse(
            "members/form.html",
            {"request": request, "member": member, "errors": errors, **_form_context()},
            status_code=422,
        )
    fields = _parse_member_form(
        first_name, last_name, email, nickname, birthday, significant_other,
        address, city, state, zip_code, home_phone, work_phone, mobile_phone,
        membership_type, skill_level, years_turning, status,
        dues_paid, dues_paid_date, volunteer_interest, volunteer_area, how_heard,
    )
    for key, value in fields.items():
        setattr(member, key, value)
    member.updated_at = datetime.now()
    db.commit()
    return RedirectResponse(url="/members/", status_code=303)


@router.post("/{member_id}/delete", response_class=RedirectResponse)
def delete_member(member_id: int, db: Session = Depends(get_db)):
    member = _get_or_404(db, member_id)
    db.delete(member)
    db.commit()
    return RedirectResponse(url="/members/", status_code=303)


@router.get("/pdf/current", response_class=Response)
def member_list_pdf(_=auth, db: Session = Depends(get_db)):
    members = (
        db.query(Member)
        .filter(Member.status == "Active")
        .order_by(Member.last_name, Member.first_name)
        .all()
    )

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "CVW Current Member List", ln=True, align="C")
    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 10)
    pdf.set_fill_color(220, 220, 220)
    col_widths = [45, 45, 65, 25, 20]
    headers = ["Last Name", "First Name", "Email", "Type", "Skill"]
    for w, h in zip(col_widths, headers):
        pdf.cell(w, 8, h, border=1, fill=True)
    pdf.ln()

    pdf.set_font("Helvetica", "", 9)
    for m in members:
        pdf.cell(col_widths[0], 7, m.last_name or "", border=1)
        pdf.cell(col_widths[1], 7, m.first_name or "", border=1)
        pdf.cell(col_widths[2], 7, m.email or "", border=1)
        pdf.cell(col_widths[3], 7, m.membership_type or "", border=1)
        pdf.cell(col_widths[4], 7, m.skill_level or "", border=1)
        pdf.ln()

    pdf.set_font("Helvetica", "I", 9)
    pdf.ln(4)
    pdf.cell(0, 6, f"Total active members: {len(members)}", ln=True)

    return Response(
        content=bytes(pdf.output()),
        media_type="application/pdf",
        headers={"Content-Disposition": "inline; filename=cvw-members.pdf"},
    )
