#!/usr/bin/env python
"""Standalone restore script — for use when the admin console is unavailable.

IMPORTANT: Stop the server before running this script to avoid data corruption.

Usage:
    python scripts/restore.py                  # list available backups
    python scripts/restore.py <filename>        # restore from named backup
    python scripts/restore.py --latest          # restore from most recent backup

Examples:
    python scripts/restore.py cvw_20260317_020000.db
    python scripts/restore.py --latest
"""
import argparse
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.backup_service import _backup_dir, _db_path, list_backups


def main():
    parser = argparse.ArgumentParser(description="Restore CVW database from backup")
    parser.add_argument("filename", nargs="?", help="Backup filename to restore")
    parser.add_argument("--latest", action="store_true",
                        help="Restore from the most recent backup")
    parser.add_argument("--yes", action="store_true",
                        help="Skip confirmation prompt")
    args = parser.parse_args()

    backups = list_backups()
    if not backups:
        print("No backups found in data/backups/")
        sys.exit(1)

    if not args.filename and not args.latest:
        print("Available backups (newest first):\n")
        for i, b in enumerate(backups):
            print(f"  {i+1:2d}.  {b.filename}  ({b.size_display})  {b.created_at.strftime('%Y-%m-%d %H:%M')}")
        print("\nUsage:")
        print("  python scripts/restore.py <filename>")
        print("  python scripts/restore.py --latest")
        return

    if args.latest:
        target = backups[0]
    else:
        path = _backup_dir() / args.filename
        if not path.exists():
            print(f"Error: {args.filename} not found in data/backups/")
            sys.exit(1)
        from app.backup_service import _info
        target = _info(path)

    print(f"\nRestore target : {target.filename}")
    print(f"Created        : {target.created_at.strftime('%Y-%m-%d %H:%M')}")
    print(f"Size           : {target.size_display}")
    print(f"Will replace   : {_db_path()}\n")

    if not args.yes:
        confirm = input("This will OVERWRITE the current database. Type 'yes' to continue: ")
        if confirm.strip().lower() != "yes":
            print("Aborted.")
            return

    # Back up current DB before overwriting
    current = _db_path()
    safety = current.parent / "pre_restore_safety.db"
    if current.exists():
        shutil.copy2(str(current), str(safety))
        print(f"  Safety copy saved to: {safety.name}")

    shutil.copy2(str(target.path), str(current))
    print(f"  ✓ Restored from {target.filename}")
    print("\nRestart the server to use the restored database.")


if __name__ == "__main__":
    main()
