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
- [x] Public membership application form (`/apply`) with confirmation page
- [x] Membership status (Prospective/Active/Former) and dues (paid, date) fields
- [x] Docker / docker-compose setup (dev)

---

## Pending Decisions

- [ ] Authentication — deferred until after initial deploy
- [ ] Pagination — needed once member count grows
- [ ] Import existing member data (CSV?)

---

## Deployment (do after minimal deploy is working)

### Steps to deploy in a container

1. **Install Docker on server**
   ```bash
   sudo apt install docker.io docker-compose-plugin
   sudo systemctl enable --now docker
   ```

2. **Copy project to server** (rsync or git clone)
   ```bash
   rsync -av --exclude='.venv' --exclude='data/' --exclude='.git' \
     /home/don/PycharmProjects/CVWdata/ user@server:/opt/cvwdata/
   ```

3. **Create `.env` on server**
   ```bash
   cp .env.example .env   # edit if needed
   ```

4. **Fix `docker-compose.yml` for production** — remove the local volume mount
   (`. :/app`) and `--reload`; create a `docker-compose.prod.yml`

5. **Build and start**
   ```bash
   docker compose up -d --build
   ```

6. **Run migrations**
   ```bash
   docker compose exec web alembic upgrade head
   ```

7. **Reverse proxy** — put nginx or Caddy in front of port 8000 for HTTPS

### Subsequent updates
```bash
git pull
docker compose up -d --build
docker compose exec web alembic upgrade head   # if schema changed
```

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
