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
| 2026-03-09 | Member fields: first_name, last_name, email | Minimal viable model; expand later |
| 2026-03-09 | No authentication initially | Deferred — add later |
| 2026-03-09 | PDF member list via fpdf2 | Pure Python, no system dependencies |

---

## Current Direction

- Build a membership management web application for CVW
- Server-rendered HTML using Jinja2 templates
- REST-style routing with FastAPI routers per resource

---

## Pending Decisions

- [ ] Authentication — deferred, not in initial scope
- [ ] Pagination strategy for member lists
- [ ] Additional member fields beyond initial set (phone, address, join date, status, etc.)

---

## Build Order

1. **Data model** — define `Member` (and related) SQLAlchemy models
2. **Schema** — Pydantic schemas for validation and serialization
3. **Migration** — initial Alembic migration
4. **Routers** — CRUD routes for members
5. **Templates** — list, detail, create/edit, delete confirmation views
6. **Auth** — if required
7. **Docker** — verify end-to-end with docker-compose

---

## Conventions

- One router file per resource (`app/routers/members.py`)
- One schema file per resource (`app/schemas/members.py`)
- One model file per resource (`app/models/member.py`)
- Templates grouped by resource (`app/templates/members/`)
- Use `get_db()` dependency injection for all DB access
- `.env` for all environment-specific config; never hardcode

---

## Out of Scope (for now)

- Authentication (deferred)
- REST API for external clients (JSON only endpoints)
- Background tasks / job queue
- Multi-tenancy
