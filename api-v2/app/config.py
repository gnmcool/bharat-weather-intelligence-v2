import os
from dataclasses import dataclass, field


def _list(v: str) -> list[str]:
    return [x.strip() for x in v.split(",") if x.strip()]


@dataclass(frozen=True)
class Settings:
    # CORE public API — the only data boundary (docs/CORE_BOUNDARY.md).
    core_api_base: str = os.getenv("CORE_API_BASE", "https://bharat-weather-intelligence-brown.vercel.app/api/v1")
    cors_origins: list[str] = field(default_factory=lambda: _list(os.getenv(
        "CORS_ORIGINS", "https://gnmcool.github.io,http://localhost:5174,http://127.0.0.1:5174")))
    point_ttl: float = float(os.getenv("POINT_TTL_S", "600"))       # 10 min
    region_ttl: float = float(os.getenv("REGION_TTL_S", "1200"))    # 20 min, same as CORE's state cache
    region_concurrency: int = int(os.getenv("REGION_CONCURRENCY", "6"))


settings = Settings()
