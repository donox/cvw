# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Purpose

CVW Membership Database — a FastAPI web application for managing CVW membership data, backed by SQLite.

## Environment

- Python 3.12 (CPython)
- Virtual environment at `.venv/` — activate with `source .venv/bin/activate`
- Install dependencies: `pip install -r requirements.txt`

## Architecture

- Entry point: `app/main.py` (FastAPI app instance)
- `app/database.py` — SQLAlchemy engine, session, Base, `get_db()` dependency
- `app/dependencies.py` — role/permission guards (`require_role`, `require_permission`)
- `app/models/` — SQLAlchemy ORM models (member, user, officer, program, financial, group, group_leader, email_models, event_registration, resource, site_content, org)
- `app/routers/` — FastAPI routers (one file per resource):
  - `auth` — login/logout
  - `members` — member CRUD, query/report, PDF
  - `apply` — public membership application
  - `programs` — program CRUD, QR codes
  - `feedback` — public feedback form
  - `financial` — transactions, Chart of Accounts, reports, CSV export
  - `exec_` — officers, org events, action items
  - `admin_console` — users, site settings, content blocks, access control
  - `admin_backup` — backup/restore console
  - `groups` — member groups (static + dynamic)
  - `email_` — compose, templates, scheduled email, log; accepts `?group_id=` on compose to pre-select a group
  - `librarian` — resource library CRUD
  - `public_` — public website (`/site/`)
  - `guides` — serves `docs/*.md` at `/guides/`
  - `processes` — process library, serves `docs/processes/*.md` at `/processes/`
  - `activity_group` — member activity groups; prefix `/activity`; overall-leader dashboard, member roster, events, resources, self opt-in/out
- `app/schemas/` — Pydantic schemas
- `app/templates/` — Jinja2 HTML templates (subdirectory per resource)
- `app/email_service.py` — Mailgun HTTP API integration
- `app/backup_service.py` — SQLite hot backup logic
- `app/registration_service.py` — event registration + waitlist promotion
- `app/scheduler.py` — APScheduler 3.x instance with SQLAlchemy jobstore
- `alembic/` — database migrations
- `data/` — SQLite database file (gitignored)
- Config via `.env` (see `.env.example`): `DATABASE_URL`, `APP_TITLE`, `MAILGUN_*`, `ADMIN_INITIAL_PASSWORD`

## Scripts

- `scripts/backup.py` / `scripts/restore.py` — emergency standalone backup/restore
- `scripts/import_members.py` — one-time Excel import (109 members)
- `scripts/seed_officers.py` / `scripts/seed_resources.py` — one-time data seeders
- `scripts/sync_admin.sh` — rsync `scripts/admin/` to production server (gitignored scripts safe to deploy)
- `scripts/run_admin.sh` — runs a Python script inside the Docker container
- `scripts/fix_server_accounts.sh` — production: stamps Alembic migration + seeds Chart of Accounts
- `scripts/admin/seed_accounts.py` — seeds AccountCategory with 12 default categories (idempotent)
- `scripts/admin/seed_drop_in_saturday.py` — seeds Drop-In Saturday activity group and assigns overall leaders interactively (gitignored)

## Supplementary Docs

- `docs/PLAN.md` — living development plan and decisions log
- `docs/FINANCIAL_PLAN.md` — financial module enhancement roadmap
- `docs/PUBLIC_SITE_PLAN.md` — public website phase roadmap
- `docs/MAINTENANCE.md` — guide for non-technical long-term maintenance
- `docs/SERVER_ADMIN.md` — server administration guide (DigitalOcean Docker deployment)
- `docs/processes/` — YAML-frontmatter Markdown files defining organisational processes
- `docs/guides/` — Markdown guides served at `/guides/` (including `defining_processes.md`)

## Dependency Notes

- `bcrypt` pinned to `4.2.1` — passlib 1.7.4 incompatible with bcrypt 5.x
- `APScheduler` 3.x (not 4.x) — different API; jobstore backed by SQLAlchemy

## Running

```bash
uvicorn app.main:app --reload
```

Or with Docker:

```bash
docker-compose up
```

## Migrations

```bash
alembic revision --autogenerate -m "description"
alembic upgrade head
```
