import os
import signal
import subprocess
from pathlib import Path
from typing import Optional

import markdown as md
from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

import markdown as md_lib

from app.database import get_db
from app.dependencies import require_permission
from app.models.member import Member
from app.models.site_content import SiteSetting, ContentBlock, PublicPage
from app.models.user import User, ROLES


def _get_settings(db: Session) -> dict:
    return {r.key: r.value or "" for r in db.query(SiteSetting).all()}


def _render_block(key: str, db: Session) -> str:
    block = db.get(ContentBlock, key)
    return md_lib.markdown(block.body or "", extensions=["nl2br"]) if block else ""

DOCS_DIR = Path(__file__).resolve().parent.parent.parent / "docs"

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


@router.get("/docs", response_class=HTMLResponse)
def docs_index(request: Request, _=auth):
    docs = sorted(
        [{"name": f.stem, "filename": f.name}
         for f in DOCS_DIR.glob("*.md")],
        key=lambda d: d["name"]
    )
    return templates.TemplateResponse("admin/docs.html", {
        "request": request, "docs": docs
    })


@router.get("/docs/{filename}", response_class=HTMLResponse)
def view_doc(filename: str, request: Request, _=auth):
    path = (DOCS_DIR / filename).resolve()
    if not path.exists() or path.suffix != ".md" or not path.is_relative_to(DOCS_DIR):
        raise HTTPException(status_code=404)
    content_html = md.markdown(
        path.read_text(),
        extensions=["tables", "toc", "fenced_code"]
    )
    return templates.TemplateResponse("admin/doc_view.html", {
        "request": request,
        "title": path.stem.replace("_", " ").title(),
        "content_html": content_html,
        "filename": filename,
    })


@router.get("/users", response_class=HTMLResponse)
def user_list(request: Request, _=auth, db: Session = Depends(get_db)):
    users = db.query(User).order_by(User.role, User.username).all()
    return templates.TemplateResponse("admin/users.html", {
        "request": request, "users": users
    })


@router.get("/users/new", response_class=HTMLResponse)
def new_user_form(request: Request, _=auth, db: Session = Depends(get_db)):
    members = db.query(Member).order_by(Member.last_name, Member.first_name).all()
    return templates.TemplateResponse("admin/user_form.html", {
        "request": request, "user": None, "roles": ROLES, "errors": [], "members": members
    })


@router.post("/users", response_class=RedirectResponse)
def create_user(
    request: Request,
    username: str = Form(...),
    member_id: str = Form(""),
    full_name: str = Form(""),
    role: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    must_change_password: Optional[str] = Form(None),
    _=auth,
    db: Session = Depends(get_db),
):
    errors = []
    mid = int(member_id) if member_id else None
    member = db.get(Member, mid) if mid else None

    resolved_name = (f"{member.first_name} {member.last_name}".strip()
                     if member else full_name.strip())
    if not resolved_name:
        errors.append("Either select a member or enter a full name.")
    if password != confirm_password:
        errors.append("Passwords do not match.")
    if len(password) < 8:
        errors.append("Password must be at least 8 characters.")
    if db.query(User).filter(User.username == username.strip().lower()).first():
        errors.append(f"Username '{username}' is already taken.")
    if role not in ROLES:
        errors.append("Invalid role.")
    if errors:
        members = db.query(Member).order_by(Member.last_name, Member.first_name).all()
        return templates.TemplateResponse("admin/user_form.html", {
            "request": request, "user": None, "roles": ROLES, "errors": errors,
            "members": members, "username": username, "full_name": full_name,
            "role": role, "sel_member_id": mid,
        }, status_code=422)

    user = User(
        username=username.strip().lower(),
        full_name=resolved_name,
        role=role,
        hashed_password=User.hash_password(password),
        active=True,
        member_id=mid,
        must_change_password=must_change_password == "on",
    )
    db.add(user)
    db.commit()
    return RedirectResponse(url="/admin/users", status_code=303)


@router.get("/users/{user_id}/edit", response_class=HTMLResponse)
def edit_user_form(user_id: int, request: Request, _=auth, db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404)
    members = db.query(Member).order_by(Member.last_name, Member.first_name).all()
    return templates.TemplateResponse("admin/user_form.html", {
        "request": request, "user": user, "roles": ROLES, "errors": [], "members": members
    })


@router.post("/users/{user_id}/edit", response_class=RedirectResponse)
def update_user(
    user_id: int,
    request: Request,
    username: str = Form(...),
    member_id: str = Form(""),
    full_name: str = Form(""),
    role: str = Form(...),
    password: Optional[str] = Form(None),
    confirm_password: Optional[str] = Form(None),
    active: Optional[str] = Form(None),
    must_change_password: Optional[str] = Form(None),
    _=auth,
    db: Session = Depends(get_db),
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404)

    mid = int(member_id) if member_id else None
    member = db.get(Member, mid) if mid else None
    resolved_name = (f"{member.first_name} {member.last_name}".strip()
                     if member else full_name.strip() or user.full_name)

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
        members = db.query(Member).order_by(Member.last_name, Member.first_name).all()
        return templates.TemplateResponse("admin/user_form.html", {
            "request": request, "user": user, "roles": ROLES, "errors": errors,
            "members": members,
        }, status_code=422)

    user.username = username.strip().lower()
    user.full_name = resolved_name
    user.role = role
    user.active = active == "on"
    user.member_id = mid
    user.must_change_password = must_change_password == "on"
    if password:
        user.hashed_password = User.hash_password(password)
    db.commit()
    return RedirectResponse(url="/admin/users", status_code=303)


