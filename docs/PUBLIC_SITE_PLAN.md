# Option A — CVW Public Website Integrated with CVWdata

**Status:** Phase 1 live at `/site/` — Phase 2 pending officer discussion
**Last updated:** 2026-03-15

---

## Concept

Replace the current WordPress site at centralvawoodturners.org with public-facing pages served directly from the CVWdata FastAPI application. The internal officer consoles remain behind login; public pages are open to all. One codebase, one server.

---

## Current Site Inventory

The existing WordPress site (centralvawoodturners.org) has the following pages:

| Page | Type | Notes |
|---|---|---|
| Home | Static | Club intro, next meeting, schedule summary |
| Club Information | Semi-dynamic | Officers list, meeting location, downloadable PDFs |
| Membership Application | Form | Contact Form 7 — already replaced by `/apply` |
| Membership Dues & Donations | Static | Tier descriptions + PayPal buttons |
| Newsletters | Archive | Monthly PDFs going back to 2004 |
| Member's Gallery | Media | ~41 images across 8 members, lightbox view |
| Members Only | Protected | WordPress password page — content unknown |
| Calendar of Events | Manual table | One page per year, 12 meetings + skill sessions |
| Upcoming Meeting | Semi-dynamic | Updated manually before each meeting |
| Skill Center & Mentoring | Static | Session schedule, contact info |
| Resources | Static links | ~15 categories, PDFs/links/videos |
| Contact Us | Form | Multi-select officer dropdown, Contact Form 7 |
| Virginia Woodturning Symposium | Static | Annual event info, volunteer opportunities |

---

## What CVWdata Already Covers

| Feature | Current status |
|---|---|
| Membership application | ✅ `/apply` — public, fully functional |
| Officers list | ✅ In DB, needs public route |
| Program/meeting calendar | ✅ OrgEvent model exists, needs public route |
| Dues payment tiers | ❌ Static page needed |
| Member feedback (QR) | ✅ `/programs/{id}/feedback` — public |

---

## Proposed Public Pages

All new routes would use a `public` or `www` prefix (or no prefix) and require no login.

### Phase 1 — ✅ Complete (live at `/site/`)

| Route | Description | Status |
|---|---|---|
| `/site/` | Home — next program + upcoming events | ✅ Live |
| `/site/about` | Club info, mission, meeting location | ✅ Live |
| `/site/officers` | Current officers and volunteer staff | ✅ Live |
| `/site/calendar` | Upcoming events / meeting schedule | ✅ Live |
| `/site/next-meeting` | Programs with `show_on_public` flag | ✅ Live |
| `/apply` | Membership application | ✅ Pre-existing |
| `/site/contact` | Contact page (static, no form submission yet) | ✅ Live |
| `/site/skill-center` | Skill session info (static) | ✅ Live |

Notes:
- Uses `base_public.html` with CVW brown/tan palette, mobile-responsive
- Next Meeting page driven by `Program.show_on_public` flag (toggled on program list)
- Contact form does not yet submit email (Phase 2)

### Phase 2 — Medium effort

| Route | Description | Notes |
|---|---|---|
| `/newsletters` | PDF archive list by year/month | Requires PDF upload management |
| `/site/resources` | Curated link library by category | YAML-driven (see below) |
| `/gallery` | Member photo gallery | Requires image upload + storage |
| `/symposium` | Virginia Woodturning Symposium info | Static or linked |
| `/dues` | Membership tiers + PayPal integration | PayPal Buttons API |
| `/members-only` | Protected content for logged-in members | Auth already exists |

#### Resources page approach

The existing WordPress Resources page has ~15 categories of links (PDFs, videos, external websites). The proposed approach:

- **Storage: YAML file** (`data/resources.yaml`). Each entry has a category, title, URL, and optional description. Example:

  ```yaml
  - category: "Getting Started"
    title: "AAW Turning Fundamentals"
    url: "https://example.com/fundamentals"
    description: "Introductory video series from the AAW"

  - category: "Wood Sources"
    title: "Local suppliers list (PDF)"
    url: "/static/pdfs/wood_sources.pdf"
  ```

