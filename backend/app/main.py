from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler
from app.database import engine, Base, SessionLocal
from app.routers import auth, behaviors, predictions
from app.services.snapshot import take_interest_snapshot

Base.metadata.create_all(bind=engine)


def run_snapshot_job():
    db = SessionLocal()
    try:
        take_interest_snapshot(db)
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        run_snapshot_job,
        "interval",
        hours=1,
        id="interest_snapshot",
        replace_existing=True,
    )
    scheduler.start()
    yield
    scheduler.shutdown()


app = FastAPI(
    title="Interest Prediction API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3002"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(behaviors.router)
app.include_router(predictions.router)
