from typing import Optional

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_permission
from app.models.user import User, ROLES

router = APIRouter(prefix="/admin", tags=["admin"])
templates = Jinja2Templates(directory="app/templates")

auth = Depends(require_permission("admin"))


@router.get("/", response_class=HTMLResponse)
def admin_index(request: Request, _=auth, db: Session = Depends(get_db)):
    user_count = db.query(User).count()
    active_count = db.query(User).filter(User.active == True).count()
    return templates.TemplateResponse("admin/index.html", {
        "request": request, "user_count": user_count, "active_count": active_count
    })


@router.get("/users", response_class=HTMLResponse)
def user_list(request: Request, _=auth, db: Session = Depends(get_db)):
    users = db.query(User).order_by(User.role, User.username).all()
    return templates.TemplateResponse("admin/users.html", {
        "request": request, "users": users
    })


@router.get("/users/new", response_class=HTMLResponse)
def new_user_form(request: Request, _=auth):
    return templates.TemplateResponse("admin/user_form.html", {
        "request": request, "user": None, "roles": ROLES, "errors": []
    })


@router.post("/users", response_class=RedirectResponse)
def create_user(
    request: Request,
    username: str = Form(...),
    full_name: str = Form(...),
    role: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    _=auth,
    db: Session = Depends(get_db),
):
    errors = []
    if password != confirm_password:
        errors.append("Passwords do not match.")
    if len(password) < 8:
        errors.append("Password must be at least 8 characters.")
    if db.query(User).filter(User.username == username.strip().lower()).first():
        errors.append(f"Username '{username}' is already taken.")
    if role not in ROLES:
        errors.append("Invalid role.")
    if errors:
        return templates.TemplateResponse("admin/user_form.html", {
            "request": request, "user": None, "roles": ROLES, "errors": errors,
            "username": username, "full_name": full_name, "role": role,
        }, status_code=422)

    user = User(
        username=username.strip().lower(),
        full_name=full_name.strip(),
        role=role,
        hashed_password=User.hash_password(password),
        active=True,
    )
    db.add(user)
    db.commit()
    return RedirectResponse(url="/admin/users", status_code=303)


@router.get("/users/{user_id}/edit", response_class=HTMLResponse)
def edit_user_form(user_id: int, request: Request, _=auth, db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404)
    return templates.TemplateResponse("admin/user_form.html", {
        "request": request, "user": user, "roles": ROLES, "errors": []
    })


@router.post("/users/{user_id}/edit", response_class=RedirectResponse)
def update_user(
    user_id: int,
    request: Request,
    username: str = Form(...),
    full_name: str = Form(...),
    role: str = Form(...),
    password: Optional[str] = Form(None),
    confirm_password: Optional[str] = Form(None),
    active: Optional[str] = Form(None),
    _=auth,
    db: Session = Depends(get_db),
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404)

    errors = []
    duplicate = db.query(User).filter(
        User.username == username.strip().lower(), User.id != user_id
    ).first()
    if duplicate:
        errors.append(f"Username '{username}' is already taken.")
    if password:
        if password != confirm_password:
            errors.append("Passwords do not match.")
        elif len(password) < 8:
            errors.append("Password must be at least 8 characters.")
    if errors:
        return templates.TemplateResponse("admin/user_form.html", {
            "request": request, "user": user, "roles": ROLES, "errors": errors,
        }, status_code=422)

    user.username = username.strip().lower()
    user.full_name = full_name.strip()
    user.role = role
    user.active = active == "on"
    if password:
        user.hashed_password = User.hash_password(password)
    db.commit()
    return RedirectResponse(url="/admin/users", status_code=303)
