from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_permission
from app.models.group import MemberGroup
from app.models.member import Member

router = APIRouter(prefix="/groups", tags=["groups"])
templates = Jinja2Templates(directory="app/templates")

view_auth = Depends(require_permission("groups"))
edit_auth = Depends(require_permission("email"))   # membership VP + admin can edit


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
        "request": request, "group": None, "members": members, "errors": []
    })


@router.post("/", response_class=RedirectResponse)
def create_group(
    request: Request,
    name: str = Form(...),
    description: str = Form(""),
    member_ids: list[int] = Form(default=[]),
    _=edit_auth,
    db: Session = Depends(get_db),
):
    errors = []
    if db.query(MemberGroup).filter(MemberGroup.name == name.strip()).first():
        errors.append(f"A group named '{name}' already exists.")
    if errors:
        members = db.query(Member).filter(Member.status == "Active").order_by(
            Member.last_name, Member.first_name
        ).all()
        return templates.TemplateResponse("groups/form.html", {
            "request": request, "group": None, "members": members,
            "errors": errors, "name": name, "description": description,
        }, status_code=422)

    user = request.state.user
    group = MemberGroup(
        name=name.strip(),
        description=description.strip(),
        created_by=user.username if user else "",
    )
    if member_ids:
        group.members = db.query(Member).filter(Member.id.in_(member_ids)).all()
    db.add(group)
    db.commit()
    return RedirectResponse(url="/groups/", status_code=303)


@router.get("/{group_id}", response_class=HTMLResponse)
def group_detail(group_id: int, request: Request, _=view_auth, db: Session = Depends(get_db)):
    group = db.get(MemberGroup, group_id)
    if not group:
        raise HTTPException(status_code=404)
    return templates.TemplateResponse("groups/detail.html", {
        "request": request, "group": group
    })


@router.get("/{group_id}/edit", response_class=HTMLResponse)
def edit_group_form(group_id: int, request: Request, _=edit_auth, db: Session = Depends(get_db)):
    group = db.get(MemberGroup, group_id)
    if not group:
        raise HTTPException(status_code=404)
    members = db.query(Member).order_by(Member.last_name, Member.first_name).all()
    return templates.TemplateResponse("groups/form.html", {
        "request": request, "group": group, "members": members, "errors": []
    })


@router.post("/{group_id}/edit", response_class=RedirectResponse)
def update_group(
    group_id: int,
    request: Request,
    name: str = Form(...),
    description: str = Form(""),
    member_ids: list[int] = Form(default=[]),
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
    if errors:
        members = db.query(Member).order_by(Member.last_name, Member.first_name).all()
        return templates.TemplateResponse("groups/form.html", {
            "request": request, "group": group, "members": members, "errors": errors,
        }, status_code=422)

    group.name = name.strip()
    group.description = description.strip()
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
