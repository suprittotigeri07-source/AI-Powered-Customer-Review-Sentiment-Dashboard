from datetime import date

from sqlalchemy import and_
from sqlalchemy.orm import Session, joinedload

from app.models.review import Review
from app.models.sentiment import SentimentResult


class ReviewRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_filtered(
        self,
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
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Review], int]:
        query = (
            self.db.query(Review)
            .options(joinedload(Review.sentiment), joinedload(Review.topics))
            .filter(Review.project_id == project_id)
        )
        if search:
            like = f"%{search}%"
            query = query.filter(Review.review_text.ilike(like))
        if source:
            query = query.filter(Review.source == source)
        if min_rating is not None:
            query = query.filter(Review.rating >= min_rating)
        if max_rating is not None:
            query = query.filter(Review.rating <= max_rating)
        if start_date:
            query = query.filter(Review.review_date >= start_date)
        if end_date:
            query = query.filter(Review.review_date <= end_date)
        if flagged is not None:
            query = query.filter(Review.flagged == flagged)
        if sentiment or min_confidence is not None:
            query = query.join(SentimentResult, SentimentResult.review_id == Review.id)
            if sentiment:
                query = query.filter(SentimentResult.sentiment == sentiment)
            if min_confidence is not None:
                query = query.filter(SentimentResult.confidence >= min_confidence)

        total = query.count()
        items = (
            query.order_by(Review.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return items, total

    def get_by_id(self, review_id: int) -> Review | None:
        return (
            self.db.query(Review)
            .options(joinedload(Review.sentiment), joinedload(Review.topics))
            .filter(Review.id == review_id)
            .first()
        )

    def pending_for_project(self, project_id: int, review_ids: list[int] | None = None) -> list[Review]:
        query = self.db.query(Review).filter(Review.project_id == project_id)
        if review_ids:
            query = query.filter(Review.id.in_(review_ids))
        return query.all()
