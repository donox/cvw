"""Guides — role-filtered documentation for dashboard users."""
from pathlib import Path

import markdown as md
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.dependencies import get_current_user
from app.models.user import User

GUIDES_DIR = Path("docs/guides")

# Which subfolders each role may read (admin sees all)
ROLE_FOLDERS: dict[str, list[str]] = {
    "admin":      ["all", "exec", "membership", "financial", "program", "librarian", "admin"],
    "exec":       ["all", "exec"],
    "membership": ["all", "membership"],
    "financial":  ["all", "financial"],
    "program":    ["all", "program"],
    "librarian":  ["all", "librarian"],
}

FOLDER_LABELS: dict[str, str] = {
    "all":        "General",
    "exec":       "Executive",
    "membership": "Membership",
    "financial":  "Financial",
    "program":    "Programs",
    "librarian":  "Library",
    "admin":      "Administration",
}

router = APIRouter(prefix="/guides", tags=["guides"])
templates = Jinja2Templates(directory="app/templates")


def _allowed_folders(role: str) -> list[str]:
    return ROLE_FOLDERS.get(role, ["all"])


@router.get("/", response_class=HTMLResponse)
def guides_index(request: Request, user: User = Depends(get_current_user)):
    folders = _allowed_folders(user.role)
    sections = []
    for folder in folders:
        folder_path = GUIDES_DIR / folder
        if not folder_path.exists():
            continue
        docs = sorted(
            [{"name": f.stem.replace("_", " ").title(), "filename": f.name, "folder": folder}
             for f in folder_path.glob("*.md")],
            key=lambda d: d["name"]
        )
        if docs:
            sections.append({"label": FOLDER_LABELS.get(folder, folder.title()), "docs": docs})
    return templates.TemplateResponse("guides/index.html", {
        "request": request, "sections": sections,
    })


@router.get("/{folder}/{filename}", response_class=HTMLResponse)
def guide_view(folder: str, filename: str, request: Request, user: User = Depends(get_current_user)):
    if folder not in _allowed_folders(user.role):
        raise HTTPException(status_code=403)
    path = (GUIDES_DIR / folder / filename).resolve()
    if not path.exists() or path.suffix != ".md" or not path.is_relative_to(GUIDES_DIR.resolve()):
        raise HTTPException(status_code=404)
    content_html = md.markdown(path.read_text(), extensions=["tables", "toc", "fenced_code"])
    return templates.TemplateResponse("guides/view.html", {
        "request": request,
        "title": path.stem.replace("_", " ").title(),
        "content_html": content_html,
        "folder": folder,
    })
