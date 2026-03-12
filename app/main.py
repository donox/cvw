from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from app.database import engine, Base
import app.models.member   # register with Base
import app.models.program  # register with Base
from app.routers import members, apply, programs, feedback

Base.metadata.create_all(bind=engine)

app = FastAPI(title="CVW Membership Database")

app.include_router(members.router)
app.include_router(apply.router)
app.include_router(programs.router)
app.include_router(feedback.router)


@app.get("/")
def root():
    return RedirectResponse(url="/members/")
