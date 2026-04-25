import json
from typing import Optional

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_permission
from app.models.group import MemberGroup, resolve_members
from app.models.member import Member

router = APIRouter(prefix="/groups", tags=["groups"])
templates = Jinja2Templates(directory="app/templates")

view_auth = Depends(require_permission("groups"))
edit_auth = Depends(require_permission("email"))

MEMBER_STATUSES = ["Active", "Prospective", "Former"]
MEMBERSHIP_TYPES = ["Individual", "Family", "Affiliated", "Honorary", "Life", "Young Adult"]
SKILL_LEVELS = ["Beginner", "Intermediate", "Advanced", "Professional"]


@router.get("/", response_class=HTMLResponse)
def list_groups(request: Request, _=view_auth, db: Session = Depends(get_db)):
    groups = db.query(MemberGroup).order_by(MemberGroup.name).all()
    return templates.TemplateResponse("groups/list.html", {
        "request": request, "groups": groups
    })


@router.get("/new", response_class=HTMLResponse)
def new_group_form(request: Request, _=edit_auth, db: Session = Depends(get_db)):
    members = db.query(Member).filter(Member.status == "Active").order_by(
        Member.last_name, Member.first_name
    ).all()
    return templates.TemplateResponse("groups/form.html", {
        "request": request, "group": None, "members": members, "errors": [],
        "statuses": MEMBER_STATUSES, "membership_types": MEMBERSHIP_TYPES,
        "skill_levels": SKILL_LEVELS,
    })


@router.post("/", response_class=RedirectResponse)
def create_group(
    request: Request,
    name: str = Form(...),
    description: str = Form(""),
    is_dynamic: Optional[str] = Form(None),
    fc_status: str = Form(""),
    fc_membership_type: str = Form(""),
    fc_dues_paid: str = Form(""),
    fc_skill_level: str = Form(""),
    fc_volunteer_interest: str = Form(""),
    member_ids: list[int] = Form(default=[]),
    is_activity: Optional[str] = Form(None),
    slug: str = Form(""),
    meeting_day: str = Form(""),
    meeting_frequency: str = Form(""),
    google_group_url: str = Form(""),
    _=edit_auth,
    db: Session = Depends(get_db),
):
    errors = []
    if db.query(MemberGroup).filter(MemberGroup.name == name.strip()).first():
        errors.append(f"A group named '{name}' already exists.")
    slug_val = slug.strip() or None
    if slug_val and db.query(MemberGroup).filter(MemberGroup.slug == slug_val).first():
        errors.append(f"The slug '{slug_val}' is already in use.")
    if errors:
        members = db.query(Member).filter(Member.status == "Active").order_by(
            Member.last_name, Member.first_name).all()
        return templates.TemplateResponse("groups/form.html", {
            "request": request, "group": None, "members": members, "errors": errors,
            "name": name, "description": description,
            "statuses": MEMBER_STATUSES, "membership_types": MEMBERSHIP_TYPES,
            "skill_levels": SKILL_LEVELS,
        }, status_code=422)

    dynamic = is_dynamic == "on"
    activity = is_activity == "on"
    criteria = None
    if dynamic:
        criteria = json.dumps({k: v for k, v in {
            "status": fc_status, "membership_type": fc_membership_type,
            "dues_paid": fc_dues_paid, "skill_level": fc_skill_level,
            "volunteer_interest": fc_volunteer_interest,
        }.items() if v})

    user = request.state.user
    group = MemberGroup(
        name=name.strip(), description=description.strip(),
        is_dynamic=dynamic, filter_criteria=criteria,
        is_activity=activity,
        slug=slug_val,
        meeting_day=meeting_day.strip() or None,
        meeting_frequency=meeting_frequency.strip() or None,
        google_group_url=google_group_url.strip() or None,
        created_by=user.username if user else "",
    )
    if not dynamic and member_ids:
        group.members = db.query(Member).filter(Member.id.in_(member_ids)).all()
    db.add(group)
    db.commit()
    return RedirectResponse(url="/groups/", status_code=303)


