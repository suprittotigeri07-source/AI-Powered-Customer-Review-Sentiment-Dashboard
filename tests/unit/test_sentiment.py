from app.ml.preprocessing import preprocess_text
from app.ml.sentiment_model import predict_sentiment


def test_preprocess_normalizes_text():
    assert preprocess_text("  Hello WORLD!!  ") == "hello world"


def test_positive_sentiment():
    label, confidence = predict_sentiment("The product is amazing and I love the quality")
    assert label == "Positive"
    assert confidence > 0.6


def test_negative_sentiment():
    label, _ = predict_sentiment("The package arrived damaged and the support was terrible")
    assert label == "Negative"


def test_empty_is_neutral():
    label, confidence = predict_sentiment("   ")
    assert label == "Neutral"
    assert confidence == 0.5
