from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.database import engine, Base, SessionLocal, settings
import app.models.member        # register with Base
import app.models.program       # register with Base
import app.models.user          # register with Base
import app.models.officer       # register with Base
import app.models.org           # register with Base
import app.models.financial     # register with Base
import app.models.group         # register with Base
import app.models.email_models  # register with Base
import app.models.resource             # register with Base
import app.models.group_leader         # register with Base
import app.models.event_registration   # register with Base
import app.models.site_content         # register with Base (SiteSetting, ContentBlock, PublicPage)
from app.dependencies import NotAuthenticatedException, PermissionDeniedException
from app.routers import members, apply, programs, feedback, auth
from app.routers import admin_console, financial, exec_, groups
from app.routers import email_ as email_router
from app.routers import public_ as public_router
from app.routers import librarian as librarian_router
from app.routers import admin_backup as backup_router
from app.routers import guides as guides_router
from app.routers import processes as processes_router
from app.routers import activity_group as activity_router

# Apply any staged restore BEFORE opening DB connections
from app.backup_service import apply_pending_restore
apply_pending_restore()

Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.scheduler import start_scheduler
    start_scheduler(app)
    yield
    from app.scheduler import scheduler
    if scheduler.running:
        scheduler.shutdown(wait=False)


app = FastAPI(title="CVW Membership Database", lifespan=lifespan)
app.mount("/static", StaticFiles(directory="app/static"), name="static")


# ── Middleware ────────────────────────────────────────────────────────────────

class UserMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request.state.user = None
        request.state.member_site_authed = False
        try:
            user_id = request.session.get("user_id")
            if user_id:
                db = SessionLocal()
                try:
                    from app.models.user import User
                    user = db.get(User, user_id)
                    if user and user.active:
                        request.state.user = user
                finally:
                    db.close()
            request.state.member_site_authed = bool(
                request.session.get("member_site_authed")
            )
        except Exception:
            pass
        return await call_next(request)


# SessionMiddleware must be added last (runs first for incoming requests)
app.add_middleware(UserMiddleware)
app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY, https_only=False)


# ── Exception handlers ────────────────────────────────────────────────────────

@app.exception_handler(NotAuthenticatedException)
async def not_authenticated_handler(request: Request, exc: NotAuthenticatedException):
    return RedirectResponse(url=f"/login?next={request.url.path}", status_code=302)


@app.exception_handler(PermissionDeniedException)
async def permission_denied_handler(request: Request, exc: PermissionDeniedException):
    return HTMLResponse("<h2>Access denied.</h2><p><a href='/'>Dashboard</a></p>", status_code=403)


# ── Routers ───────────────────────────────────────────────────────────────────

app.include_router(auth.router)
app.include_router(members.router)
app.include_router(apply.router)
app.include_router(programs.router)
app.include_router(feedback.router)
app.include_router(financial.router)
app.include_router(exec_.router)
app.include_router(admin_console.router)
app.include_router(groups.router)
app.include_router(email_router.router)
app.include_router(public_router.router)
app.include_router(librarian_router.router)
app.include_router(backup_router.router)
app.include_router(guides_router.router)
app.include_router(processes_router.router)
app.include_router(activity_router.router)


@app.get("/")
def root(request: Request):
    if not request.state.user:
        return RedirectResponse(url="/login", status_code=302)
    return RedirectResponse(url="/dashboard", status_code=302)


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):
    if not request.state.user:
        return RedirectResponse(url="/login", status_code=302)
    from fastapi.templating import Jinja2Templates
    templates = Jinja2Templates(directory="app/templates")
    return templates.TemplateResponse("dashboard.html", {"request": request})


# ── Seed admin user ───────────────────────────────────────────────────────────

def _seed_admin():
    if not settings.ADMIN_INITIAL_PASSWORD:
        return
    db = SessionLocal()
    try:
        from app.models.user import User
        if db.query(User).count() == 0:
            admin = User(
                username="admin",
                full_name="Administrator",
                role="admin",
                hashed_password=User.hash_password(settings.ADMIN_INITIAL_PASSWORD),
                active=True,
            )
            db.add(admin)
            db.commit()
            print("✓ Admin user created (username: admin)")
    finally:
        db.close()


