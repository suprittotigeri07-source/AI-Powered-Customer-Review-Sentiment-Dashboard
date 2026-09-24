TOPIC_KEYWORDS = {
    "Delivery": ["delivery", "shipping", "shipped", "courier", "arrived", "late", "delay", "package"],
    "Product Quality": ["quality", "broken", "damaged", "defect", "defective", "build", "material", "cheap"],
    "Customer Support": ["support", "service", "staff", "agent", "help", "rude", "unhelpful", "response"],
    "Pricing": ["price", "expensive", "cheap", "cost", "value", "overpriced", "refund", "billing"],
    "Packaging": ["packaging", "box", "wrapped", "seal", "open"],
    "Usability": ["easy", "difficult", "confusing", "setup", "app", "interface", "instructions"],
}


def detect_topics(text: str) -> list[tuple[str, float]]:
    lowered = (text or "").lower()
    found: list[tuple[str, float]] = []
    for topic, keywords in TOPIC_KEYWORDS.items():
        hits = sum(1 for keyword in keywords if keyword in lowered)
        if hits:
            confidence = min(0.95, 0.55 + hits * 0.12)
            found.append((topic, round(confidence, 4)))
    if not found:
        found.append(("General", 0.5))
    return found
