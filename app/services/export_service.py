import csv
import io

from sqlalchemy.orm import Session, joinedload

from app.models.review import Review
from app.models.user import User
from app.services.project_service import ProjectService


class ExportService:
    def __init__(self, db: Session, projects: ProjectService):
        self.db = db
        self.projects = projects

    def to_csv(self, user: User, project_id: int) -> str:
        self.projects.get_owned(user, project_id)
        reviews = (
            self.db.query(Review)
            .options(joinedload(Review.sentiment), joinedload(Review.topics))
            .filter(Review.project_id == project_id)
            .all()
        )
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(["Review", "Rating", "Date", "Source", "Sentiment", "Confidence", "Topic", "Status"])
        for review in reviews:
            topic = review.topics[0].topic if review.topics else ""
            writer.writerow(
                [
                    review.review_text,
                    review.rating or "",
                    review.review_date or "",
                    review.source or "",
                    review.sentiment.sentiment if review.sentiment else "",
                    review.sentiment.confidence if review.sentiment else "",
                    topic,
                    review.status,
                ]
            )
        return buffer.getvalue()
