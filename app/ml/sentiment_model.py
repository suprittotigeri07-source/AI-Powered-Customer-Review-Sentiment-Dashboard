from app.ml.preprocessing import contains_negation, tokenize

POSITIVE_WORDS = {
    "good": 1.0,
    "great": 1.4,
    "excellent": 1.8,
    "amazing": 1.7,
    "love": 1.6,
    "loved": 1.6,
    "awesome": 1.5,
    "perfect": 1.8,
    "fantastic": 1.6,
    "wonderful": 1.5,
    "happy": 1.2,
    "satisfied": 1.3,
    "recommend": 1.4,
    "fast": 0.8,
    "easy": 0.9,
    "quality": 0.7,
    "helpful": 1.1,
    "friendly": 1.0,
    "best": 1.4,
    "smooth": 0.8,
    "reliable": 1.0,
    "worth": 0.9,
    "beautiful": 1.1,
    "pleasant": 1.0,
    "impressed": 1.3,
}

NEGATIVE_WORDS = {
    "bad": 1.1,
    "terrible": 1.8,
    "awful": 1.7,
    "horrible": 1.8,
    "hate": 1.6,
    "poor": 1.2,
    "slow": 1.0,
    "late": 1.1,
    "broken": 1.5,
    "damaged": 1.6,
    "worst": 1.8,
    "disappointed": 1.5,
    "disappointing": 1.4,
    "refund": 1.2,
    "rude": 1.4,
    "expensive": 0.9,
    "issue": 0.8,
    "problem": 0.9,
    "problems": 0.9,
    "never": 0.8,
    "waste": 1.4,
    "useless": 1.5,
    "scam": 1.8,
    "missing": 1.1,
    "delay": 1.0,
    "delayed": 1.1,
    "wrong": 1.1,
    "defect": 1.4,
    "defective": 1.5,
    "complaint": 1.0,
    "unhelpful": 1.3,
}


def predict_sentiment(text: str) -> tuple[str, float]:
    tokens = tokenize(text)
    if not tokens:
        return "Neutral", 0.5

    positive = 0.0
    negative = 0.0
    for index, token in enumerate(tokens):
        negated = contains_negation(tokens, index)
        if token in POSITIVE_WORDS:
            score = POSITIVE_WORDS[token]
            if negated:
                negative += score
            else:
                positive += score
        if token in NEGATIVE_WORDS:
            score = NEGATIVE_WORDS[token]
            if negated:
                positive += score * 0.6
            else:
                negative += score

    total = positive + negative
    if total == 0:
        return "Neutral", 0.58

    margin = abs(positive - negative)
    confidence = min(0.97, 0.55 + margin / (total + 1.5))

    if positive - negative >= 0.6:
        return "Positive", round(confidence, 4)
    if negative - positive >= 0.6:
        return "Negative", round(confidence, 4)
    return "Neutral", round(max(0.5, 0.72 - margin / 4), 4)
