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
| 2026-03-17 | Automated daily backups via APScheduler; admin console at `/admin/backup/` | SQLite backup API for consistency; staged restore pattern (apply on restart); `scripts/backup.py` and `scripts/restore.py` for emergency use; retention configurable from console |
| 2026-03-16 | `OrgEvent.show_on_public` flag drives public "Upcoming Events" page | OrgEvent is the primary calendar model; Programs are a refinement (feedback QR, ratings); `show_on_public` belongs on OrgEvent |
| 2026-03-16 | Optional `org_event_id` FK on Program links to OrgEvent | Program is a refinement of OrgEvent; programs can display alongside event details on Upcoming Events page |
| 2026-03-16 | Renamed "Next Meeting" → "Upcoming Events" on public site | Page now shows all upcoming flagged OrgEvents, not just one; allows multiple programs/events to be visible |
| 2026-03-27 | Role permissions expanded — exec/financial/program now have email + groups edit | All officer roles can send email and manage groups, not just membership |
| 2026-03-27 | Planning docs (`docs/*.md`) served via `/guides/` for all logged-in users | No duplication; edits to source files reflected immediately |
| 2026-03-27 | Mailgun `h:Reply-To` — configurable default in `.env`, overridable per compose | Thunderbird strips Reply-To in some configurations; per-send override gives sender control |
| 2026-04-19 | `scripts/admin/` pattern for gitignored production scripts; deployed via `sync_admin.sh` + `run_admin.sh` | Avoids committing credentials or server-specific logic; scripts run inside Docker container |
| 2026-04-19 | Process Library stored as YAML-frontmatter Markdown in `docs/processes/`; rendered by a new router | File-based keeps processes in git history and editable by Claude Code; no DB or form editor needed for officers |

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
- [x] Admin script infrastructure (`scripts/admin/`, `sync_admin.sh`, `run_admin.sh`)
- [x] Chart of Accounts seeded on production via `fix_server_accounts.sh`

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
- [x] Dynamic groups — filter criteria (status, type, dues, skill, volunteer) resolved at send time
- [x] Migration: `is_dynamic`, `filter_criteria` columns added to `member_groups`

### Email Console
- [x] Compose & send — to all active members or a named group
- [x] Per-member personalisation mode (individual sends with substitutions)
- [x] Dual rendering: Simple (`{{ variable }}` replace) and Jinja2 (if/for/filters)
- [x] Email templates — CRUD, name, subject, body, rendering mode
- [x] Test email button on template edit page (sends to author with sample data)
- [x] Scheduled email — APScheduler cron jobs, persisted in DB, active/inactive toggle
- [x] Email log — records every send with recipient count, status, errors
- [x] Available template variables: first_name, last_name, full_name, email, membership_type, status, dues_paid
- [x] Single-member email from member detail page
- [x] Mailgun HTTP API (replaces SMTP, bypasses DigitalOcean port 587 block)
- [x] Reply-To header — configurable default in `.env` (`MAILGUN_REPLY_TO`); overridable per send in compose form

### Programs (additions)
- [x] `show_on_public` flag — kept on Program for officer reference
- [x] Optional `org_event_id` FK — link a Program to a calendar OrgEvent
- [x] Program details appear on public Upcoming Events page when linked to a flagged OrgEvent

### Public Website (Phase 1)
- [x] Base public template (`base_public.html`) — CVW brown/tan palette, mobile responsive
- [x] Home page (`/site/`) — next program + upcoming events
- [x] About, Officers, Calendar, Next Meeting, Skill Center, Contact pages
- [x] Upcoming Events page (`/site/upcoming-events`) driven by `OrgEvent.show_on_public`; shows linked Program details
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
- [x] File upload support — resources can be uploaded files (PDF, Word, etc.) stored in `app/static/resources/` or external URLs; `file_path` column added via migration

---

## Pending / Backlog

