import re

NEGATION_WORDS = {"not", "no", "never", "neither", "nor", "barely", "hardly", "without"}


def preprocess_text(text: str) -> str:
    if not text:
        return ""
    cleaned = text.strip().lower()
    cleaned = re.sub(r"https?://\S+|www\.\S+", " ", cleaned)
    cleaned = re.sub(r"[^a-z0-9'\s]", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip()


def tokenize(text: str) -> list[str]:
    return [token for token in preprocess_text(text).split(" ") if token]


def contains_negation(tokens: list[str], index: int, window: int = 3) -> bool:
    start = max(0, index - window)
    return any(token in NEGATION_WORDS for token in tokens[start:index])
