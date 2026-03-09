from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from fpdf import FPDF
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.member import Member
from app.schemas.member import MemberCreate, MemberUpdate

router = APIRouter(prefix="/members", tags=["members"])
templates = Jinja2Templates(directory="app/templates")


def _get_or_404(db: Session, member_id: int) -> Member:
    member = db.get(Member, member_id)
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    return member


@router.get("/", response_class=HTMLResponse)
def list_members(request: Request, db: Session = Depends(get_db)):
    members = db.query(Member).order_by(Member.last_name, Member.first_name).all()
    return templates.TemplateResponse("members/list.html", {"request": request, "members": members})


@router.get("/new", response_class=HTMLResponse)
def new_member_form(request: Request):
    return templates.TemplateResponse("members/form.html", {"request": request, "member": None, "errors": []})


@router.post("/", response_class=RedirectResponse)
def create_member(
    request: Request,
    first_name: str = Form(...),
    last_name: str = Form(...),
    email: str = Form(...),
    db: Session = Depends(get_db),
):
    errors = []
    if db.query(Member).filter(Member.email == email).first():
        errors.append(f"Email '{email}' is already registered.")
    if errors:
        return templates.TemplateResponse(
            "members/form.html",
            {"request": request, "member": None, "errors": errors,
             "first_name": first_name, "last_name": last_name, "email": email},
            status_code=422,
        )
    member = Member(first_name=first_name, last_name=last_name, email=email)
    db.add(member)
    db.commit()
    return RedirectResponse(url="/members/", status_code=303)


@router.get("/{member_id}", response_class=HTMLResponse)
def member_detail(member_id: int, request: Request, db: Session = Depends(get_db)):
    member = _get_or_404(db, member_id)
    return templates.TemplateResponse("members/detail.html", {"request": request, "member": member})


@router.get("/{member_id}/edit", response_class=HTMLResponse)
def edit_member_form(member_id: int, request: Request, db: Session = Depends(get_db)):
    member = _get_or_404(db, member_id)
    return templates.TemplateResponse("members/form.html", {"request": request, "member": member, "errors": []})


@router.post("/{member_id}/edit", response_class=RedirectResponse)
def update_member(
    member_id: int,
    request: Request,
    first_name: str = Form(...),
    last_name: str = Form(...),
    email: str = Form(...),
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
            {"request": request, "member": member, "errors": errors,
             "first_name": first_name, "last_name": last_name, "email": email},
            status_code=422,
        )
    member.first_name = first_name
    member.last_name = last_name
    member.email = email
    db.commit()
    return RedirectResponse(url="/members/", status_code=303)


@router.post("/{member_id}/delete", response_class=RedirectResponse)
def delete_member(member_id: int, db: Session = Depends(get_db)):
    member = _get_or_404(db, member_id)
    db.delete(member)
    db.commit()
    return RedirectResponse(url="/members/", status_code=303)


@router.get("/pdf/current", response_class=Response)
def member_list_pdf(db: Session = Depends(get_db)):
    members = db.query(Member).order_by(Member.last_name, Member.first_name).all()

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "CVW Current Member List", ln=True, align="C")
    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 11)
    pdf.set_fill_color(220, 220, 220)
    pdf.cell(60, 8, "Last Name", border=1, fill=True)
    pdf.cell(60, 8, "First Name", border=1, fill=True)
    pdf.cell(70, 8, "Email", border=1, fill=True, ln=True)

    pdf.set_font("Helvetica", "", 10)
    for m in members:
        pdf.cell(60, 7, m.last_name, border=1)
        pdf.cell(60, 7, m.first_name, border=1)
        pdf.cell(70, 7, m.email, border=1, ln=True)

    pdf.set_font("Helvetica", "I", 9)
    pdf.ln(4)
    pdf.cell(0, 6, f"Total members: {len(members)}", ln=True)

    return Response(
        content=bytes(pdf.output()),
        media_type="application/pdf",
        headers={"Content-Disposition": "inline; filename=cvw-members.pdf"},
    )
