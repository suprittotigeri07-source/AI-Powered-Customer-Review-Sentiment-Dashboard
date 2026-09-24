from app.core.config import get_settings
from app.ml.sentiment_model import predict_sentiment
from app.ml.topics import detect_topics


class InferenceResult:
    def __init__(self, sentiment: str, confidence: float, topics: list[tuple[str, float]]):
        self.sentiment = sentiment
        self.confidence = confidence
        self.topics = topics
        settings = get_settings()
        self.model_name = settings.model_name
        self.model_version = settings.model_version


def run_inference(text: str) -> InferenceResult:
    sentiment, confidence = predict_sentiment(text)
    topics = detect_topics(text)
    return InferenceResult(sentiment, confidence, topics)