### Member Management
- [ ] Pagination on member list (currently loads all ~109 members)
- [x] Email member(s) directly from member detail page
- [x] Reverse sort (toggle asc/desc) on member list columns
- [x] Member Query / Report page — `/members/query` with filters, sortable columns, CSV export, print, Save as Group

### Programs
- [ ] Program console — add auth to remaining routes
- [ ] Feedback summary report per program (currently just averages on detail page)

### Financial Console
- [x] Chart of Accounts — DB-managed categories replacing hardcoded lists
- [ ] Fiscal year awareness — configurable start, year selector on dashboard
- [x] Reports page — Income & Expense Summary, Month-by-Month (Transaction Ledger still pending)
- [ ] Budget — optional actual vs. budget comparison
- [x] CSV export of filtered transactions
- [ ] (Optional) PDF reports via fpdf2
- See [FINANCIAL_PLAN.md](FINANCIAL_PLAN.md) for full discussion

### Infrastructure
- [x] Automated daily database backups (APScheduler, 2 AM, 30-day retention)
- [x] Admin backup console — manual backup, restore, download, retention setting
- [x] Emergency standalone scripts (`scripts/backup.py`, `scripts/restore.py`)
- [ ] Off-site backup delivery — Google Drive via rclone (see details below)
- [ ] Production deployment (Docker + nginx/Caddy + domain)
- [ ] PayPal dues payment integration (requires public server + PayPal dev account)

### Public Website
- [x] Members-only access — per-page flags + shared password; admin UI at `/admin/content/access`
- [x] Per-event registration restriction — `zoom_members_only` / `members_only` on OrgEvent; enforced in form and server-side
- [ ] Phase 2: newsletters, gallery (see PUBLIC_SITE_PLAN.md)

### Off-Site Backup — Google Drive (pending team decision)

**Approach:** rclone + SQLite hot backup, scheduled on the host droplet (not inside Docker).

**Key decisions needed:**
- [ ] Confirm team is OK storing backups on a personal Google Drive account
- [ ] Decide who owns the Google account used (ideally a shared club account)
- [ ] Decide retention period (suggested: 30 days of daily backups)

**Implementation steps (once decided):**
1. **Google credentials** — create a Service Account in Google Cloud Console; share a Drive folder with the service account email. No browser login needed after setup.
2. **Install rclone on the droplet**
   ```bash
   apt install rclone
   rclone config  # one-time setup; creates a remote named "gdrive"
   ```
3. **Backup script** (`/opt/cvwapp/scripts/offsite_backup.sh`):
   ```bash
   #!/bin/bash
   # Hot backup — consistent even with concurrent writes (WAL mode)
   STAMP=$(date +%Y%m%d_%H%M)
   sqlite3 /opt/cvwapp/data/cvw.db ".backup '/tmp/cvwapp_${STAMP}.db'"
   rclone copy "/tmp/cvwapp_${STAMP}.db" gdrive:cvwapp-backups/
   # Remove local temp file
   rm "/tmp/cvwapp_${STAMP}.db"
   # Prune Drive copies older than 30 days
   rclone delete gdrive:cvwapp-backups/ --min-age 30d
   ```
4. **Schedule** — add host cron job (runs after the 2 AM APScheduler local backup):
   ```bash
   15 2 * * * bash /opt/cvwapp/scripts/offsite_backup.sh >> /var/log/cvwapp_backup.log 2>&1
   ```

**Database notes:**
- SQLite is sufficient for CVW scale (2–3 concurrent users normally; burst during post-event report uploads)
- Enable WAL mode for safer concurrent writes: `PRAGMA journal_mode=WAL`
- SQLite's `.backup` command gives a consistent snapshot without stopping the app
- **Migrate to PostgreSQL only if** `database is locked` errors appear in logs after group events — migration is straightforward when needed

**Why not S3:** Google Drive is free at this scale and the club likely already has Google accounts. S3 would require AWS credentials and small monthly cost.

