# CVWdata Development Plan

Living document tracking decisions, directions, and instructions for ongoing development.
Update this as decisions are made or directions change.

---

## Decisions Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-03-09 | FastAPI + Jinja2 (server-side rendering) | Simple, no separate frontend build step |
| 2026-03-09 | SQLite via SQLAlchemy | Lightweight, file-based, sufficient for membership scale |
| 2026-03-09 | Alembic for migrations | Schema version control |
| 2026-03-09 | App entry point at `app/main.py` | Docker/uvicorn convention (`app.main:app`) |
| 2026-03-09 | No authentication initially | Deferred — add later |
| 2026-03-09 | PDF member list via fpdf2 | Pure Python, no system dependencies |
| 2026-03-11 | Member fields match centralvawoodturners.org/membership-application/ | Single source of truth for field definitions |
| 2026-03-11 | volunteer_interest stored as Boolean (True/Yes, False/Not at this time) | Clean storage; rendered as radio buttons |
| 2026-03-11 | years_turning stored as String with fixed options | Matches dropdown ranges on public form |

---

## Current Direction

- Build a membership management web application for CVW
- Server-rendered HTML using Jinja2 templates
- REST-style routing with FastAPI routers per resource
- Member data mirrors the public membership application form at centralvawoodturners.org

---

## Completed

- [x] FastAPI app scaffold (`app/main.py`, `app/database.py`)
- [x] Member model with full field set (personal, address, phone, membership, volunteer, other)
- [x] Pydantic schemas (create, update, read)
- [x] Alembic migrations (initial + field expansion)
- [x] CRUD routes (list, new, create, detail, edit, update, delete)
- [x] Jinja2 templates (list, form, detail) with fieldset layout
- [x] PDF current member list (sorted by last/first name, includes type and skill)
- [x] Docker / docker-compose setup

---

## Pending Decisions

- [ ] Authentication — deferred, not in initial scope
- [ ] Pagination — needed once member count grows
- [ ] Member status field (Active, Inactive, Lapsed) — not on public form but likely needed for management
- [ ] Dues / renewal tracking
- [ ] Import existing member data (CSV?)

---

## Conventions

- One router file per resource (`app/routers/members.py`)
- One schema file per resource (`app/schemas/member.py`)
- One model file per resource (`app/models/member.py`)
- Templates grouped by resource (`app/templates/members/`)
- Use `get_db()` dependency injection for all DB access
- `.env` for all environment-specific config; never hardcode
- Form dropdowns defined as constants in the router file (e.g. `MEMBERSHIP_TYPES`, `SKILL_LEVELS`)

---

## Out of Scope (for now)

- Authentication (deferred)
- REST API for external clients (JSON only endpoints)
- Background tasks / job queue
- Multi-tenancy
