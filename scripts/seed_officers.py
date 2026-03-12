"""
Seed 2026-2027 CVW officer/volunteer positions.
Safe to re-run: skips positions that already exist (same title + active).

Usage:
    source .venv/bin/activate
    python scripts/seed_officers.py
"""
import sys
from pathlib import Path
from datetime import date

sys.path.insert(0, str(Path(__file__).parent.parent))

import app.models.program
import app.models.officer
import app.models.org
import app.models.financial
import app.models.user
from app.database import SessionLocal
from app.models.member import Member
from app.models.officer import Officer

TERM_START = date(2026, 1, 1)
TERM_END   = date(2026, 12, 31)

# (title, category, last_name, first_name_hint, notes)
# last_name=None → vacant position
POSITIONS = [
    # ── Elected ────────────────────────────────────────────────────────────────
    ("President",              "Elected", None,       None,       None),
    ("VP Program Coordinator", "Elected", None,       None,       None),
    ("VP Member Services",     "Elected", "Oxley",    "Don",      None),
    ("Treasurer",              "Elected", "Burton",   "Ron",      None),
    ("Secretary",              "Elected", "Schmidt",  "John",     None),
    ("Skills Center Director", "Elected", "Oates",    "Jim",      None),
    # ── Volunteer ──────────────────────────────────────────────────────────────
    ("Cheese Shop Coordinator",                   "Volunteer", "Reeves",   "Tom",   None),
    ("Shenandoah Valley Arts Center Coordinator", "Volunteer", "Steck",    "Mark",  None),
    ("Newsletter Editor",                         "Volunteer", None,       None,    None),
    ("Video Team",                                "Volunteer", "Andrews",  "Robert",None),
    ("Video Team",                                "Volunteer", "Shiflet",  "Bob",   None),
    ("Photographer",                              "Volunteer", "Shiflet",  "Bob",   None),
    ("Store Manager",                             "Volunteer", "Culver",   "Mark",  None),
    ("Librarian",                                 "Volunteer", "Shombert", "David", None),
    ("AnchorSeal Manager",                        "Volunteer", "Guendel",  "Fred",  None),
    ("VA Symposium Board Member",                 "Volunteer", "Conley",   "Gary",  None),
    ("VA Symposium Board Member",                 "Volunteer", None,       None,    "Second board member TBD"),
    ("Webmaster",                                 "Volunteer", None,       None,    None),
    ("Assistant Skills Center Director",          "Volunteer", "Conley",   "Gary",  None),
]


def find_member(db, last_name, first_name_hint):
    if not last_name:
        return None
    q = db.query(Member).filter(Member.last_name.ilike(last_name))
    results = q.all()
    if not results:
        print(f"  WARNING: no member found for last_name='{last_name}'")
        return None
    if len(results) == 1:
        return results[0]
    # Multiple matches — use first name hint
    if first_name_hint:
        for m in results:
            if m.first_name.lower().startswith(first_name_hint[:3].lower()):
                return m
    print(f"  WARNING: ambiguous match for '{last_name}', using first result")
    return results[0]


def main():
    db = SessionLocal()
    try:
        created = skipped = 0
        for title, category, last_name, first_hint, notes in POSITIONS:
            member = find_member(db, last_name, first_hint)
            member_id = member.id if member else None

            # Skip if identical active position already exists
            exists = (
                db.query(Officer)
                .filter(
                    Officer.title == title,
                    Officer.active == True,
                    Officer.member_id == member_id,
                )
                .first()
            )
            if exists:
                skipped += 1
                continue

            db.add(Officer(
                title=title,
                category=category,
                member_id=member_id,
                notes=notes,
                term_start=TERM_START,
                term_end=TERM_END,
                active=True,
            ))
            holder = f"{member.first_name} {member.last_name}" if member else "Vacant"
            print(f"  + {category:10s}  {title:45s}  {holder}")
            created += 1

        db.commit()
        print(f"\nDone: {created} created, {skipped} skipped (already exist)")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
