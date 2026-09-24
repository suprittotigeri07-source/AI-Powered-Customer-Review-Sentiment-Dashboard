from pydantic import BaseModel


class AnalyzeTextRequest(BaseModel):
    text: str
    project_id: int | None = None
    review_id: int | None = None


class AnalyzeTextResponse(BaseModel):
    sentiment: str
    confidence: float
    model_name: str
    model_version: str
    topics: list[str] = []