---

### Executive Console
- [ ] Reconsider non-officer event ownership for registration control (currently officer-only; future: event coordinator role or per-event owner)

### Process Library

A mechanism for defining, rendering, and managing key club operational processes in a form suitable for non-technical officers to follow.

**Storage:** YAML-frontmatter Markdown files in `docs/processes/` — version-controlled, Claude Code-editable via plain-English requests. No DB or in-app editor required.

**New router** `app/routers/processes.py` at `/processes/` (any logged-in user):

- [ ] List view — table of all processes (title, owner, status, last updated, open-questions badge)
- [ ] Detail view — structured HTML from YAML frontmatter + rendered Markdown narrative below
  - Overview card: description, owner, version
  - Roles table: Role | Current Person | Responsibilities
  - Path selector: JS tabs for multi-path processes (shows numbered steps for chosen path only)
  - Open Questions section — amber callout if any unresolved items
- [ ] Nav entry: "Processes" in internal nav, visible to all logged-in roles

**Process files schema** (YAML frontmatter fields):
- `process`, `version`, `status`, `last_updated`, `owner`, `description`
- `roles` — list of role objects (id, title, responsibilities, notes)
- `triggers` — entry points / starting conditions
- `steps` — with `actor`, `depends_on`, `trigger_variants` or `variants`
- `decision_points` — branching logic
- `artifacts` — documents and systems referenced
- `open_issues` — unresolved questions (drives the amber badge)

**Decisions made:**
- Editing model: file-based only (Claude Code) — no in-app editor
- Public visibility: processes are public only where necessary (e.g., renewal instructions); officer-only by default
- Compliance tracking: out of scope — process docs are reference material only

**Completed:**
- [x] List view — table of all processes with status badge and open-questions count
- [x] Detail view — roles table (current person from DB), path-selector tabs, open questions callout, narrative body
- [x] Nav entry: "Processes" visible to all logged-in roles
- [x] Current person pulled live from Officers table via `db_title` field on each role

**Pending — Visual & Authoring improvements:**
- [ ] Swimlane diagram — auto-generate Mermaid from YAML; render in-browser via mermaid.js CDN; no extra authoring needed
- [ ] Flat schema + form wizard — replace nested trigger_variants/variants with a flat Path→Steps model; form lets officers build processes without touching YAML (target authoring solution)
- [ ] Claude API "describe it" bridge — officer types plain-English process description; Claude converts to structured YAML; bridges the gap until form wizard is built

**Schema note:** Current YAML schema (trigger_variants, nested variants) is over-engineered for human authoring. Target schema flattens to: Process → named Paths → ordered Steps (actor + action). Simpler to form-edit and cleaner to generate Mermaid from. Migration path: rewrite membership process file when flat schema is adopted.

#### First Process: Membership — New Members and Renewals

- Source: `docs/processes/membership-new-and-renewal.md`
- Owner: VP Membership
- Three paths: In-Person Application, Online New Application, Online Renewal
- All paths converge at: Membership DB updated in Dropbox + member list posted to website
- Open questions resolved:
  1. Cash/check payment communication — **email** to VP Membership
  2. AI-monitored mailbox — **no automation for now**; mailbox is a future placeholder
  3. Dropbox membership DB location — **placeholder** (to be filled in when known)
  4. Backup for vacant VP Membership — **President**

---

### Member Activity Groups

A capability for managing recurring sub-group activities where a subset of CVW members opt in, there is dedicated leadership, and the group needs its own events, email, planning docs, and artifacts.

#### Pilot: Drop-In Saturday

- Meets the 4th Saturday of each month
- ~20 opted-in members participate
- **Two leadership tiers:**
  - *Monthly leader* — one member designated as leader for a specific month's session; rotates
  - *Overall leaders* — small standing committee (3–5 people) who own the program long-term
- Google Group exists for chat; keep it for now and link from the dashboard
- Needs: opt-in list, event management, email to members, shared planning notes, group artifacts

