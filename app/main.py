from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import analytics, auth, health, projects, reviews, sentiment
from app.core.config import get_settings
from app.database.base import Base
from app.database.connection import engine
from app.models import project, review, sentiment as sentiment_model, topic, user  # noqa: F401

settings = get_settings()
Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.app_name, version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

prefix = settings.api_v1_prefix
app.include_router(health.router, prefix=prefix)
app.include_router(auth.router, prefix=prefix)
app.include_router(projects.router, prefix=prefix)
app.include_router(reviews.router, prefix=prefix)
app.include_router(sentiment.router, prefix=prefix)
app.include_router(analytics.router, prefix=prefix)