# ── System ────────────────────────────────────────────────────────────────────

@router.get("/system", response_class=HTMLResponse)
def system_index(request: Request, _=auth):
    from app.backup_service import restore_pending_exists
    return templates.TemplateResponse("admin/system.html", {
        "request": request,
        "restore_pending": restore_pending_exists(),
        "action": None, "output": None,
    })


@router.post("/system/deploy", response_class=HTMLResponse)
def system_deploy(request: Request, _=auth):
    result = subprocess.run(
        ["git", "pull"],
        capture_output=True, text=True, cwd="/app"
    )
    output = result.stdout + result.stderr
    from app.backup_service import restore_pending_exists
    return templates.TemplateResponse("admin/system.html", {
        "request": request,
        "restore_pending": restore_pending_exists(),
        "action": "deploy", "output": output.strip(),
    })


@router.post("/system/restart", response_class=HTMLResponse)
def system_restart(request: Request, _=auth):
    import threading
    from app.backup_service import restore_pending_exists
    def _kill():
        import time
        time.sleep(2)
        os.kill(os.getpid(), signal.SIGTERM)
    threading.Thread(target=_kill, daemon=True).start()
    return templates.TemplateResponse("admin/system.html", {
        "request": request,
        "restore_pending": restore_pending_exists(),
        "action": "restart", "output": "Server is restarting…",
    })


# ── Site Content ──────────────────────────────────────────────────────────────

@router.get("/content/settings", response_class=HTMLResponse)
def content_settings(request: Request, _=auth, db: Session = Depends(get_db)):
    settings = db.query(SiteSetting).order_by(SiteSetting.key).all()
    return templates.TemplateResponse("admin/content_settings.html", {
        "request": request, "settings": settings,
    })


@router.post("/content/settings", response_class=RedirectResponse)
async def save_settings(request: Request, _=auth, db: Session = Depends(get_db)):
    form = await request.form()
    for setting in db.query(SiteSetting).all():
        new_val = form.get(f"setting_{setting.key}", "").strip()
        setting.value = new_val
    db.commit()
    return RedirectResponse(url="/admin/content/settings?saved=1", status_code=303)


@router.get("/content/blocks", response_class=HTMLResponse)
def content_blocks(request: Request, _=auth, db: Session = Depends(get_db)):
    blocks = db.query(ContentBlock).order_by(ContentBlock.key).all()
    return templates.TemplateResponse("admin/content_blocks.html", {
        "request": request, "blocks": blocks,
    })


@router.get("/content/blocks/{key}/edit", response_class=HTMLResponse)
def edit_block_form(key: str, request: Request, _=auth, db: Session = Depends(get_db)):
    block = db.get(ContentBlock, key)
    if not block:
        raise HTTPException(status_code=404)
    preview = md_lib.markdown(block.body or "", extensions=["nl2br"])
    return templates.TemplateResponse("admin/content_block_edit.html", {
        "request": request, "block": block, "preview": preview,
    })


@router.post("/content/blocks/{key}/edit", response_class=RedirectResponse)
def save_block(
    key: str,
    body: str = Form(""),
    _=auth,
    db: Session = Depends(get_db),
):
    block = db.get(ContentBlock, key)
    if not block:
        raise HTTPException(status_code=404)
    block.body = body
    db.commit()
    return RedirectResponse(url="/admin/content/blocks", status_code=303)


# ── Member Access Control ─────────────────────────────────────────────────────

@router.get("/content/access", response_class=HTMLResponse)
def content_access(request: Request, _=auth, db: Session = Depends(get_db)):
    pages = db.query(PublicPage).order_by(PublicPage.label).all()
    pwd_setting = db.get(SiteSetting, "member_site_password")
    return templates.TemplateResponse("admin/content_access.html", {
        "request": request,
        "pages": pages,
        "member_password": pwd_setting.value if pwd_setting else "",
    })


@router.post("/content/access", response_class=RedirectResponse)
async def save_access(request: Request, _=auth, db: Session = Depends(get_db)):
    form = await request.form()
    for page in db.query(PublicPage).all():
        page.members_only = f"page_{page.slug}" in form
    pwd_setting = db.get(SiteSetting, "member_site_password")
    if pwd_setting is not None:
        pwd_setting.value = form.get("member_site_password", "").strip()
    db.commit()
    return RedirectResponse(url="/admin/content/access?saved=1", status_code=303)
