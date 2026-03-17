"""Database backup and restore utilities for CVW."""
import shutil
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List


def _db_path() -> Path:
    from app.database import settings
    raw = settings.DATABASE_URL.replace("sqlite:///", "")
    return Path(raw).resolve()


def _backup_dir() -> Path:
    d = _db_path().parent / "backups"
    d.mkdir(exist_ok=True)
    return d


# ── Public API ────────────────────────────────────────────────────────────────

@dataclass
class BackupInfo:
    filename: str
    path: Path
    size_bytes: int
    created_at: datetime

    @property
    def size_display(self) -> str:
        if self.size_bytes >= 1_048_576:
            return f"{self.size_bytes / 1_048_576:.1f} MB"
        return f"{self.size_bytes / 1024:.0f} KB"


def create_backup(label: str = "") -> BackupInfo:
    """Create a consistent timestamped backup using sqlite3.backup().
    Safe to call while the server is running.
    """
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    slug = f"_{label}" if label else ""
    dest = _backup_dir() / f"cvw_{ts}{slug}.db"

    src_conn = sqlite3.connect(str(_db_path()))
    dst_conn = sqlite3.connect(str(dest))
    try:
        src_conn.backup(dst_conn)
    finally:
        dst_conn.close()
        src_conn.close()

    return _info(dest)


def list_backups() -> List[BackupInfo]:
    """Return all backups, newest first."""
    return sorted(
        [_info(p) for p in _backup_dir().glob("cvw_*.db")],
        key=lambda b: b.created_at,
        reverse=True,
    )


def prune_backups(keep: int) -> int:
    """Delete oldest backups beyond keep count. Returns number deleted."""
    all_backups = sorted(
        _backup_dir().glob("cvw_*.db"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    to_delete = all_backups[keep:]
    for p in to_delete:
        p.unlink()
    return len(to_delete)


def stage_restore(filename: str) -> bool:
    """Copy a backup to restore_pending.db for application on next restart.
    Returns True on success, False if the file doesn't exist.
    """
    src = _backup_dir() / filename
    if not src.exists() or src.suffix != ".db":
        return False
    # Safety: only allow files inside the backup directory
    if src.parent.resolve() != _backup_dir().resolve():
        return False
    pending = _db_path().parent / "restore_pending.db"
    shutil.copy2(str(src), str(pending))
    return True


def apply_pending_restore() -> bool:
    """Apply a staged restore. Called at startup BEFORE any DB connections.
    Returns True if a restore was applied.
    """
    pending = _db_path().parent / "restore_pending.db"
    if not pending.exists():
        return False
    shutil.copy2(str(pending), str(_db_path()))
    pending.unlink()
    print("✓ Database restored from staged backup.")
    return True


def restore_pending_exists() -> bool:
    return (_db_path().parent / "restore_pending.db").exists()


def delete_backup(filename: str) -> bool:
    """Delete a single backup file. Returns True on success."""
    target = _backup_dir() / filename
    if not target.exists() or target.suffix != ".db":
        return False
    if target.parent.resolve() != _backup_dir().resolve():
        return False
    target.unlink()
    return True


# ── Internal ──────────────────────────────────────────────────────────────────

def _info(path: Path) -> BackupInfo:
    stat = path.stat()
    stem = path.stem  # e.g. "cvw_20260317_020000" or "cvw_20260317_020000_manual"
    try:
        ts_part = stem[4:19]  # "20260317_020000"
        created_at = datetime.strptime(ts_part, "%Y%m%d_%H%M%S")
    except (ValueError, IndexError):
        created_at = datetime.fromtimestamp(stat.st_mtime)
    return BackupInfo(
        filename=path.name,
        path=path,
        size_bytes=stat.st_size,
        created_at=created_at,
    )
