from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from app.database import engine, Base
import app.models.member  # ensure model is registered with Base
from app.routers import members

Base.metadata.create_all(bind=engine)

app = FastAPI(title="CVW Membership Database")

app.include_router(members.router)


@app.get("/")
def root():
    return RedirectResponse(url="/members/")