#### Architecture

**Reuse existing models where possible:**

| Need | Approach |
|---|---|
| Opt-in member list | Extend `MemberGroup` — add `is_activity` flag + `meeting_day`, `meeting_frequency`, `google_group_url` fields |
| Overall leaders | New `GroupLeader` table: `group_id`, `member_id`, `role` ("overall" or "monthly") |
| Monthly leader per event | Add `monthly_leader_id` FK (→ Member) to `OrgEvent` |
| Events | Reuse `OrgEvent` + `EventRegistration` + `Attendance`; filter by group |
| Email to group | Reuse email console — group already usable as target; no change needed |
| Group artifacts / resources | Add optional `group_id` FK to `Resource`; group-scoped resources shown on dashboard |
| Planning notes | Add `planning_notes` text field to `OrgEvent` — simple, visible to leaders only |
| Group chat | Link to existing Google Group URL — no in-app chat needed now |

**New router:** `app/routers/activity_group.py` at `/activity/` — visible to overall leaders + admin.

#### Pending — Phase 1 (core)

- [ ] DB changes: `is_activity`, `meeting_day`, `meeting_frequency`, `google_group_url` on `MemberGroup`; `GroupLeader` table; `monthly_leader_id` + `planning_notes` on `OrgEvent`; `group_id` on `Resource`
- [ ] Self-service opt-in: member can join/leave an activity group from their profile page (or a public `/activity/{slug}/join` page)
- [ ] Overall leader dashboard at `/activity/{slug}/` — scoped to one group:
  - Member roster (opted-in list, with join/leave controls)
  - Event list — upcoming + past sessions for this group
  - Designate monthly leader per event (dropdown on event edit)
  - Email compose — pre-targeted to this group's members
  - Artifacts — group-scoped resources (links, uploaded docs)
  - Planning notes per event
  - Link to Google Group (chat/discussion)
- [ ] Admin can create/configure activity groups
- [ ] Nav: "Activities ▾" dropdown in internal nav, visible to overall leaders + admin; lists groups they lead

#### Pending — Phase 2 (enhancements)

- [ ] Recurring event auto-generation — create all 4th-Saturday events for a calendar year in one action
- [ ] Monthly leader rotation — notify designated leader by email when they are assigned
- [ ] Public-facing activity page — opt-in form for members who aren't logged in (requires member email lookup, same pattern as event registration)
- [ ] In-app planning discussion thread per event (if Google Groups proves insufficient)

#### Decisions needed

| Question | Recommendation |
|---|---|
| Who can opt in — self-service or leader-managed? | Both: leaders manage the list, but members can self-opt from their profile |
| Is "monthly leader" per calendar month or per specific event? | Per event — more flexible, handles cancellations and schedule shifts |
| Google Groups vs. in-app chat | Keep Google Groups for now; link from dashboard; revisit if usage shows it's insufficient |
| Nav placement | New "Activities ▾" dropdown (not under VP Membership) — activity groups may span multiple officer roles over time |
| Multiple activity groups eventually? | Yes — build generic from the start; Drop-In Saturday is just the first instance |

---

## Open Questions / Items for Discussion

| # | Topic | Summary |
|---|---|---|
| 1 | Long-term maintenance by non-technical admins | Admin UI covers routine content (settings, blocks, members, events). Structural changes (new pages, new fields, nav) should be delegated to Claude Code via plain-English requests. See [MAINTENANCE.md](MAINTENANCE.md) for draft guide and open questions. Key decisions needed: production server choice, remote access method, Claude Code licensing, and who fills the maintainer role. |
| 2 | Process Library — editing model | **Decided:** file-based only (Claude Code). Officers request changes via plain-English; no in-app editor needed. |
| 3 | Process Library — public visibility | **Decided:** public only where necessary (e.g., renewal instructions). Officer-only by default. |

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
