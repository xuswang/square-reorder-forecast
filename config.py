import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()

DEFAULT_HISTORY_DAYS = 90
DEFAULT_FORECAST_DAYS = 30
DEFAULT_SAFETY_STOCK_Z = 1.65


@dataclass(frozen=True)
class Settings:
    access_token: str
    environment: str
    location_id: str | None
    history_days: int
    forecast_days: int
    safety_stock_z: float

    @classmethod
    def from_values(
        cls,
        access_token: str,
        *,
        environment: str = "production",
        location_id: str | None = None,
        history_days: int = DEFAULT_HISTORY_DAYS,
        forecast_days: int = DEFAULT_FORECAST_DAYS,
        safety_stock_z: float = DEFAULT_SAFETY_STOCK_Z,
    ) -> "Settings":
        token = access_token.strip()
        if not token:
            raise ValueError("ERR_MISSING_TOKEN")
        env = environment.strip().lower()
        if env not in ("production", "sandbox"):
            raise ValueError("ERR_INVALID_ENV")
        loc = location_id.strip() if location_id else None
        return cls(
            access_token=token,
            environment=env,
            location_id=loc or None,
            history_days=history_days,
            forecast_days=forecast_days,
            safety_stock_z=safety_stock_z,
        )

    @classmethod
    def from_env(cls) -> "Settings":
        token = os.getenv("SQUARE_ACCESS_TOKEN", "").strip()
        if not token:
            raise ValueError(
                "SQUARE_ACCESS_TOKEN is not set. Enter it in the app, or create a .env file."
            )
        return cls.from_values(
            token,
            environment=os.getenv("SQUARE_ENVIRONMENT", "production"),
            location_id=os.getenv("SQUARE_LOCATION_ID", "").strip() or None,
            history_days=int(os.getenv("HISTORY_DAYS", str(DEFAULT_HISTORY_DAYS))),
            forecast_days=int(os.getenv("FORECAST_DAYS", str(DEFAULT_FORECAST_DAYS))),
            safety_stock_z=float(os.getenv("SAFETY_STOCK_Z", str(DEFAULT_SAFETY_STOCK_Z))),
        )

    @classmethod
    def env_defaults(cls) -> dict:
        """返回 .env 中的默认值（若存在），供界面预填。"""
        return {
            "access_token": os.getenv("SQUARE_ACCESS_TOKEN", "").strip(),
            "environment": os.getenv("SQUARE_ENVIRONMENT", "production").strip().lower()
            or "production",
            "location_id": os.getenv("SQUARE_LOCATION_ID", "").strip(),
            "history_days": int(os.getenv("HISTORY_DAYS", str(DEFAULT_HISTORY_DAYS))),
            "forecast_days": int(os.getenv("FORECAST_DAYS", str(DEFAULT_FORECAST_DAYS))),
            "safety_stock_z": float(os.getenv("SAFETY_STOCK_Z", str(DEFAULT_SAFETY_STOCK_Z))),
        }
