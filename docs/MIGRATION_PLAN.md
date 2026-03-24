# Domain & Hosting Migration Plan

## Current State

- Domain: `centralvawoodturners.org` registered at GoDaddy
- Public website: WordPress hosted at GoDaddy
- Membership app: this FastAPI/SQLite app, not yet publicly hosted

## Target State

- Dev instance live at `cvwdev.org` (or similar) for content review and testing
- Production cutover: `centralvawoodturners.org` transferred to Cloudflare, DNS pointed at VPS
- WordPress eliminated — all public pages served by this app
- Members-only admin area served from the same app (path or subdomain TBD)
- Option to retain `cvwdev.org` as a permanent staging environment after go-live

## Rationale

- The FastAPI app already has public-facing routes (home, contact, events)
- Consolidating into one app removes a second system to maintain and secure
- Cloudflare provides better DNS tooling, DDoS protection, and at-cost .org renewals (~$10/yr)
- Docker-based deployment is already in place
- Dev domain allows full end-to-end testing without touching the live WordPress site

## WordPress Content to Migrate

Known content on the current WordPress site that requires human review and disposition decisions:

- **Newsletters** — archive of past newsletters; hosting as static PDFs is already implemented
- **Photos** — gallery content; decide whether to host on the VPS, link to an external photo service, or omit
- **Other pages** — review each page and decide: port as static template, replace with a DB-driven template, or retire

Some content may be better replaced by live data already in the database (e.g. an events page driven by the events model rather than a static WordPress page).

**This review should happen on the dev instance before cutover is scheduled.**

---

## Phase 1 — Dev Instance Setup (cvwdev.org)

> Goal: get the app running live at cvwdev.org so content work and testing can proceed.

- [x] **1.1** Check availability of `cvwdev.org` at cloudflare.com/registrar
- [x] **1.2** Register `cvwdev.org` on Cloudflare (~$10/yr)
- [x] **1.3** Provision a VPS — DigitalOcean Droplet, Ubuntu 24.04 LTS, $6/mo — IP: `104.236.111.180`
- [x] **1.4** SSH in, install Docker and Docker Compose
- [x] **1.5** Install Caddy as reverse proxy (`apt install caddy`)
- [x] **1.6** Clone repo to VPS; create `.env` from `.env.example` with production values
- [x] **1.7** Run `docker-compose up -d`; confirm app starts
- [x] **1.8** Add `A` record in Cloudflare DNS: `cvwdev.org` → VPS IP
- [x] **1.9** Add `A` record: `www.cvwdev.org` → VPS IP
- [x] **1.10** Configure Caddyfile for `cvwdev.org` (see snippet below); reload Caddy
- [x] **1.11** Confirm site loads at `https://cvwdev.org` with valid SSL
- [x] **1.12** Set `SESSION_SECRET` and other secrets in `.env`; restart app
- [x] **1.13** Create admin user; log in and verify all app sections work

**Caddy config snippet** (`/etc/caddy/Caddyfile`):
```
cvwdev.org, www.cvwdev.org {
    reverse_proxy localhost:8000
}
```

---

## Phase 2 — Content Review & Porting

> Goal: make the dev site a complete replacement for the WordPress site.

- [ ] **2.1** Walk through current WordPress site page by page; document each item in a content checklist
- [ ] **2.2** Port or retire static pages (About, etc.) — compare WordPress copy to existing templates
- [ ] **2.3** Upload newsletter PDFs to `app/static/newsletters/` on the VPS
- [ ] **2.4** Decide on photo gallery: host on VPS | link to external service | omit for now
- [x] **2.5** Enter current officers and events into the database via the exec console — imported from local dev db via `scp` + `docker compose cp`
- [ ] **2.6** Review and approve all public-facing pages on `cvwdev.org`
- [ ] **2.7** Configure SMTP in `.env`; test contact form end-to-end
- [ ] **2.8** Configure member site password; test members-only pages
- [ ] **2.9** Set up automated database backups (already built-in — verify schedule in admin console)
- [ ] **2.10** Get sign-off from at least one other officer that the site is ready

---

## Phase 3 — Production Cutover

> Goal: move `centralvawoodturners.org` to this app; WordPress goes dark.

- [ ] **3.1** Lower TTL on `centralvawoodturners.org` DNS to 5 minutes (do this ~24 hrs before cutover)
- [ ] **3.2** Unlock domain at GoDaddy; obtain transfer authorization code
- [ ] **3.3** Initiate transfer to Cloudflare (cloudflare.com/registrar) — takes up to 7 days
- [ ] **3.4** Once transfer completes, add DNS records in Cloudflare: `centralvawoodturners.org` → VPS IP
- [ ] **3.5** Update Caddyfile to add `centralvawoodturners.org` alongside or replacing `cvwdev.org`
- [ ] **3.6** Confirm `https://centralvawoodturners.org` loads correctly with valid SSL
- [ ] **3.7** Verify contact forms, member login, and event registration work on the production domain
- [ ] **3.8** Cancel GoDaddy hosting plan (keep domain transfer window in mind — don't cancel before transfer)
- [ ] **3.9** Decide: retire `cvwdev.org` or retain as permanent staging environment

---

## Open Questions

- Subdomain strategy for final site: single domain with path-based routing vs. `app.` subdomain for the admin area
- Where to host photos: on VPS, Google Drive, or a static file service
- Who will have SSH access to administer the VPS
- Retain `cvwdev.org` post-cutover as staging? (Recommended if ongoing development continues)
