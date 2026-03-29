# CVWdata Server Administration Guide

Reference for Docker Compose and Alembic commands used to manage the production
server at cvwdev.org. All commands run from `/opt/cvwapp` on the server unless
noted otherwise.

---

## Connecting to the Server

```bash
ssh root@cvwdev.org
cd /opt/cvwapp
```

---

## Docker Compose

The app runs as a Docker container named `web` (defined in `docker-compose.yml`).
Caddy runs as a separate container handling HTTPS.

### Start / Stop / Restart

```bash
docker compose up -d          # start all containers in background
docker compose down           # stop and remove containers (data is safe — db is a volume)
docker compose restart web    # restart just the app container
```

### Deploy a Code Update

Pull the latest code from git, then rebuild and restart:

```bash
git pull
docker compose up -d --build
```

`--build` rebuilds the image with the new code. The app is briefly unavailable
during the restart (a few seconds).

### View Logs

```bash
docker compose logs web           # all logs for the app container
docker compose logs web -f        # follow (live tail)
docker compose logs web --tail=50 # last 50 lines
docker compose logs caddy         # Caddy / HTTPS proxy logs
```

Use logs to diagnose startup errors, 500 responses, or migration failures.

### Run a Command Inside the Container

```bash
docker compose exec web bash -c "cd /app && <command>"
```

The container's working directory for the app is `/app`. Always `cd /app` before
running Python or Alembic commands so imports resolve correctly.

### Open an Interactive Shell

```bash
docker compose exec web bash
cd /app
```

Useful for one-off debugging. Exit with `exit`.

### Copy a File Into the Container

```bash
docker compose cp /path/on/host web:/app/filename.py
```

Used to run admin scripts that need access to the app's Python environment.
See [Admin Scripts](#admin-scripts) below.

### Check Container Status

```bash
docker compose ps       # running containers and their state
docker compose top      # processes inside containers
```

---

## Alembic (Database Migrations)

Alembic tracks which schema changes have been applied to the SQLite database.
Each migration is a Python file in `alembic/versions/` with a unique revision ID.

### Apply All Pending Migrations

```bash
docker compose exec web bash -c "cd /app && alembic upgrade head"
```

Run this after every `git pull` that includes new migration files. `head` means
"apply everything up to the latest revision." Safe to run when already up to
date — it does nothing.

### Check Current Migration State

```bash
docker compose exec web bash -c "cd /app && alembic current"
```

Shows which revision the database is on. If it says `(head)` you are up to date.

### View Migration History

```bash
docker compose exec web bash -c "cd /app && alembic history"
```

Lists all revisions oldest-to-newest with their IDs and descriptions.

### Stamp a Revision (Fix Mismatched State)

```bash
docker compose exec web bash -c "cd /app && alembic stamp <revision_id>"
```

Use when the database table already exists but Alembic doesn't know about it —
for example, if the table was created by SQLAlchemy's `create_all` before
migrations were in place, or if a migration partially ran and left the tracking
table out of sync.

**This does NOT run the migration.** It only updates Alembic's internal record
to say "this revision has been applied." Use it only when you are certain the
schema already matches what the migration would have created.

Example:
```bash
docker compose exec web bash -c "cd /app && alembic stamp a1b2c3d4e5f6"
```

### Downgrade One Step (Undo Last Migration)

```bash
docker compose exec web bash -c "cd /app && alembic downgrade -1"
```

Rolls back the most recent migration. Use with caution — some downgrades drop
columns or tables and lose data.

---

## Common Scenarios

### Scenario: New code was pushed — deploy it

```bash
git pull
docker compose up -d --build
docker compose exec web bash -c "cd /app && alembic upgrade head"
docker compose logs web --tail=20   # confirm clean startup
```

### Scenario: Migration fails with "table already exists"

The table was created outside of Alembic (e.g. by `create_all` on first boot).

1. Stamp the revision so Alembic considers it done:
   ```bash
   docker compose exec web bash -c "cd /app && alembic stamp <revision_id>"
   ```
2. If the migration also seeded data, run the seed script manually
   (see Admin Scripts below).
3. Confirm state:
   ```bash
   docker compose exec web bash -c "cd /app && alembic current"
   ```

### Scenario: App won't start after a deploy

```bash
docker compose logs web --tail=50
```

Common causes:
- Missing `.env` variable — add it to `/opt/cvwapp/.env` and restart
- Migration not applied — run `alembic upgrade head`
- Python import error in new code — check the traceback in logs

### Scenario: Need to check what's in the database

```bash
docker compose exec web bash -c "sqlite3 /app/data/cvw.db"
```

Standard SQLite shell. Useful commands:
```sql
.tables                        -- list all tables
.schema account_categories     -- show a table's schema
SELECT * FROM account_categories;
.quit
```

---

## Admin Scripts

One-off Python scripts (seeding data, fixing records, etc.) live in
`scripts/admin/` on your local machine. This directory is gitignored so it is
safe to include passwords or sensitive values.

### Workflow

**On your local machine** — sync scripts to the server:
```bash
./scripts/sync_admin.sh
```

**On the server** — run a script inside the container:
```bash
bash /opt/cvwapp/admin/run_admin.sh seed_accounts.py
```

`run_admin.sh` copies the script into `/app` inside the container, runs it from
there (so all app imports work), then deletes it.

### Writing an Admin Script

Admin scripts must import all SQLAlchemy models before querying, because
SQLAlchemy resolves relationships by name at query time:

```python
# Always include these imports at the top of admin scripts
import app.models.member, app.models.user, app.models.officer, app.models.org
import app.models.program, app.models.group, app.models.email_models
from app.database import SessionLocal
from app.models.whatever import MyModel

db = SessionLocal()
try:
    # ... your logic
    db.commit()
finally:
    db.close()
```

### Bootstrapping sync_admin.sh (First Time)

`sync_admin.sh` uses rsync over SSH. If SSH key auth is not set up, rsync will
hang waiting for a password prompt that never appears in the pipe. Workaround:
create files directly on the server with `cat > /path/file << 'EOF'` in your
SSH session, then copy into the container with `docker compose cp`.

To set up SSH key auth permanently (eliminates the hang):
```bash
# On your local machine
ssh-copy-id root@cvwdev.org
```

After that, `./scripts/sync_admin.sh` will work without hanging.

---

## Quick Reference

| Goal | Command |
|---|---|
| Deploy new code | `git pull && docker compose up -d --build` |
| Apply migrations | `docker compose exec web bash -c "cd /app && alembic upgrade head"` |
| Check migration state | `docker compose exec web bash -c "cd /app && alembic current"` |
| Fix mismatched migration | `docker compose exec web bash -c "cd /app && alembic stamp <id>"` |
| View app logs | `docker compose logs web -f` |
| Open app shell | `docker compose exec web bash` then `cd /app` |
| SQLite shell | `docker compose exec web bash -c "sqlite3 /app/data/cvw.db"` |
| Run admin script | `bash /opt/cvwapp/admin/run_admin.sh <script.py>` |
| Sync admin scripts | `./scripts/sync_admin.sh` (run locally) |
