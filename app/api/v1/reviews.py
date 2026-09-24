from datetime import date

from fastapi import APIRouter, Depends, Query, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database.connection import get_db
from app.models.user import User
from app.repositories.project_repository import ProjectRepository
from app.repositories.review_repository import ReviewRepository
from app.schemas.review import ReviewListResponse, ReviewResponse, TopicResponse, SentimentResponse, UploadSummary
from app.services.export_service import ExportService
from app.services.project_service import ProjectService
from app.services.review_service import ReviewService

router = APIRouter(prefix="/reviews", tags=["reviews"])


def serialize(review) -> ReviewResponse:
    sentiment = None
    if review.sentiment:
        sentiment = SentimentResponse(
            sentiment=review.sentiment.sentiment,
            confidence=review.sentiment.confidence,
            model_name=review.sentiment.model_name,
            model_version=review.sentiment.model_version,
            processed_at=review.sentiment.processed_at,
        )
    topics = [TopicResponse(topic=item.topic, confidence=item.confidence) for item in review.topics]
    return ReviewResponse(
        id=review.id,
        project_id=review.project_id,
        review_text=review.review_text,
        rating=review.rating,
        source=review.source,
        product=review.product,
        category=review.category,
        review_date=review.review_date,
        status=review.status,
        flagged=review.flagged,
        created_at=review.created_at,
        sentiment=sentiment,
        topics=topics,
    )


@router.get("", response_model=ReviewListResponse)
def list_reviews(
    project_id: int,
    search: str | None = None,
    sentiment: str | None = None,
    source: str | None = None,
    min_rating: float | None = None,
    max_rating: float | None = None,
    min_confidence: float | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    flagged: bool | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ProjectService(ProjectRepository(db)).get_owned(current_user, project_id)
    items, total = ReviewRepository(db).list_filtered(
        project_id=project_id,
        search=search,
        sentiment=sentiment,
        source=source,
        min_rating=min_rating,
        max_rating=max_rating,
        min_confidence=min_confidence,
        start_date=start_date,
        end_date=end_date,
        flagged=flagged,
        page=page,
        page_size=page_size,
    )
    return ReviewListResponse(items=[serialize(item) for item in items], total=total, page=page, page_size=page_size)


@router.get("/export")
def export_reviews(project_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    csv_data = ExportService(db, ProjectService(ProjectRepository(db))).to_csv(current_user, project_id)
    return StreamingResponse(
        iter([csv_data]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=reviewsense-export.csv"},
    )


@router.get("/{review_id}", response_model=ReviewResponse)
def get_review(
    review_id: int,
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ProjectService(ProjectRepository(db)).get_owned(current_user, project_id)
    review = ReviewRepository(db).get_by_id(review_id)
    if not review or review.project_id != project_id:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Review not found")
    return serialize(review)


@router.post("/upload", response_model=UploadSummary)
def upload_reviews(
    project_id: int = Form(...),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    summary = ReviewService(db, ProjectService(ProjectRepository(db))).upload_csv(current_user, project_id, file)
    return summary


@router.post("/{review_id}/flag")
def flag_review(
    review_id: int,
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ProjectService(ProjectRepository(db)).get_owned(current_user, project_id)
    review = ReviewRepository(db).get_by_id(review_id)
    if not review or review.project_id != project_id:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Review not found")
    review.flagged = not review.flagged
    db.commit()
    return {"flagged": review.flagged}
