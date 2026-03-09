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
- `app/models/` — SQLAlchemy ORM models
- `app/routers/` — FastAPI routers
- `app/schemas/` — Pydantic schemas
- `app/templates/` — Jinja2 HTML templates (subdirectory per resource, e.g. `templates/members/`)
- `alembic/` — database migrations
- `data/` — SQLite database file (gitignored)
- Config via `.env` (see `.env.example`): `DATABASE_URL`, `APP_TITLE`

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
