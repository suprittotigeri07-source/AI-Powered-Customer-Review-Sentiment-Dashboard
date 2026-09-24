from fastapi import HTTPException, status

from app.models.project import Project
from app.models.user import User
from app.repositories.project_repository import ProjectRepository
from app.schemas.project import ProjectCreate, ProjectResponse


class ProjectService:
    def __init__(self, projects: ProjectRepository):
        self.projects = projects

    def list_projects(self, user: User) -> list[ProjectResponse]:
        items = []
        for project in self.projects.list_for_user(user.id):
            total, analyzed = self.projects.review_counts(project.id)
            items.append(
                ProjectResponse(
                    id=project.id,
                    name=project.name,
                    description=project.description or "",
                    created_at=project.created_at,
                    review_count=total,
                    analyzed_count=analyzed,
                )
            )
        return items

    def create(self, user: User, payload: ProjectCreate) -> Project:
        return self.projects.create(user.id, payload.name.strip(), payload.description.strip())

    def get_owned(self, user: User, project_id: int) -> Project:
        project = self.projects.get_owned(project_id, user.id)
        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
        return project

    def delete(self, user: User, project_id: int) -> None:
        project = self.get_owned(user, project_id)
        self.projects.delete(project)
