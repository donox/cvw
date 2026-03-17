"""Admin routes for backup management."""
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.backup_service import (
    create_backup, delete_backup, list_backups, prune_backups,
    restore_pending_exists, stage_restore,
)
from app.database import get_db
from app.dependencies import require_permission
from app.models.site_content import SiteSetting

router = APIRouter(prefix="/admin/backup", tags=["admin"])
templates = Jinja2Templates(directory="app/templates")
auth = Depends(require_permission("admin"))


def _keep_count(db: Session) -> int:
    s = db.get(SiteSetting, "backup_keep_count")
    try:
        return int(s.value) if s and s.value else 30
    except ValueError:
        return 30


@router.get("/", response_class=HTMLResponse)
def backup_index(request: Request, _=auth, db: Session = Depends(get_db)):
    from app.scheduler import scheduler
    backups = list_backups()
    job = scheduler.get_job("cvw_daily_backup")
    next_run = job.next_run_time if job else None
    return templates.TemplateResponse("admin/backup.html", {
        "request": request,
        "backups": backups,
        "keep_count": _keep_count(db),
        "next_run": next_run,
        "restore_pending": restore_pending_exists(),
        "saved": request.query_params.get("saved"),
    })


@router.post("/create", response_class=RedirectResponse)
def manual_backup(_=auth, db: Session = Depends(get_db)):
    info = create_backup(label="manual")
    prune_backups(_keep_count(db))
    return RedirectResponse(url="/admin/backup/?saved=backup", status_code=303)


@router.post("/settings", response_class=RedirectResponse)
async def save_backup_settings(request: Request, _=auth, db: Session = Depends(get_db)):
    form = await request.form()
    raw = form.get("backup_keep_count", "30").strip()
    keep = max(1, min(365, int(raw))) if raw.isdigit() else 30
    setting = db.get(SiteSetting, "backup_keep_count")
    if setting:
        setting.value = str(keep)
    db.commit()
    prune_backups(keep)
    return RedirectResponse(url="/admin/backup/?saved=settings", status_code=303)


@router.get("/{filename}/download")
def download_backup(filename: str, _=auth):
    from app.backup_service import _backup_dir
    path = _backup_dir() / filename
    if not path.exists() or path.suffix != ".db":
        raise HTTPException(status_code=404)
    if path.parent.resolve() != _backup_dir().resolve():
        raise HTTPException(status_code=400)
    return FileResponse(
        path=str(path),
        filename=filename,
        media_type="application/octet-stream",
    )


@router.post("/{filename}/restore", response_class=RedirectResponse)
def stage_restore_route(filename: str, _=auth):
    if not stage_restore(filename):
        raise HTTPException(status_code=404)
    return RedirectResponse(url="/admin/backup/?saved=restore", status_code=303)


@router.post("/{filename}/delete", response_class=RedirectResponse)
def delete_backup_route(filename: str, _=auth):
    delete_backup(filename)
    return RedirectResponse(url="/admin/backup/", status_code=303)
