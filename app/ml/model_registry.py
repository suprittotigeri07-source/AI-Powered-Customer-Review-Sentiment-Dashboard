from app.core.config import get_settings


def get_active_model() -> dict:
    settings = get_settings()
    return {
        "name": settings.model_name,
        "version": settings.model_version,
        "type": "lexicon-transformer-compatible",
        "labels": ["Positive", "Neutral", "Negative"],
        "notes": "Default MVP model uses a deterministic lexicon and topic rules. HuggingFace transformers can be enabled later without changing the API contract.",
    }
