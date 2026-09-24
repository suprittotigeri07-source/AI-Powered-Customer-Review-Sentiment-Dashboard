from collections import Counter, defaultdict
from datetime import date

from sqlalchemy.orm import Session

from app.models.review import Review
from app.models.sentiment import SentimentResult
from app.models.topic import Topic
from app.models.user import User
from app.schemas.analytics import AnalyticsSummary, InsightResponse, TopicStat, TrendPoint
from app.services.project_service import ProjectService


class AnalyticsService:
    def __init__(self, db: Session, projects: ProjectService):
        self.db = db
        self.projects = projects

    def summary(self, user: User, project_id: int) -> AnalyticsSummary:
        self.projects.get_owned(user, project_id)
        reviews = self.db.query(Review).filter(Review.project_id == project_id).all()
        analyzed = [review for review in reviews if review.sentiment]
        counts = Counter(review.sentiment.sentiment for review in analyzed)
        total = len(reviews)
        analyzed_count = len(analyzed)
        ratings = [review.rating for review in reviews if review.rating is not None]
        confidences = [review.sentiment.confidence for review in analyzed]
        attention = sum(
            1
            for review in analyzed
            if review.flagged or review.sentiment.sentiment == "Negative" or review.sentiment.confidence < 0.6
        )
        return AnalyticsSummary(
            total_reviews=total,
            analyzed_reviews=analyzed_count,
            positive=counts.get("Positive", 0),
            neutral=counts.get("Neutral", 0),
            negative=counts.get("Negative", 0),
            positive_pct=_pct(counts.get("Positive", 0), analyzed_count),
            neutral_pct=_pct(counts.get("Neutral", 0), analyzed_count),
            negative_pct=_pct(counts.get("Negative", 0), analyzed_count),
            average_rating=round(sum(ratings) / len(ratings), 2) if ratings else None,
            average_confidence=round(sum(confidences) / len(confidences), 4) if confidences else None,
            attention_count=attention,
        )

    def trends(self, user: User, project_id: int) -> list[TrendPoint]:
        self.projects.get_owned(user, project_id)
        rows = (
            self.db.query(Review, SentimentResult)
            .join(SentimentResult, SentimentResult.review_id == Review.id)
            .filter(Review.project_id == project_id)
            .all()
        )
        grouped: dict[str, Counter] = defaultdict(Counter)
        for review, sentiment in rows:
            key = (review.review_date or review.created_at.date()).isoformat()
            grouped[key][sentiment.sentiment] += 1
        points = []
        for key in sorted(grouped):
            counter = grouped[key]
            points.append(
                TrendPoint(
                    date=key,
                    positive=counter.get("Positive", 0),
                    neutral=counter.get("Neutral", 0),
                    negative=counter.get("Negative", 0),
                )
            )
        return points

    def topics(self, user: User, project_id: int) -> list[TopicStat]:
        self.projects.get_owned(user, project_id)
        rows = (
            self.db.query(Topic, SentimentResult)
            .join(Review, Review.id == Topic.review_id)
            .outerjoin(SentimentResult, SentimentResult.review_id == Review.id)
            .filter(Review.project_id == project_id)
            .all()
        )
        counts = Counter(topic.topic for topic, _ in rows)
        total = sum(counts.values()) or 1
        dominant = defaultdict(Counter)
        for topic, sentiment in rows:
            if sentiment:
                dominant[topic.topic][sentiment.sentiment] += 1
        stats = []
        for name, count in counts.most_common(12):
            top_sentiment = dominant[name].most_common(1)[0][0] if dominant[name] else None
            stats.append(TopicStat(topic=name, count=count, share=round(count / total * 100, 1), sentiment=top_sentiment))
        return stats

    def distribution(self, user: User, project_id: int) -> dict:
        summary = self.summary(user, project_id)
        return {
            "sentiment": [
                {"name": "Positive", "value": summary.positive},
                {"name": "Neutral", "value": summary.neutral},
                {"name": "Negative", "value": summary.negative},
            ],
            "ratings": self._ratings(project_id),
        }

    def _ratings(self, project_id: int) -> list[dict]:
        reviews = self.db.query(Review).filter(Review.project_id == project_id).all()
        counts = Counter(int(review.rating) for review in reviews if review.rating)
        return [{"rating": rating, "count": counts.get(rating, 0)} for rating in range(1, 6)]


class InsightService:
    def generate(self, summary: AnalyticsSummary, topics: list[TopicStat], trends: list[TrendPoint]) -> InsightResponse:
        if summary.analyzed_reviews == 0:
            return InsightResponse(
                summary="No analyzed reviews yet. Upload a CSV and run sentiment analysis to generate insights.",
                negative_issues="Issue summaries appear after negative reviews are classified.",
                trend_explanation="Trend explanations require completed analysis across more than one date.",
                generated=False,
            )

        negative_topics = [item.topic for item in topics if item.sentiment == "Negative"][:3]
        issue_text = ", ".join(negative_topics) if negative_topics else "general dissatisfaction"
        trend_text = "Sentiment is relatively stable across the selected period."
        if len(trends) >= 2:
            first = _neg_share(trends[0])
            last = _neg_share(trends[-1])
            if last > first + 5:
                trend_text = f"Negative sentiment increased from {first:.0f}% to {last:.0f}% across the available dates."
            elif first > last + 5:
                trend_text = f"Negative sentiment improved from {first:.0f}% to {last:.0f}% across the available dates."

        summary_text = (
            f"{summary.analyzed_reviews} reviews were analyzed. "
            f"{summary.positive_pct:.0f}% are predicted positive, "
            f"{summary.neutral_pct:.0f}% neutral, and {summary.negative_pct:.0f}% negative. "
            f"{summary.attention_count} reviews may need human attention."
        )
        issues = (
            f"Negative reviews most often mention {issue_text}. "
            "These themes should be reviewed by the operations or product team."
        )
        return InsightResponse(summary=summary_text, negative_issues=issues, trend_explanation=trend_text)


def _pct(part: int, total: int) -> float:
    return round((part / total) * 100, 1) if total else 0.0


def _neg_share(point: TrendPoint) -> float:
    total = point.positive + point.neutral + point.negative
    return (point.negative / total) * 100 if total else 0.0