@router.get("/{group_id}", response_class=HTMLResponse)
def group_detail(group_id: int, request: Request, _=view_auth, db: Session = Depends(get_db)):
    group = db.get(MemberGroup, group_id)
    if not group:
        raise HTTPException(status_code=404)
    members = resolve_members(group, db)
    return templates.TemplateResponse("groups/detail.html", {
        "request": request, "group": group, "resolved_members": members,
    })


@router.get("/{group_id}/edit", response_class=HTMLResponse)
def edit_group_form(group_id: int, request: Request, _=edit_auth, db: Session = Depends(get_db)):
    group = db.get(MemberGroup, group_id)
    if not group:
        raise HTTPException(status_code=404)
    members = db.query(Member).order_by(Member.last_name, Member.first_name).all()
    return templates.TemplateResponse("groups/form.html", {
        "request": request, "group": group, "members": members, "errors": [],
        "statuses": MEMBER_STATUSES, "membership_types": MEMBERSHIP_TYPES,
        "skill_levels": SKILL_LEVELS,
    })


@router.post("/{group_id}/edit", response_class=RedirectResponse)
def update_group(
    group_id: int,
    request: Request,
    name: str = Form(...),
    description: str = Form(""),
    is_dynamic: Optional[str] = Form(None),
    fc_status: str = Form(""),
    fc_membership_type: str = Form(""),
    fc_dues_paid: str = Form(""),
    fc_skill_level: str = Form(""),
    fc_volunteer_interest: str = Form(""),
    member_ids: list[int] = Form(default=[]),
    is_activity: Optional[str] = Form(None),
    slug: str = Form(""),
    meeting_day: str = Form(""),
    meeting_frequency: str = Form(""),
    google_group_url: str = Form(""),
    _=edit_auth,
    db: Session = Depends(get_db),
):
    group = db.get(MemberGroup, group_id)
    if not group:
        raise HTTPException(status_code=404)

    errors = []
    duplicate = db.query(MemberGroup).filter(
        MemberGroup.name == name.strip(), MemberGroup.id != group_id
    ).first()
    if duplicate:
        errors.append(f"A group named '{name}' already exists.")
    slug_val = slug.strip() or None
    if slug_val:
        slug_conflict = db.query(MemberGroup).filter(
            MemberGroup.slug == slug_val, MemberGroup.id != group_id
        ).first()
        if slug_conflict:
            errors.append(f"The slug '{slug_val}' is already in use.")
    if errors:
        members = db.query(Member).order_by(Member.last_name, Member.first_name).all()
        return templates.TemplateResponse("groups/form.html", {
            "request": request, "group": group, "members": members, "errors": errors,
            "statuses": MEMBER_STATUSES, "membership_types": MEMBERSHIP_TYPES,
            "skill_levels": SKILL_LEVELS,
        }, status_code=422)

    dynamic = is_dynamic == "on"
    activity = is_activity == "on"
    criteria = None
    if dynamic:
        criteria = json.dumps({k: v for k, v in {
            "status": fc_status, "membership_type": fc_membership_type,
            "dues_paid": fc_dues_paid, "skill_level": fc_skill_level,
            "volunteer_interest": fc_volunteer_interest,
        }.items() if v})

    group.name = name.strip()
    group.description = description.strip()
    group.is_dynamic = dynamic
    group.filter_criteria = criteria
    group.is_activity = activity
    group.slug = slug_val
    group.meeting_day = meeting_day.strip() or None
    group.meeting_frequency = meeting_frequency.strip() or None
    group.google_group_url = google_group_url.strip() or None
    if not dynamic:
        group.members = db.query(Member).filter(Member.id.in_(member_ids)).all() if member_ids else []
    db.commit()
    return RedirectResponse(url=f"/groups/{group_id}", status_code=303)


@router.post("/{group_id}/delete", response_class=RedirectResponse)
def delete_group(group_id: int, _=edit_auth, db: Session = Depends(get_db)):
    group = db.get(MemberGroup, group_id)
    if not group:
        raise HTTPException(status_code=404)
    db.delete(group)
    db.commit()
    return RedirectResponse(url="/groups/", status_code=303)
