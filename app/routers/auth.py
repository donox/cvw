from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
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
    return RedirectResponse(url=next if next.startswith("/") else "/", status_code=303)


@router.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login", status_code=303)
