from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database.connection import get_db
from app.ml.model_registry import get_active_model
from app.models.user import User
from app.repositories.project_repository import ProjectRepository
from app.repositories.review_repository import ReviewRepository
from app.schemas.review import AnalyzeRequest, AnalyzeResponse
from app.schemas.sentiment import AnalyzeTextRequest, AnalyzeTextResponse
from app.services.project_service import ProjectService
from app.services.sentiment_service import SentimentService

router = APIRouter(prefix="/sentiment", tags=["sentiment"])


def _service(db: Session) -> SentimentService:
    return SentimentService(db, ProjectService(ProjectRepository(db)), ReviewRepository(db))


@router.post("/analyze", response_model=AnalyzeTextResponse)
def analyze_text(payload: AnalyzeTextRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return _service(db).analyze_text(payload.text)


@router.post("/batch", response_model=AnalyzeResponse)
def analyze_batch(payload: AnalyzeRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    result = _service(db).analyze_project(current_user, payload.project_id, payload.review_ids)
    return result


@router.get("/model")
def model_info(current_user: User = Depends(get_current_user)):
    return get_active_model()
