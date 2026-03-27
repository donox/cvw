"""Librarian console — manage the public resources library."""
import os
import re
import uuid
from collections import defaultdict

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_permission
from app.models.resource import Resource

router = APIRouter(prefix="/librarian", tags=["librarian"])
templates = Jinja2Templates(directory="app/templates")

auth = Depends(require_permission("librarian"))

UPLOAD_DIR = "app/static/resources"


def _safe_filename(original: str) -> str:
    """Return a collision-safe filename preserving the original name."""
    name, _, ext = original.rpartition(".")
    name = re.sub(r"[^\w\-]", "_", name)[:60]
    ext = re.sub(r"[^\w]", "", ext)[:10]
    return f"{name}_{uuid.uuid4().hex[:8]}.{ext}" if ext else f"{name}_{uuid.uuid4().hex[:8]}"


def _save_upload(upload: UploadFile) -> str:
    """Write upload to UPLOAD_DIR and return the stored filename."""
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    filename = _safe_filename(upload.filename)
    with open(os.path.join(UPLOAD_DIR, filename), "wb") as f:
        f.write(upload.file.read())
    return filename


def _delete_file(file_path: str | None) -> None:
    if file_path:
        full = os.path.join(UPLOAD_DIR, file_path)
        try:
            os.remove(full)
        except OSError:
            pass


def _grouped(db: Session) -> dict:
    resources = (
        db.query(Resource)
        .order_by(Resource.category, Resource.sort_order, Resource.title)
        .all()
    )
    groups: dict[str, list] = defaultdict(list)
    for r in resources:
        groups[r.category].append(r)
    return dict(sorted(groups.items()))


def _category_list(db: Session) -> list[str]:
    rows = db.query(Resource.category).distinct().order_by(Resource.category).all()
    return [r[0] for r in rows]


# ── List ──────────────────────────────────────────────────────────────────────

@router.get("/resources/", response_class=HTMLResponse)
def resource_list(request: Request, _=auth, db: Session = Depends(get_db)):
    return templates.TemplateResponse("librarian/resource_list.html", {
        "request": request,
        "by_category": _grouped(db),
    })


# ── Create ────────────────────────────────────────────────────────────────────

@router.get("/resources/new", response_class=HTMLResponse)
def new_resource_form(request: Request, _=auth, db: Session = Depends(get_db)):
    return templates.TemplateResponse("librarian/resource_form.html", {
        "request": request, "res": None, "errors": [],
        "categories": _category_list(db),
    })


@router.post("/resources/", response_class=RedirectResponse)
async def create_resource(
    request: Request,
    category:    str = Form(...),
    title:       str = Form(...),
    source_type: str = Form("url"),   # "url" or "file"
    url:         str = Form(""),
    upload:      UploadFile = File(None),
    description: str = Form(""),
    sort_order:  str = Form("0"),
    active:      str = Form(""),
    _=auth,
    db: Session = Depends(get_db),
):
    errors = []
    if not category.strip():
        errors.append("Category is required.")
    if not title.strip():
        errors.append("Title is required.")
    if source_type == "url" and not url.strip():
        errors.append("URL is required.")
    if source_type == "file" and (not upload or not upload.filename):
        errors.append("A file is required.")

    if errors:
        return templates.TemplateResponse("librarian/resource_form.html", {
            "request": request, "res": None, "errors": errors,
            "categories": _category_list(db),
            "category": category, "title": title, "url": url,
            "description": description, "sort_order": sort_order,
            "source_type": source_type,
        }, status_code=422)

    file_path = None
    if source_type == "file":
        file_path = _save_upload(upload)
        url = ""
    else:
        url = url.strip()

    db.add(Resource(
        category=category.strip(),
        title=title.strip(),
        url=url,
        file_path=file_path,
        description=description.strip() or None,
        sort_order=int(sort_order) if sort_order.strip().isdigit() else 0,
        active=(active == "on"),
    ))
    db.commit()
    return RedirectResponse(url="/librarian/resources/", status_code=303)


# ── Edit ──────────────────────────────────────────────────────────────────────

@router.get("/resources/{res_id}/edit", response_class=HTMLResponse)
def edit_resource_form(res_id: int, request: Request, _=auth, db: Session = Depends(get_db)):
    res = db.get(Resource, res_id)
    if not res:
        raise HTTPException(status_code=404)
    return templates.TemplateResponse("librarian/resource_form.html", {
        "request": request, "res": res, "errors": [],
        "categories": _category_list(db),
    })


@router.post("/resources/{res_id}/edit", response_class=RedirectResponse)
async def update_resource(
    res_id:      int,
    category:    str = Form(...),
    title:       str = Form(...),
    source_type: str = Form("url"),
    url:         str = Form(""),
    upload:      UploadFile = File(None),
    description: str = Form(""),
    sort_order:  str = Form("0"),
    active:      str = Form(""),
    _=auth,
    db: Session = Depends(get_db),
):
    res = db.get(Resource, res_id)
    if not res:
        raise HTTPException(status_code=404)

    errors = []
    if source_type == "url" and not url.strip():
        errors.append("URL is required.")
    if errors:
        return templates.TemplateResponse("librarian/resource_form.html", {
            "request": request, "res": res, "errors": errors,
            "categories": _category_list(db),
        }, status_code=422)

    if source_type == "file" and upload and upload.filename:
        # Replace existing file if there was one
        _delete_file(res.file_path)
        res.file_path = _save_upload(upload)
        res.url = None
    elif source_type == "url":
        # Switching to URL — delete any existing file
        _delete_file(res.file_path)
        res.file_path = None
        res.url = url.strip() or ""
    # else: source_type == "file" but no new file uploaded — keep existing file_path

    res.category    = category.strip()
    res.title       = title.strip()
    res.description = description.strip() or None
    res.sort_order  = int(sort_order) if sort_order.strip().isdigit() else 0
    res.active      = (active == "on")
    db.commit()
    return RedirectResponse(url="/librarian/resources/", status_code=303)


# ── Delete ────────────────────────────────────────────────────────────────────

@router.post("/resources/{res_id}/delete", response_class=RedirectResponse)
def delete_resource(res_id: int, _=auth, db: Session = Depends(get_db)):
    res = db.get(Resource, res_id)
    if not res:
        raise HTTPException(status_code=404)
    _delete_file(res.file_path)
    db.delete(res)
    db.commit()
    return RedirectResponse(url="/librarian/resources/", status_code=303)


# ── Toggle active ─────────────────────────────────────────────────────────────

@router.post("/resources/{res_id}/toggle", response_class=RedirectResponse)
def toggle_resource(res_id: int, _=auth, db: Session = Depends(get_db)):
    res = db.get(Resource, res_id)
    if not res:
        raise HTTPException(status_code=404)
    res.active = not res.active
    db.commit()
    return RedirectResponse(url="/librarian/resources/", status_code=303)
