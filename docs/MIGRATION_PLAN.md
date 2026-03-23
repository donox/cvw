# Domain & Hosting Migration Plan

## Current State

- Domain: `centralvawoodturners.org` registered at GoDaddy
- Public website: WordPress hosted at GoDaddy
- Membership app: this FastAPI/SQLite app, not yet publicly hosted

## Target State

- Domain transferred to Cloudflare
- Single VPS (DigitalOcean or Linode) running the FastAPI app via Docker
- WordPress eliminated — public pages served by this app
- `centralvawoodturners.org` → public-facing pages (home, events, contact, etc.)
- Members-only admin area served from the same app (path or subdomain TBD)

## Rationale

- The FastAPI app already has public-facing routes (home, contact, events)
- Consolidating into one app removes a second system to maintain and secure
- Cloudflare provides better DNS tooling, DDoS protection, and at-cost .org renewals (~$10/yr)
- Docker-based deployment is already in place

## WordPress Content to Migrate

Known content on the current WordPress site that requires human review and disposition decisions:

- **Newsletters** — archive of past newsletters; decide whether to host as static files, a simple list page, or link to external storage (e.g. Google Drive)
- **Photos** — gallery content; decide whether to host on the VPS, link to an external photo service, or omit
- **Other pages** — review each page and decide: port as static template, replace with a DB-driven template, or retire

Some content may be better replaced by live data already in the database (e.g. an events page driven by the events model rather than a static WordPress page).

**This review requires human decisions and should happen before cutover is scheduled.**

## Migration Strategy: Temporary Domain

To avoid disrupting the live WordPress site during development and testing, the new app will be deployed first under a temporary domain (e.g. a cheap `.com` or a subdomain of a domain we control). This allows:

- Full end-to-end testing in production conditions
- Content review and porting without time pressure
- A fixed, planned cutover date when everything is verified

Cutover sequence:
1. New app is live and fully reviewed on temporary domain
2. Transfer `centralvawoodturners.org` to Cloudflare
3. Update DNS to point to VPS — WordPress goes offline
4. Verify new site, cancel GoDaddy hosting

## Migration Steps

### 1. Content audit
- Walk through the current WordPress site page by page
- For each item decide: port as static template | replace with DB-driven page | host as file | retire
- Track decisions in a simple checklist (can be added here or in a separate doc)

### 2. Provision VPS
- Create a small VPS (DigitalOcean Droplet or Linode, ~$6-12/mo)
- Install Docker and Docker Compose
- Clone repo, configure `.env` for production (DATABASE_URL, APP_TITLE, etc.)

### 3. Set up SSL and reverse proxy on temporary domain
- Use Caddy (recommended) or Nginx + Certbot as a reverse proxy
- Caddy handles Let's Encrypt SSL automatically
- Point temporary domain DNS at VPS, confirm SSL and app are working

### 4. Port WordPress content
- Build out missing public templates (newsletters, photos, etc.) per audit decisions
- Load any structured content (events, officers, etc.) into the database

### 5. Transfer domain to Cloudflare
- Unlock domain at GoDaddy, get transfer authorization code
- Initiate transfer at cloudflare.com/registrar
- Transfer takes up to 7 days; DNS continues working during transfer

### 6. Cutover
- Set DNS TTL low (5 min) a day before cutover for fast propagation
- Update `centralvawoodturners.org` A record to VPS IP
- Add `www` CNAME → `centralvawoodturners.org`
- Confirm SSL cert issued and site loads correctly
- Cancel GoDaddy hosting plan

## Open Questions

- Temporary domain name to use during staging
- Subdomain strategy for final site: single domain with path-based routing vs. `app.` subdomain for admin area
- Where to host photos/newsletters: on VPS, Google Drive, or a static file service
- Who will administer the VPS
