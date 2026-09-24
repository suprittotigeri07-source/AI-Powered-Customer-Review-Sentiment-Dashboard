from sqlalchemy.orm import Session

from app.models.project import Project
from app.models.review import Review


class ProjectRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_for_user(self, user_id: int) -> list[Project]:
        return self.db.query(Project).filter(Project.user_id == user_id).order_by(Project.created_at.desc()).all()

    def get_owned(self, project_id: int, user_id: int) -> Project | None:
        return (
            self.db.query(Project)
            .filter(Project.id == project_id, Project.user_id == user_id)
            .first()
        )

    def create(self, user_id: int, name: str, description: str) -> Project:
        project = Project(user_id=user_id, name=name, description=description)
        self.db.add(project)
        self.db.commit()
        self.db.refresh(project)
        return project

    def delete(self, project: Project) -> None:
        self.db.delete(project)
        self.db.commit()

    def review_counts(self, project_id: int) -> tuple[int, int]:
        total = self.db.query(Review).filter(Review.project_id == project_id).count()
        analyzed = (
            self.db.query(Review)
            .filter(Review.project_id == project_id, Review.status == "COMPLETED")
            .count()
        )
        return total, analyzed
