from sqlalchemy.orm import Session

from app.ml.inference import run_inference
from app.models.review import Review
from app.models.sentiment import SentimentResult
from app.models.topic import Topic
from app.models.user import User
from app.repositories.review_repository import ReviewRepository
from app.services.project_service import ProjectService


class SentimentService:
    def __init__(self, db: Session, projects: ProjectService, reviews: ReviewRepository):
        self.db = db
        self.projects = projects
        self.reviews = reviews

    def analyze_project(self, user: User, project_id: int, review_ids: list[int] | None = None) -> dict:
        self.projects.get_owned(user, project_id)
        items = self.reviews.pending_for_project(project_id, review_ids)
        processed = 0
        failed = 0
        for review in items:
            try:
                self._analyze_review(review)
                processed += 1
            except Exception:
                review.status = "FAILED"
                failed += 1
        self.db.commit()
        return {
            "processed": processed,
            "failed": failed,
            "status": "COMPLETED" if failed == 0 else "PARTIAL",
        }

    def analyze_text(self, text: str) -> dict:
        result = run_inference(text)
        return {
            "sentiment": result.sentiment,
            "confidence": result.confidence,
            "model_name": result.model_name,
            "model_version": result.model_version,
            "topics": [name for name, _ in result.topics],
        }

    def _analyze_review(self, review: Review) -> None:
        review.status = "PROCESSING"
        self.db.flush()
        result = run_inference(review.review_text)
        if review.sentiment:
            review.sentiment.sentiment = result.sentiment
            review.sentiment.confidence = result.confidence
            review.sentiment.model_name = result.model_name
            review.sentiment.model_version = result.model_version
        else:
            self.db.add(
                SentimentResult(
                    review_id=review.id,
                    sentiment=result.sentiment,
                    confidence=result.confidence,
                    model_name=result.model_name,
                    model_version=result.model_version,
                )
            )
        self.db.query(Topic).filter(Topic.review_id == review.id).delete()
        for name, confidence in result.topics:
            self.db.add(Topic(review_id=review.id, topic=name, confidence=confidence))
        if result.sentiment == "Negative" and result.confidence >= 0.7:
            review.flagged = True
        if result.confidence < 0.6:
            review.flagged = True
        review.status = "COMPLETED"
