# CVWdata — CVW Membership Database

Web application for managing membership, programs, finances, and the public website for
[Central Virginia Woodturners](https://centralvawoodturners.org).

Built with FastAPI + Jinja2 (server-side rendering), SQLite via SQLAlchemy, and Alembic migrations.

---

## Features

- **Members** — full CRUD, search, dues tracking, PDF member list, Excel import
- **Programs** — CRUD, public feedback form with QR code, ratings
- **Financial** — transaction ledger, YTD dashboard, dues status report
- **Executive** — officer roster, org schedule (events), action items, attendance, event registration with waitlist
- **Email** — compose & send, templates, scheduled email (APScheduler), email log
- **Member Groups** — many-to-many, usable as email targets
- **Public website** (`/site/`) — home, about, officers, calendar, upcoming events, skill center, resources, contact, event registration
- **Librarian** — resource library CRUD; public resources page
- **Admin** — user management, site content editor, database backups, planning docs viewer

---

## Setup

**Requirements:** Python 3.12, git

```bash
# 1. Clone the repo
git clone <repo-url>
cd CVWdata

# 2. Create virtual environment
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt
# If the pip script fails, use: python3 -m pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env — set SECRET_KEY; leave SMTP_HOST blank to disable email

# 5. Run database migrations
alembic upgrade head

# 6. Start the app
uvicorn app.main:app --reload
# Or, if the script fails: python3 -m uvicorn app.main:app --reload
```

Open `http://localhost:8000` in a browser. The admin account is created automatically
on first startup using `ADMIN_INITIAL_PASSWORD` from `.env` (default: `admin`).

### Running on a local network

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Other machines on the network can then reach the app at `http://<your-ip>:8000`.

---

## Database

The SQLite database lives at `data/cvw.db` (gitignored). Copy this file to move the
database to another machine.

### Migrations

```bash
# Apply all pending migrations
alembic upgrade head

# Create a new migration after model changes
alembic revision --autogenerate -m "description"
```

### Backups

Automated daily backups run at 2 AM (via APScheduler). The admin console at
`/admin/backup/` supports manual backup, download, restore, and retention settings.

Emergency CLI scripts are also available:
```bash
python scripts/backup.py
python scripts/restore.py <backup-file>
```

---

## Roles

| Role | Access |
|---|---|
| `admin` | Everything |
| `exec` | Executive console, members, groups, programs |
| `membership` | Members, groups, email |
| `program` | Programs |
| `financial` | Financial console |
| `librarian` | Resource library |

---

## Project layout

```
app/
  main.py          # FastAPI app, middleware, startup seeding
  database.py      # SQLAlchemy engine and session
  dependencies.py  # Auth dependencies and role-permission map
  models/          # SQLAlchemy ORM models
  routers/         # FastAPI route handlers
  templates/       # Jinja2 HTML templates
alembic/           # Database migrations
data/              # SQLite database (gitignored)
docs/              # Planning documents
scripts/           # Standalone utility scripts
```

---

## Development notes

See `docs/PLAN.md` for architecture decisions, completed features, and backlog.
See `docs/PUBLIC_SITE_PLAN.md` for the public website roadmap.
See `CLAUDE.md` for guidance specific to working with Claude Code.
