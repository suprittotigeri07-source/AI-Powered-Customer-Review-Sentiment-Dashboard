from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database.connection import get_db
from app.models.user import User
from app.repositories.project_repository import ProjectRepository
from app.schemas.analytics import AnalyticsSummary, InsightResponse, TopicStat, TrendPoint
from app.services.analytics_service import AnalyticsService, InsightService
from app.services.project_service import ProjectService

router = APIRouter(prefix="/analytics", tags=["analytics"])


def _service(db: Session) -> AnalyticsService:
    return AnalyticsService(db, ProjectService(ProjectRepository(db)))


@router.get("/summary", response_model=AnalyticsSummary)
def summary(project_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return _service(db).summary(current_user, project_id)


@router.get("/trends", response_model=list[TrendPoint])
def trends(project_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return _service(db).trends(current_user, project_id)


@router.get("/distribution")
def distribution(project_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return _service(db).distribution(current_user, project_id)


@router.get("/topics", response_model=list[TopicStat])
def topics(project_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return _service(db).topics(current_user, project_id)


@router.get("/insights", response_model=InsightResponse)
def insights(project_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    service = _service(db)
    summary_data = service.summary(current_user, project_id)
    topic_data = service.topics(current_user, project_id)
    trend_data = service.trends(current_user, project_id)
    return InsightService().generate(summary_data, topic_data, trend_data)