- **Why YAML, not a DB table:** Resources change infrequently (a few times a year). YAML is human-editable by any officer with file access, version-controlled in git, and requires no admin UI to manage. A DB table would add a full CRUD console for minimal benefit at CVW's scale.

- **The `/site/resources` route** reads the YAML file at request time, groups entries by category, and renders them. No migration needed.

- **PDFs:** Linked PDFs are stored in `static/pdfs/` and served by FastAPI's StaticFiles mount. Uploading new PDFs requires server file access (same as editing YAML) — deferred to Phase 3 if an upload UI is needed.

- **Who maintains it:** Any officer or developer with git access edits `data/resources.yaml` and redeploys. If a browser-based editor is needed later, a simple admin CRUD UI can be added without changing the public route.

---

### Phase 3 — Deferred / Complex

| Feature | Notes |
|---|---|
| PayPal dues payment | Requires PayPal developer account, webhook for payment confirmation, auto-update dues_paid on Member |
| Newsletter upload tool | Admin UI to upload PDFs and publish to archive |
| Gallery submission | Members submit photos; admin approves |
| Email contact routing | Contact form emails correct officer by role; requires SMTP config |
| Zoom link management | Store and display Zoom credentials per meeting |

---

## Technical Approach

### Templates
Public pages would use a new `base_public.html` — same CVW brown branding but without the internal nav bar. Wider max-width, more visual, suitable for public visitors including non-members.

### Design
- Keep CVW brown/tan palette
- Responsive layout (mobile-friendly for members at meetings using QR codes)
- Print-friendly styles for meeting agendas and skills session info
- Separate from the internal console look — less utilitarian, more welcoming

### Static assets
Images, PDFs, and gallery photos would be served from a `static/` directory. FastAPI's `StaticFiles` mount handles this.

### Email (Contact form)
Use Python's `smtplib` or `fastapi-mail` with SMTP credentials in `.env`. Route contact form submissions to the correct officer's email based on their role in the Officer table.

### Domain / Hosting
- Point centralvawoodturners.org DNS to the new server
- Run behind nginx or Caddy for HTTPS (Let's Encrypt)
- Keep the WordPress site live until the new site is fully ready, then cut over

---

## Open Questions for Officer Discussion

1. **Who maintains content?** Static pages (About, Skill Center, Resources) need someone to update them. With FastAPI/Jinja2 this means editing template files — not as easy as WordPress. A lightweight CMS layer or editable DB fields could help.

2. **Newsletter archive migration** — 20+ years of PDFs need to be organized and uploaded. Is this worth doing, or link to the existing WordPress archive during transition?

3. **Member gallery** — Does the club want to continue this? Who approves submitted photos? What's the storage strategy?

4. **PayPal integration** — Treasurer needs to be involved. PayPal webhooks require a publicly accessible server, so this can't be tested locally.

5. **Members-only content** — What is currently behind the WordPress password? This determines the scope of the protected area.

6. **Timeline** — Phase 1 could be prototyped quickly for discussion. Full cutover to replace WordPress would require officer sign-off and a transition plan.

---

## Suggested Next Steps

1. **Review Phase 1** — Walk through the live `/site/` pages with officers. Get feedback.
2. **Decide on Phase 2 priorities** — Newsletters and gallery require the most effort; resources and dues page are simpler.
3. **Decide on content ownership** — Static pages (About, Skill Center, Resources) need someone to update them. With FastAPI/Jinja2 this means editing template files — not as easy as WordPress.
4. **Set a cutover target** — If approved, aim to replace the WordPress site after Phase 2 is at least 80% complete.

---

## Dependencies on CVWdata Backlog

Completing this plan depends on:
- OrgEvent model being used consistently for all meetings and events
- Officer data being kept current in the DB (already seeded)
- A production hosting environment (Docker + domain)
- SMTP credentials for contact form email routing
