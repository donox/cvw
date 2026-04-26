# CVW System Maintenance Guide

**Status: Draft for discussion — not yet operational.**
This document is intended to support executive understanding and discussion of the path forward for long-term system maintenance. All procedures and examples are hypothetical until production deployment details are finalised.

---

## Index

- [Purpose](#purpose)
- [Two Kinds of Maintenance](#two-kinds-of-maintenance)
- [Site Settings — How They Work](#site-settings--how-they-work)
- [What Is Claude Code?](#what-is-claude-code)
- [Who Should Be the Maintainer?](#who-should-be-the-maintainer)
- [Hypothetical Example: Making a Change](#hypothetical-example-making-a-change)
- [Hypothetical Example: Correcting Content Not in the Admin Console](#hypothetical-example-correcting-content-that-is-not-in-the-admin-console)
- [What the Non-Technical Maintainer Model Handles Well](#what-the-non-technical-maintainer-model-handles-well)
- [Where the Model Has Gaps — When a Developer Is Needed](#where-the-model-has-gaps--when-a-developer-is-needed)
- [Recommended Maintenance Model](#recommended-maintenance-model)
- [What Claude Code Cannot Do](#what-claude-code-cannot-do-without-extra-steps)
- [Backup and Recovery](#backup-and-recovery)
- [Open Questions](#open-questions-requiring-decision-before-this-guide-is-operational)
- [Summary](#summary)

---

## Purpose

The CVW membership system is a custom web application. Unlike a hosted platform (WordPress, Wild Apricot), it runs on a server we control and is maintained by editing code files. This gives full control over features and data, but it means someone must be able to make changes when they are needed.

This guide describes how that maintenance can be done by a non-technical officer using **Claude Code** — an AI assistant that understands the codebase and can make changes based on plain-English requests.

---

## Two Kinds of Maintenance

### 1. Routine Content — No Technical Help Needed

These tasks are handled entirely through the internal admin console at `/admin/`. No code changes, no restart, no Claude Code required.

| Task | Where |
|---|---|
| Update meeting time, location, or format | Admin → Site Content → Settings |
| Update annual dues amounts | Admin → Site Content → Settings |
| Edit narrative text on About or Skill Center pages | Admin → Site Content → Content Blocks |
| Add or edit calendar events | Exec → Schedule |
| Add or edit programs | Programs console |
| Manage members | Membership console |
| Add or edit resources (links library) | Volunteer → Library |
| Send email to members | Email console |
| Manage users and passwords | Admin → Users |

### 2. Structural Changes — Use Claude Code

These tasks require editing the application code. Examples include:

- Adding a new page to the public website
- Adding a new field to the membership form
- Changing the navigation menu structure
- Adding a new type of report
- Creating a new officer role or permission
- Changing how something looks or is laid out

For these, a designated maintainer opens a conversation with Claude Code, describes what is needed in plain English, and Claude Code makes the changes. No programming knowledge is required to describe the task — only the ability to say clearly what you want.

---

## Site Settings — How They Work

The **Admin → Site Content → Settings** page shows editable values such as meeting time, location, and dues amounts. These values are pre-defined in code and seeded into the database on first startup. **You can edit them freely in the UI, but you cannot add new settings there — the UI has no "Add" button.**

To add a new setting (e.g. a new dues category or a configurable label that appears on the public site):

1. Ask Claude Code: *"Add a site setting for X with label Y and default value Z."*
2. Claude Code adds it to the seed list in `app/main.py` and any templates that use it.
3. On next startup the new setting appears automatically in the Settings page for editing.

This also applies to **Content Blocks** (the narrative text sections on About, Skill Center, etc.) — new blocks must be defined in code, then they become editable in the UI.

---

## What Is Claude Code?

Claude Code is a command-line tool made by Anthropic (the company behind the Claude AI). It runs on the same computer as the CVW application, reads the codebase, and can edit files, run migrations, and test that changes work — all based on a plain-English description of the task.

A typical session looks like:

> *"Add a phone number field to the public membership application form."*

Claude Code will find the relevant files, make the changes, update the database if needed, and confirm when it is done. The maintainer reviews the result in a browser and approves or asks for adjustments.

Claude Code is not a general chatbot — it is specifically designed for working inside a software project. It has full context of the CVW codebase and understands how all the pieces fit together.

---

## Who Should Be the Maintainer?

The maintainer does not need to be a programmer. They need to be:

- Comfortable using a terminal (command line) for basic commands
- Able to describe clearly what they want changed
- Willing to review the result in a browser and give feedback
- Able to follow a short checklist to restart the server after changes

Ideally this is the same person who manages the server (see Production Deployment, below). It could be a technically inclined officer, a club member who volunteers for the role, or a contracted helper.

---

## Hypothetical Example: Making a Change

*The following is illustrative only. Exact commands depend on the production environment.*

**Scenario:** The club wants to add a "How did you hear about us?" field to the public membership application.

**Step 1 — Open a terminal on the server and navigate to the project:**
```bash
cd /path/to/cvwdata
source .venv/bin/activate
```

**Step 2 — Start Claude Code:**
```bash
claude
```

**Step 3 — Describe the task:**
```
Add an optional "How did you hear about us?" text field to the public
membership application form. Store it on the member record. It does not
need to appear anywhere in the internal member list, just be saved.
```

**Step 4 — Review the changes:**
Claude Code will describe what it changed and why. Open the application in a browser and test the form.

**Step 5 — Restart the server** so changes take effect:
```bash
# Hypothetical — exact command depends on production setup
sudo systemctl restart cvw
```

---

## Hypothetical Example: Correcting Content That Is Not in the Admin Console

*Scenario: The "Guests are always welcome" line on the About page needs to be changed.*

Some wording is built into the page templates rather than stored in the content editor. For these, Claude Code can make the change directly:

```
On the public About page, change "Guests are always welcome to attend a
meeting before deciding to join" to "Visitors are welcome to attend up
to two meetings before being asked to join."
```

Claude Code finds the template file, makes the edit, and confirms. No database change or migration is needed — restart is still required for the change to appear.

---

## What the Non-Technical Maintainer Model Handles Well

The terminal + Claude Code model works well when:

- The result is visible and testable in a browser ("does it look right, does it work?")
- The task is specific and well-described ("add this field", "change this wording")
- Errors produce an obvious symptom — a broken page, a form that fails

Claude Code reads and understands the full codebase itself. The maintainer's role is to describe the goal and evaluate the outcome. Code visibility is not required for this.

---

## Where the Model Has Gaps — When a Developer Is Needed

These categories represent residual risk that cannot be fully handled by a non-technical maintainer alone, even with Claude Code:

**1. Dependency and platform aging**
Python versions reach end-of-life. Libraries release security patches or breaking changes. These need periodic attention — not necessarily an emergency, but they accumulate if ignored. Someone needs to notice and decide to act. Claude Code can execute the updates once directed; the gap is awareness and timing judgment. *Suggested mitigation: annual developer review.*

**2. Silent data integrity problems**
A bug that corrupts data without producing a visible browser error is the hardest failure mode to catch without code visibility. *Suggested mitigation: automated daily database backups and periodic spot-checks — operational discipline rather than code skill.*

**3. Security vulnerabilities**
A vulnerability in a dependency (the codebase already has one precedent: a `bcrypt` version incompatibility) may require understanding tradeoffs before acting. Claude Code can implement a fix; someone needs to recognise the severity. *Suggested mitigation: subscribe to Python security advisories or rely on annual developer touchpoint.*

**4. Poorly framed requests producing bad results**
Claude Code is reliable for small, specific requests. Vague or large requests carry higher risk of a change that works superficially but causes problems later — and without code visibility, the maintainer cannot catch this. *Suggested mitigation: the maintenance guide (this document) coaches the maintainer toward small, incremental, specific requests.*

**5. Catastrophic application failure**
If the application stops starting entirely — due to a bad migration, a broken import, or a corrupted file — the maintainer needs to either describe the error precisely to Claude Code or escalate to a developer. All changes are tracked in git, so recovery is always possible; the question is whether the maintainer can execute it. *Suggested mitigation: developer available as emergency contact; git backup of all code.*

---

## Recommended Maintenance Model

| Frequency | Who | What |
|---|---|---|
| Daily / as needed | Non-technical maintainer | Admin console tasks (content, members, events, email) |
| As needed | Non-technical maintainer + Claude Code | Feature requests, wording changes, structural updates |
| Annual | Developer (brief engagement) | Dependency review, security patches, backup verification, review of accumulated changes |
| Emergency | Developer on-call | Application failure, data corruption, security incident |

This is sustainable for a club application at CVW's scale — low traffic, known user base, infrequent structural changes. The developer touchpoint is a periodic consultant relationship, not ongoing support.

---

## What Claude Code Cannot Do (Without Extra Steps)

- **Deploy to a live server remotely** — it runs on the machine where the code lives; remote access (SSH) is a prerequisite
- **Send emails on its own** — email configuration is in the `.env` file and must be set up separately
- **Guarantee correctness** — changes should always be reviewed in a browser before considering them done; the maintainer is the final check
- **Roll back automatically** — if a change causes a problem, recovery requires either describing the fix to Claude Code or using `git` to revert (a technical step)

---

---

## Backup and Recovery

### Automatic Backups

The system creates a backup of the database automatically every night at 2:00 AM. Backups are stored in the `data/backups/` folder on the server as timestamped files (e.g., `cvw_20260317_020000.db`). By default the 30 most recent backups are kept; older ones are deleted automatically.

Backups use SQLite's internal backup mechanism and are safe to create while the server is running.

### Admin Console — Normal Operations

All backup management is available at **Admin → Backups** (`/admin/backup/`):

| Action | How |
|---|---|
| See backup status | Admin → Backups — shows last backup, next scheduled, count stored |
| Create a backup immediately | Admin → Backups → "Create Backup Now" |
| Change how many backups to keep | Admin → Backups → retention setting |
| Download a backup for off-site storage | Admin → Backups → Download button next to any backup |
| Restore from a backup | Admin → Backups → Restore button, then restart the server |

**Good practice:** create a manual backup before making any significant changes, and download a copy to a safe location (e.g., a club Google Drive folder) regularly.

### Restoring from the Admin Console

1. Go to Admin → Backups
2. Find the backup you want to restore and click **Restore**
3. Confirm the dialog
4. The console will show a yellow warning: *"A restore is staged. Restart the server to apply."*
5. Restart the server (see restart procedure for your deployment)
6. Verify the application is working correctly after restart

The restore is staged rather than applied immediately so that a restart is always the final confirmation step. Nothing is overwritten until the server restarts.

### Emergency Restore — When the Console Is Unavailable

If the application is not starting or the admin console cannot be reached, use the standalone restore script from a terminal on the server.

**Stop the server first**, then:

```bash
# List available backups
python scripts/restore.py

# Restore the most recent backup
python scripts/restore.py --latest

# Restore a specific backup
python scripts/restore.py cvw_20260317_020000.db
```

The script automatically saves a safety copy of the current database as `pre_restore_safety.db` before overwriting, in case you need to reverse the restore.

After running the script, start the server normally.

### Creating a Backup Without the Console

```bash
python scripts/backup.py
```

This is safe to run while the server is running. Use `--keep N` to retain a specific number of backups.

### Off-Site Storage

The `data/backups/` folder is on the server. If the server is lost or corrupted, these backups are also lost. **Regularly download backup files** from the admin console and store them somewhere independent (club Google Drive, an officer's computer, etc.). The frequency depends on how often data changes — weekly downloads are a reasonable minimum.

### Backup Strategy Summary

| Setting | Value |
|---|---|
| Schedule | Daily at 2:00 AM (America/New_York) |
| Location | `data/backups/` on the server |
| Format | SQLite database file (directly usable) |
| Retention | 30 most recent (configurable in admin console) |
| Off-site | Manual download — admin should download regularly |
| Emergency restore | `scripts/restore.py` from terminal |

---

## Open Questions Requiring Decision Before This Guide Is Operational

1. **Production server** — Where will the application run? (VPS, club-owned machine, cloud hosting?) This determines how the maintainer accesses it.
2. **Remote access** — Will the maintainer work directly on the server machine, or remotely via SSH?
3. **Claude Code licensing** — Claude Code requires an Anthropic account and API usage fees (or a Claude Pro/Max subscription). Who pays and manages this account?
4. **Maintainer role** — Who fills this role? Is it an officer position, a volunteer role, or contracted?
5. **Restart procedure** — The exact command to restart the application depends on how it is deployed (systemd service, Docker, screen session, etc.).
6. **Backup and recovery** — The SQLite database file (`data/cvw.db`) is the single source of truth for all club data. A backup strategy must be in place before production use.
7. **Git and version control** — Changes made by Claude Code are tracked in git. Pushing to GitHub and understanding how to revert a bad change requires at minimum a one-time setup and brief orientation.

---

## Summary

| Situation | Action | Technical skill needed |
|---|---|---|
| Update meeting info or dues | Admin console | None |
| Edit About / Skill Center text | Admin console | None |
| Add a new feature or page | Describe to Claude Code | Minimal (terminal, browser review) |
| Fix a broken page | Describe to Claude Code | Minimal |
| Recover from a bad change | Git revert or describe fix to Claude Code | Low–moderate |
| Deploy to production | Follow deployment runbook (TBD) | Moderate (one-time setup) |
