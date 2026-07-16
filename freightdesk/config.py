import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    max_rounds: int = 5
    confidence_threshold: float = 0.7
    use_openai: bool = False          # experimental; stub engine is the default
    openai_model: str = "gpt-5.6"


def settings_from_env() -> Settings:
    return Settings(
        max_rounds=int(os.getenv("FREIGHTDESK_MAX_ROUNDS", "5")),
        confidence_threshold=float(os.getenv("FREIGHTDESK_CONFIDENCE_THRESHOLD", "0.7")),
        use_openai=os.getenv("FREIGHTDESK_USE_OPENAI", "0") == "1"
        and bool(os.getenv("OPENAI_API_KEY")),
        openai_model=os.getenv("FREIGHTDESK_MODEL", "gpt-5.6"),
    )
