# Option A — CVW Public Website Integrated with CVWdata

**Status:** Proposed — under discussion
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

### Phase 1 — Low effort, high value

| Route | Description | Data source |
|---|---|---|
| `/` (redesigned) | Home — next meeting, club intro | OrgEvent, static text |
| `/about` | Club info, mission, meeting location | Static + Officers DB |
| `/officers` | Current officers and volunteer staff | Officer model (already seeded) |
| `/calendar` | Upcoming events / meeting schedule | OrgEvent model |
| `/next-meeting` | Next single meeting detail with agenda | OrgEvent model |
| `/apply` | Membership application | ✅ Already exists |
| `/contact` | Contact form routing to officers by role | Static form + email |
| `/skill-center` | Skill session info | Static page |

### Phase 2 — Medium effort

| Route | Description | Notes |
|---|---|---|
| `/newsletters` | PDF archive list by year/month | Requires PDF upload management |
| `/resources` | Curated link library by category | DB-backed or YAML-driven |
| `/gallery` | Member photo gallery | Requires image upload + storage |
| `/symposium` | Virginia Woodturning Symposium info | Static or linked |
| `/dues` | Membership tiers + PayPal integration | PayPal Buttons API |
| `/members-only` | Protected content for logged-in members | Auth already exists |

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

1. **Discuss with officers** — Share this plan at an executive meeting. Get buy-in before building.
2. **Prototype Phase 1** — Build the public home, officers, and calendar pages as a prototype running alongside the internal app. Low risk, useful for demonstrating the concept.
3. **Decide on content ownership** — Identify who owns each section and how they'll update it.
4. **Set a cutover target** — If approved, aim for a cutover date after Phase 1 is stable and Phase 2 is at least 80% complete.

---

## Dependencies on CVWdata Backlog

Completing this plan depends on:
- OrgEvent model being used consistently for all meetings and events
- Officer data being kept current in the DB (already seeded)
- A production hosting environment (Docker + domain)
- SMTP credentials for contact form email routing
