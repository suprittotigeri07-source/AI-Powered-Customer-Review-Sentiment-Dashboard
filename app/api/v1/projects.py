from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database.connection import get_db
from app.models.user import User
from app.repositories.project_repository import ProjectRepository
from app.schemas.project import ProjectCreate, ProjectResponse
from app.services.project_service import ProjectService

router = APIRouter(prefix="/projects", tags=["projects"])


def _service(db: Session) -> ProjectService:
    return ProjectService(ProjectRepository(db))


@router.get("", response_model=list[ProjectResponse])
def list_projects(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return _service(db).list_projects(current_user)


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(
    payload: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = _service(db).create(current_user, payload)
    return ProjectResponse(
        id=project.id,
        name=project.name,
        description=project.description or "",
        created_at=project.created_at,
        review_count=0,
        analyzed_count=0,
    )


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(project_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    service = _service(db)
    project = service.get_owned(current_user, project_id)
    total, analyzed = ProjectRepository(db).review_counts(project.id)
    return ProjectResponse(
        id=project.id,
        name=project.name,
        description=project.description or "",
        created_at=project.created_at,
        review_count=total,
        analyzed_count=analyzed,
    )


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(project_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _service(db).delete(current_user, project_id)
