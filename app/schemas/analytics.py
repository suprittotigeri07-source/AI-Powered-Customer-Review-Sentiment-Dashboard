from pydantic import BaseModel


class AnalyticsSummary(BaseModel):
    total_reviews: int
    analyzed_reviews: int
    positive: int
    neutral: int
    negative: int
    positive_pct: float
    neutral_pct: float
    negative_pct: float
    average_rating: float | None
    average_confidence: float | None
    attention_count: int


class TrendPoint(BaseModel):
    date: str
    positive: int
    neutral: int
    negative: int


class TopicStat(BaseModel):
    topic: str
    count: int
    share: float
    sentiment: str | None = None


class InsightResponse(BaseModel):
    summary: str
    negative_issues: str
    trend_explanation: str
    generated: bool = True
