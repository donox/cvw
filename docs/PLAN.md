# CVWdata — Development Plan

Living document tracking decisions, directions, and status of ongoing development.

---

## Current Direction

Build and maintain a membership management web application for CVW (Central Virginia Woodturners), with a possible future extension to replace the public-facing website. See [PUBLIC_SITE_PLAN.md](PUBLIC_SITE_PLAN.md) for the public site option.

---

## Architecture

| Component | Choice | Rationale |
|---|---|---|
| Framework | FastAPI + Jinja2 | Server-side rendering, no frontend build step |
| Database | SQLite via SQLAlchemy | Lightweight, file-based, sufficient for club scale |
| Migrations | Alembic | Schema version control |
| Auth | Session-based (Starlette SessionMiddleware) | Simple, no JWT complexity needed |
| Passwords | passlib[bcrypt] pinned to bcrypt 4.x | passlib 1.7.4 incompatible with bcrypt 5.x |
| PDF | fpdf2 | Pure Python, no system dependencies |
| QR codes | qrcode[pil] | Program feedback QR generation |
| Settings | pydantic-settings via .env | Twelve-factor config |

---

## Decisions Log

| Date | Decision | Rationale |
|---|---|---|
| 2026-03-09 | FastAPI + Jinja2 (server-side rendering) | Simple, no separate frontend build step |
| 2026-03-09 | SQLite via SQLAlchemy | Lightweight, file-based, sufficient for membership scale |
| 2026-03-09 | Alembic for migrations | Schema version control |
| 2026-03-09 | App entry point at `app/main.py` | Docker/uvicorn convention (`app.main:app`) |
| 2026-03-09 | PDF member list via fpdf2 | Pure Python, no system dependencies |
| 2026-03-11 | Member fields match centralvawoodturners.org/membership-application/ | Single source of truth |
| 2026-03-11 | Session-based auth, role-permission mapping in dependencies.py | Simple; roles: admin, membership, program, financial, exec |
| 2026-03-11 | Auto-seed admin user on first startup via ADMIN_INITIAL_PASSWORD | Avoids chicken-and-egg bootstrap problem |
| 2026-03-12 | bcrypt pinned to 4.2.1 | passlib 1.7.4 incompatible with bcrypt 5.x |
| 2026-03-12 | email nullable on Member | Honorary members often have no email address |
| 2026-03-12 | Officer.member_id nullable | Vacant positions must be representable |
| 2026-03-12 | Docker deferred until production deploy | No benefit during active development |

---

## Completed Features

### Infrastructure
- [x] FastAPI app scaffold (`app/main.py`, `app/database.py`)
- [x] Alembic migrations (initial + all expansions)
- [x] Session-based auth with role-permission mapping
- [x] UserMiddleware sets `request.state.user` for all templates
- [x] Auto-seed admin user on first startup
- [x] Docker / docker-compose setup (dev)
- [x] Role-aware nav bar (CVW brown theme)

### Member Management
- [x] Member model — full field set matching CVW application form
- [x] CRUD routes (list, new, create, detail, edit, update, delete)
- [x] Member list: search by last name, sort by column, last-updated column
- [x] PDF current member list
- [x] Public membership application form (`/apply`) with confirmation page
- [x] Membership status (Prospective/Active/Former/Life), dues tracking
- [x] Payment method, dues amount, donation fields
- [x] Excel import script (`scripts/import_members.py`) — 109 members loaded from 2026 spreadsheet

### Programs
- [x] Program model + CRUD
- [x] Public feedback form (QR code accessible, anonymous option)
- [x] QR code generation per program (PNG + printable page)
- [x] Anchored rating scales (Program Quality, Relevance, Learned Something)
- [x] Program summary statistics

### Financial Console
- [x] FinancialTransaction model (income/expense, categories)
- [x] Transaction CRUD with type filter
- [x] YTD summary dashboard with category breakdown
- [x] Dues status report (paid/unpaid active members, Life excluded)

### Executive Console
- [x] Officer model — elected and volunteer categories, nullable member, notes
- [x] 2026-2027 officers seeded (19 positions, linked to members)
- [x] Exec dashboard: elected committee + volunteer staff separated
- [x] Org schedule (OrgEvent) CRUD
- [x] Action items / todo (OrgTodo) CRUD with priority and status

### Admin Console
- [x] User management (list, create, edit, activate/deactivate)
- [x] Dashboard card grid (role-aware)
- [x] Planning documents viewer

---

## Pending / Backlog

- [ ] Pagination on member list (currently loads all ~109 members)
- [ ] Email member(s) directly from member detail page
- [ ] Program console — add auth to remaining routes
- [ ] Feedback summary report per program (currently just averages on detail page)
- [ ] PayPal dues payment integration
- [ ] Production deployment (Docker + nginx/Caddy + domain)
- [ ] Public-facing website (see PUBLIC_SITE_PLAN.md)

---

## Conventions

- One router file per resource (`app/routers/members.py`)
- One model file per resource (`app/models/member.py`)
- Templates grouped by resource (`app/templates/members/`)
- Use `get_db()` dependency injection for all DB access
- `.env` for all environment-specific config; never hardcode
- Form dropdowns defined as constants in the router file
- SQLite batch mode required for `ALTER COLUMN` in Alembic migrations

---

## Deployment

### Development (current)
```bash
source .venv/bin/activate
uvicorn app.main:app --reload
```
Open `http://localhost:8000`. To move to another machine: copy `data/cvw.db`.

### Production (when ready)
See Docker section — add nginx/Caddy reverse proxy for HTTPS, switch `docker-compose.yml` to remove `--reload` and the local volume mount. Consider PostgreSQL if concurrent write load becomes an issue (unlikely at CVW scale).

```bash
docker compose up -d --build
docker compose exec web alembic upgrade head
```
