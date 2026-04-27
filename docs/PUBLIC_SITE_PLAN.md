# Option A — CVW Public Website Integrated with CVWdata

**Status:** Phase 1 live at `/site/` — Phase 2 in progress
**Last updated:** 2026-04-27

---

## Index

- [Concept](#concept)
- [Current Site Inventory](#current-site-inventory)
- [What CVWdata Already Covers](#what-cvwdata-already-covers)
- [Proposed Public Pages](#proposed-public-pages)
  - [Phase 1 — Complete](#phase-1---complete-live-at-site)
  - [Phase 2 — Medium effort](#phase-2--medium-effort)
  - [Phase 3 — Deferred / Complex](#phase-3--deferred--complex)
- [Content Migration from WordPress](#content-migration-from-wordpress)
  - [Content Classification](#content-classification)
  - [Members Nav Dropdown](#members-nav-dropdown)
  - [Migration Process](#migration-process)
- [Technical Approach](#technical-approach)
- [Open Questions for Officer Discussion](#open-questions-for-officer-discussion)
- [Suggested Next Steps](#suggested-next-steps)
- [Dependencies on CVWdata Backlog](#dependencies-on-cvwdata-backlog)

---

## Concept

Replace the current WordPress site at centralvawoodturners.org with public-facing pages served directly from the CVWdata FastAPI application. The internal officer consoles remain behind login; public pages are open to all. One codebase, one server.

[↑ Index](#index)

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

[↑ Index](#index)

---

## What CVWdata Already Covers

| Feature | Current status |
|---|---|
| Membership application | ✅ `/apply` — public, fully functional |
| Officers list | ✅ In DB, needs public route |
| Program/meeting calendar | ✅ OrgEvent model exists, needs public route |
| Dues payment tiers | ❌ Static page needed |
| Member feedback (QR) | ✅ `/programs/{id}/feedback` — public |

[↑ Index](#index)

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
| `/site/resources` | Curated link library by category | ✅ Live — DB-backed, managed via Librarian console |
| `/gallery` | Member photo gallery | Requires image upload + storage |
| `/symposium` | Virginia Woodturning Symposium info | Static or linked |
| `/dues` | Membership tiers + PayPal integration | PayPal Buttons API |
| `/members-only` | Per-page access restriction + shared member password | ✅ Live — see below |

#### Members-only access — implemented

**Status:** ✅ Live.

The WordPress site had a single password-protected page. The approach here is more flexible:

- **`PublicPage` model** — one DB row per public page, each with a `members_only` bool flag. Seeded with all current pages; all start as unrestricted (open).
- **Shared member password** stored as a `SiteSetting` (`member_site_password`). Visitors enter this password at `/site/login`; the session is marked `member_site_authed`.
- **Admin UI** at `/admin/content/access` — checkboxes to toggle each page + password field.
- **Internal officers** (anyone logged into the officer console) bypass the member login automatically.
- No per-member accounts are needed for public access; a single club-wide password is sufficient at CVW scale.

There is no dedicated `/members-only` URL — any page can be restricted. The "Members Only" area is whatever the admin marks as restricted.

#### Per-event registration restriction — implemented

**Status:** ✅ Live.

Some events (especially monthly meetings) allow visitor in-person attendance but restrict Zoom to members. Others may be members-only entirely. A single `registration_restriction` field on `OrgEvent` covers both cases:

| Value | Behaviour |
|---|---|
| `None` (default) | Open to all |
| `zoom_members_only` | Visitors can register In Person only; Remote option disabled in form and rejected server-side |
| `members_only` | Visitor option hidden from registration form; server rejects visitor submissions |

- Set per event via the exec event form (dropdown in the Registration fieldset).
- Calendar and Upcoming Events pages show "Members Only" badge and Zoom qualifier where applicable.
- Designed for the monthly meeting: Zoom is members-only, in-person is open.

#### Resources page — implemented

**Status:** ✅ Live. 93 resources seeded from the WordPress site across 14 categories.

The initial plan proposed a YAML file (`data/resources.yaml`) on the grounds that resources change infrequently and YAML is version-controlled without needing an admin UI. This was **rejected** after discussion:

- A "simple editor" that lets officers edit raw YAML still requires YAML knowledge and correct indentation — not suitable for a non-technical librarian.
- A form-per-entry browser editor (add/edit/delete individual resources) is equivalent in UI work whether the backing store is YAML or a DB table. The DB version is more robust and fits the existing app patterns.
- The marginal savings of YAML (one migration, one model file) did not outweigh the usability cost.

**Actual approach:** `Resource` DB table (category, title, url, description, sort_order, active) managed via the Librarian console at `/librarian/resources/`. The `librarian` role and a "Volunteer ▾" nav dropdown were added at the same time to support future volunteer-role consoles.

[↑ Index](#index)

---

### Phase 3 — Deferred / Complex

| Feature | Notes |
|---|---|
| PayPal dues payment | Requires PayPal developer account, webhook for payment confirmation, auto-update dues_paid on Member |
| Newsletter upload tool | Admin UI to upload PDFs and publish to archive |
| Gallery submission | Members submit photos; admin approves |
| Email contact routing | Contact form emails correct officer by role; requires SMTP config |
| Zoom link management | Store and display Zoom credentials per meeting |

[↑ Index](#index)

---

## Content Migration from WordPress

Migrate content from centralvawoodturners.org in three buckets based on type and age.

[↑ Index](#index)

### Content Classification

| WordPress Page | Bucket | Destination | Status |
|---|---|---|---|
| Home | Public | `/site/` | ✅ Done |
| Club Information (officers, location) | Public | `/site/about`, `/site/officers` | ✅ Done |
| Membership Application | Public | `/apply` | ✅ Done |
| Calendar of Events | Public | `/site/calendar` | ✅ Done |
| Upcoming Meeting | Public | `/site/upcoming-events` | ✅ Done |
| Skill Center & Mentoring | Public | `/site/skill-center` | ✅ Done |
| Resources | Public | `/site/resources` | ✅ Done |
| Contact Us | Public | `/site/contact` | ✅ Done |
| Membership Dues & Donations | Public | `/site/dues` — Phase 2 | ⬜ Pending |
| Virginia Woodturning Symposium | Public | `/site/symposium` — static page | ⬜ Pending |
| Newsletters — current 2 years | Members | `/site/newsletters` — members_only | ⬜ Pending |
| Newsletters — older than 2 years | Archive | Google Drive: `CVW Club Files/Newsletters/` | ⬜ Pending |
| Member's Gallery | Members | `/site/gallery` — members_only, Phase 2 | ⬜ Pending |
| Members Only (WP password page) | TBD | Determine actual content first | ⬜ Blocked |

**Archive rule:** Content older than 2 years moves to Google Drive only — no web route. A "Older issues →" link on the newsletters page points to the Drive folder.

### Members Nav Dropdown

A **"Members"** top-level nav item with a dropdown. Pages flagged `members_only` in the `PublicPage` table do not appear in the dropdown for unauthenticated visitors. Officers bypass the member login automatically (already implemented).

```
Members ▾
  ├── Newsletters          (members_only — current 2 years)
  ├── Member Gallery       (members_only — Phase 2)
  └── Renew Membership     (members_only — dues + PayPal, Phase 3)
```

Non-members see the "Members" label but an empty or login-prompt dropdown. The `PublicPage.members_only` flag and `member_site_authed` session handle visibility — no new auth machinery needed.

### Migration Process

- [ ] **Get Dropbox access** — inventory financial records, minutes, member lists, historical docs before finalising what migrates vs. archives (blocker for full classification)
- [ ] **Determine "Members Only" page content** on WordPress — find out what's behind the WP password; classify each item
- [ ] **Newsletter PDFs** — download all from WordPress; sort by year; 2024–present → `app/static/newsletters/`; pre-2024 → Google Drive
- [ ] **Build `/site/newsletters` route** — members_only page listing PDFs by year with "Older issues →" Drive link
- [ ] **Build Members nav dropdown** — add "Members ▾" to `base_public.html`; items hidden from guests using `member_site_authed`
- [ ] **Symposium page** — static content, low effort; add to Phase 2
- [ ] **Dues page** — static tier descriptions + PayPal buttons; coordinate with Treasurer (see FINANCIAL_PLAN.md)
- [ ] **Gallery** — defer until photo approval owner and storage approach are decided
- [ ] **Dropbox migration** — once accessed: financial historical records → Google Drive; active items → leave in Dropbox until financial module is ready; member lists → verify against DB

[↑ Index](#index)

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

[↑ Index](#index)

---

## Open Questions for Officer Discussion

1. **Who maintains content?** Static pages (About, Skill Center, Resources) need someone to update them. With FastAPI/Jinja2 this means editing template files — not as easy as WordPress. A lightweight CMS layer or editable DB fields could help.

2. **Newsletter archive migration** — 20+ years of PDFs need to be organized and uploaded. Is this worth doing, or link to the existing WordPress archive during transition?

3. **Member gallery** — Does the club want to continue this? Who approves submitted photos? What's the storage strategy?

4. **PayPal integration** — Treasurer needs to be involved. PayPal webhooks require a publicly accessible server, so this can't be tested locally.

5. **Members-only content** — What is currently behind the WordPress password? This determines the scope of the protected area.

6. **Timeline** — Phase 1 could be prototyped quickly for discussion. Full cutover to replace WordPress would require officer sign-off and a transition plan.

[↑ Index](#index)

---

## Suggested Next Steps

1. **Review Phase 1** — Walk through the live `/site/` pages with officers. Get feedback.
2. **Decide on Phase 2 priorities** — Newsletters and gallery require the most effort; resources and dues page are simpler.
3. **Decide on content ownership** — Static pages (About, Skill Center, Resources) need someone to update them. With FastAPI/Jinja2 this means editing template files — not as easy as WordPress.
4. **Set a cutover target** — If approved, aim to replace the WordPress site after Phase 2 is at least 80% complete.

[↑ Index](#index)

---

## Dependencies on CVWdata Backlog

Completing this plan depends on:
- OrgEvent model being used consistently for all meetings and events
- Officer data being kept current in the DB (already seeded)
- A production hosting environment (Docker + domain)
- SMTP credentials for contact form email routing

[↑ Index](#index)
