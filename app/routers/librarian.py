"""Librarian console — manage the public resources library."""
from collections import defaultdict

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_permission
from app.models.resource import Resource

router = APIRouter(prefix="/librarian", tags=["librarian"])
templates = Jinja2Templates(directory="app/templates")

auth = Depends(require_permission("librarian"))


def _grouped(db: Session) -> dict:
    """Return active + inactive resources grouped by category, sorted."""
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
    """Distinct existing categories for the datalist autocomplete."""
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
def create_resource(
    request: Request,
    category:    str = Form(...),
    title:       str = Form(...),
    url:         str = Form(...),
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
    if not url.strip():
        errors.append("URL is required.")
    if errors:
        return templates.TemplateResponse("librarian/resource_form.html", {
            "request": request, "res": None, "errors": errors,
            "categories": _category_list(db),
            "category": category, "title": title, "url": url,
            "description": description, "sort_order": sort_order,
        }, status_code=422)

    db.add(Resource(
        category=category.strip(),
        title=title.strip(),
        url=url.strip(),
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
def update_resource(
    res_id:      int,
    category:    str = Form(...),
    title:       str = Form(...),
    url:         str = Form(...),
    description: str = Form(""),
    sort_order:  str = Form("0"),
    active:      str = Form(""),
    _=auth,
    db: Session = Depends(get_db),
):
    res = db.get(Resource, res_id)
    if not res:
        raise HTTPException(status_code=404)
    res.category    = category.strip()
    res.title       = title.strip()
    res.url         = url.strip()
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
