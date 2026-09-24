from datetime import datetime

from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str = ""


class ProjectResponse(BaseModel):
    id: int
    name: str
    description: str
    created_at: datetime
    review_count: int = 0
    analyzed_count: int = 0

    model_config = {"from_attributes": True}
