#!/usr/bin/env python
"""Standalone backup script — safe to run while the server is running.

Usage:
    python scripts/backup.py [--keep N]

Options:
    --keep N    Keep the N most recent backups (default: 30)
"""
import argparse
import sys
from pathlib import Path

# Allow running from the project root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.backup_service import create_backup, list_backups, prune_backups


def main():
    parser = argparse.ArgumentParser(description="Create a CVW database backup")
    parser.add_argument("--keep", type=int, default=30,
                        help="Number of backups to retain (default: 30)")
    args = parser.parse_args()

    print("Creating backup...")
    info = create_backup(label="manual")
    print(f"  ✓ {info.filename}  ({info.size_display})")

    pruned = prune_backups(args.keep)
    if pruned:
        print(f"  Pruned {pruned} old backup(s). Keeping last {args.keep}.")

    all_backups = list_backups()
    print(f"  {len(all_backups)} backup(s) stored in data/backups/")


if __name__ == "__main__":
    main()
