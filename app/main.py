from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
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
import app.models.event_registration   # register with Base
from app.dependencies import NotAuthenticatedException, PermissionDeniedException
from app.routers import members, apply, programs, feedback, auth
from app.routers import admin_console, financial, exec_, groups
from app.routers import email_ as email_router
from app.routers import public_ as public_router
from app.routers import librarian as librarian_router

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


# ── Middleware ────────────────────────────────────────────────────────────────

class UserMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request.state.user = None
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
