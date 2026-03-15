from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User

router = APIRouter(tags=["auth"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/login", response_class=HTMLResponse)
def login_form(request: Request, next: str = "/"):
    if request.state.user:
        return RedirectResponse(url="/", status_code=302)
    return templates.TemplateResponse("auth/login.html", {
        "request": request, "next": next, "error": None
    })


@router.post("/login", response_class=HTMLResponse)
def login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    next: str = Form("/"),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.username == username.strip().lower()).first()
    if not user or not user.active or not user.verify_password(password):
        return templates.TemplateResponse("auth/login.html", {
            "request": request, "next": next,
            "error": "Invalid username or password.",
        }, status_code=401)

    request.session["user_id"] = user.id
    if user.must_change_password:
        return RedirectResponse(url="/change-password", status_code=303)
    return RedirectResponse(url=next if next.startswith("/") else "/", status_code=303)


@router.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login", status_code=303)


@router.get("/change-password", response_class=HTMLResponse)
def change_password_form(request: Request, user: User = Depends(get_current_user)):
    return templates.TemplateResponse("auth/change_password.html", {
        "request": request, "errors": [], "forced": user.must_change_password
    })


@router.post("/change-password", response_class=HTMLResponse)
def change_password_submit(
    request: Request,
    current_password: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    errors = []
    if not user.verify_password(current_password):
        errors.append("Current password is incorrect.")
    if password != confirm_password:
        errors.append("New passwords do not match.")
    if len(password) < 8:
        errors.append("Password must be at least 8 characters.")
    if errors:
        return templates.TemplateResponse("auth/change_password.html", {
            "request": request, "errors": errors, "forced": user.must_change_password
        }, status_code=422)

    user.hashed_password = User.hash_password(password)
    user.must_change_password = False
    db.commit()
    return RedirectResponse(url="/dashboard", status_code=303)
