from datetime import date, datetime

from pydantic import BaseModel


class TopicResponse(BaseModel):
    topic: str
    confidence: float


class SentimentResponse(BaseModel):
    sentiment: str
    confidence: float
    model_name: str
    model_version: str
    processed_at: datetime


class ReviewResponse(BaseModel):
    id: int
    project_id: int
    review_text: str
    rating: float | None
    source: str | None
    product: str | None
    category: str | None
    review_date: date | None
    status: str
    flagged: bool
    created_at: datetime
    sentiment: SentimentResponse | None = None
    topics: list[TopicResponse] = []

    model_config = {"from_attributes": True}


class ReviewListResponse(BaseModel):
    items: list[ReviewResponse]
    total: int
    page: int
    page_size: int


class UploadSummary(BaseModel):
    total_rows: int
    valid_rows: int
    invalid_rows: int
    imported_rows: int
    errors: list[dict]


class AnalyzeRequest(BaseModel):
    project_id: int
    review_ids: list[int] | None = None


class AnalyzeResponse(BaseModel):
    processed: int
    failed: int
    status: str
