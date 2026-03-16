# CVWdata — Development Plan

Living document tracking decisions, directions, and status of ongoing development.

---

## Current Direction

Build and maintain a membership management web application for CVW (Central Virginia Woodturners), with a public-facing website at `/site/` (Phase 1 live). See [PUBLIC_SITE_PLAN.md](PUBLIC_SITE_PLAN.md) for the public site roadmap and [FINANCIAL_PLAN.md](FINANCIAL_PLAN.md) for planned financial enhancements.

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
| Email | smtplib (stdlib) | No external dependency; SMTP config in .env |
| Scheduling | APScheduler 3.x + SQLAlchemy jobstore | Persistent scheduled email jobs |

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
| 2026-03-13 | Member Groups (many-to-many) for email targeting | Allows sending to subsets without changing member records |
| 2026-03-13 | APScheduler with SQLAlchemy jobstore for scheduled email | Jobs survive server restarts |
| 2026-03-13 | Dual email rendering: simple (string replace) vs. Jinja2 | Simple is safer for non-technical users; Jinja2 available when needed |
| 2026-03-13 | User linked to Member via member_id FK | Enables personalised defaults (test email address) and audit trails |
| 2026-03-13 | must_change_password flag on User | Forces password change at first login for new accounts |
| 2026-03-13 | show_on_public flag on Program | Controls which programs appear on public next-meeting page |
| 2026-03-13 | Public site at /site/ prefix | Internal / at root already taken by dashboard redirect |
| 2026-03-15 | Financial enhancements deferred — plan doc circulated | No bookkeeping library needed; single-entry is sufficient at CVW scale |
| 2026-03-15 | Resource library backed by DB table, not YAML | Form-per-entry editor is equivalent work to YAML + editor; DB fits existing patterns and is usable by non-technical officers |
| 2026-03-15 | `librarian` role added; Volunteer dropdown in nav | Volunteer roles are a distinct nav group from officer consoles; dropdown supports future additions |

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
- [x] User → Member link (member select replaces free-text name)
- [x] Forced password change on first login (`must_change_password` flag)
- [x] Dashboard card grid (role-aware)
- [x] Planning documents viewer (`docs/*.md`)

### Member Groups
- [x] MemberGroup model with many-to-many to Member
- [x] Group CRUD (`/groups/`) — membership VP + admin
- [x] Client-side member filter on group edit form
- [x] Groups usable as email targets in compose and scheduled email

### Email Console
- [x] Compose & send — to all active members or a named group
- [x] Per-member personalisation mode (individual sends with substitutions)
- [x] Dual rendering: Simple (`{{ variable }}` replace) and Jinja2 (if/for/filters)
- [x] Email templates — CRUD, name, subject, body, rendering mode
- [x] Test email button on template edit page (sends to author with sample data)
- [x] Scheduled email — APScheduler cron jobs, persisted in DB, active/inactive toggle
- [x] Email log — records every send with recipient count, status, errors
- [x] Available template variables: first_name, last_name, full_name, email, membership_type, status, dues_paid

### Programs (additions)
- [x] `show_on_public` flag — quick toggle on program list
- [x] Programs with flag drive public next-meeting page

### Public Website (Phase 1)
- [x] Base public template (`base_public.html`) — CVW brown/tan palette, mobile responsive
- [x] Home page (`/site/`) — next program + upcoming events
- [x] About, Officers, Calendar, Next Meeting, Skill Center, Contact pages
- [x] Next Meeting page driven by `show_on_public` programs
- [x] Resources page (`/site/resources`) — grouped by category, active items only

### Event Registration & Attendance
- [x] `EventRegistration` model — confirmed/waitlist/cancelled, cancel token, member or visitor
- [x] `Attendance` model — member checklist + visitor name/email, recorded_by (future kiosk: null)
- [x] OrgEvent additions: `zoom_url`, `registration_enabled`, `capacity`, `registration_note`
- [x] Officer: attendance entry per event (member checklist with filter + visitor freeform)
- [x] Officer: registrations view — confirmed list, waitlist, officer cancel
- [x] Officer cancel auto-promotes next waitlisted person and sends email
- [x] Public: `/site/events/{id}/register` — member path (email lookup) and visitor path
- [x] Public: attendance type choice (In Person / Remote) when zoom_url is set
- [x] Public: self-cancel via token link in confirmation email
- [x] Emails: confirmed, waitlisted, promoted off waitlist (all via existing SMTP)
- [x] Calendar shows "Sign up" button and "Zoom available" indicator

### Librarian Console
- [x] Resource model (category, title, url, description, sort_order, active)
- [x] CRUD at `/librarian/resources/` — librarian + admin roles
- [x] Category datalist for autocomplete (derive from existing rows, allow new)
- [x] Active toggle — controls visibility on public site
- [x] `librarian` role added to ROLE_PERMISSIONS and ROLES
- [x] "Volunteer ▾" CSS dropdown in internal nav (librarian + admin)
- [x] 93 resources seeded from centralvawoodturners.org (`scripts/seed_resources.py`)

---

## Pending / Backlog

### Member Management
- [ ] Pagination on member list (currently loads all ~109 members)
- [ ] Email member(s) directly from member detail page

### Programs
- [ ] Program console — add auth to remaining routes
- [ ] Feedback summary report per program (currently just averages on detail page)

### Financial Console
- [ ] Chart of Accounts — DB-managed categories replacing hardcoded lists
- [ ] Fiscal year awareness — configurable start, year selector on dashboard
- [ ] Reports page — Income & Expense Summary, Month-by-Month, Transaction Ledger
- [ ] Budget — optional actual vs. budget comparison
- [ ] CSV export of filtered transactions
- [ ] (Optional) PDF reports via fpdf2
- See [FINANCIAL_PLAN.md](FINANCIAL_PLAN.md) for full discussion

### Infrastructure
- [ ] Production deployment (Docker + nginx/Caddy + domain)
- [ ] PayPal dues payment integration (requires public server + PayPal dev account)

### Public Website
- [ ] Phase 2: newsletters, resources, gallery (see PUBLIC_SITE_PLAN.md)

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