_seed_admin()


def _seed_site_content():
    from app.models.site_content import SiteSetting, ContentBlock
    db = SessionLocal()
    try:
        settings_data = [
            ("member_site_password", "Member Site Password",        ""),
            ("meeting_day",      "Meeting Day / Frequency",    "Third Tuesday of each month"),
            ("meeting_time",     "Meeting Time",               "6:00 PM – 9:00 PM"),
            ("meeting_location", "Meeting Location",           "Crimora Community Center, Crimora, Virginia"),
            ("meeting_format",   "Meeting Format",
             "Demonstration by invited presenter or club member, Show and Tell by members, open gallery, Q&A, announcements"),
            ("dues_individual",  "Individual Annual Dues",     "$50"),
            ("dues_family",      "Family Annual Dues",         "$50"),
            ("dues_affiliated",  "Affiliated Annual Dues",     "$20"),
            ("dues_young_adult", "Young Adult / Student Dues", "$20"),
            ("dues_honorary",    "Honorary Dues",              "Free"),
            ("backup_keep_count", "Backups to Keep",            "30"),
        ]
        for key, label, value in settings_data:
            if not db.get(SiteSetting, key):
                db.add(SiteSetting(key=key, label=label, value=value))

        blocks_data = [
            ("about_who_we_are", "About — Who We Are",
             "Central Virginia Woodturners (CVW) is a chapter of the "
             "[American Association of Woodturners (AAW)](https://woodturner.org), "
             "based in the Crimora, Virginia area. Founded by a small group of enthusiasts, "
             "CVW has grown into a community of turners who range from complete beginners to "
             "nationally recognised artists.\n\n"
             "We meet monthly for programs featuring demonstrations, Show and Tell, and discussions. "
             "Members regularly share tips, tools, and timber from the meeting floor — and the "
             "friendly atmosphere makes every meeting a great place to learn."),
            ("about_membership_intro", "About — Membership Section Intro",
             "Annual dues support club programs, library resources, and the Skills Center."),
            ("skill_center_what", "Skill Center — What Is It?",
             "The CVW Skill Center is a member resource offering hands-on lathe time, tool use, and "
             "one-on-one mentoring from experienced turners. Whether you are learning for the first "
             "time or refining a specific technique, the Skill Center provides a supportive, "
             "well-equipped environment."),
            ("skill_center_expect", "Skill Center — What to Expect",
             "A typical Skill Center session accommodates a small group of members working on "
             "individual projects with guidance available from the Skills Center Director and "
             "volunteer mentors. Lathes, basic turning tools, and safety equipment are provided. "
             "Participants are encouraged to bring their own tools as they progress.\n\n"
             "Topics covered include:\n\n"
             "- Safe lathe operation and tool handling\n"
             "- Bowl and spindle turning fundamentals\n"
             "- Tool sharpening and maintenance\n"
             "- Finishing techniques — oils, lacquers, and waxes\n"
             "- Hollowing and advanced forms\n"
             "- Member-requested skill topics"),
        ]
        for key, title, body in blocks_data:
            if not db.get(ContentBlock, key):
                db.add(ContentBlock(key=key, title=title, body=body))

        # Public pages — all start as unrestricted; admin toggles members_only
        from app.models.site_content import PublicPage
        pages_data = [
            ("home",            "Home"),
            ("about",           "About"),
            ("officers",        "Leadership / Officers"),
            ("calendar",        "Calendar"),
            ("upcoming-events", "Upcoming Events"),
            ("skill-center",    "Skill Center"),
            ("resources",       "Resources"),
            ("newsletters",     "Newsletters"),
            ("guides",          "Guides"),
            ("contact",         "Contact"),
        ]
        for slug, label in pages_data:
            if not db.get(PublicPage, slug):
                db.add(PublicPage(slug=slug, label=label, members_only=False))

        db.commit()
    finally:
        db.close()


_seed_site_content()
