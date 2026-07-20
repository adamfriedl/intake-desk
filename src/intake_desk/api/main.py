from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from intake_desk.api.routes import WEB_DIR, router

app = FastAPI(
    title="Intake Desk",
    description="Agentic legal intake, triage, and guided-document workflow",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=WEB_DIR / "static"), name="static")
app.include_router(router)
