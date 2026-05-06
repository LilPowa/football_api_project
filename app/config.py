from pathlib import Path
from dotenv import load_dotenv
import os


BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")


class Settings:
    API_FOOTBALL_KEY: str = os.getenv("API_FOOTBALL_KEY", "")
    API_FOOTBALL_BASE_URL: str = os.getenv(
        "API_FOOTBALL_BASE_URL",
        "https://v3.football.api-sports.io"
    )

    DATABASE_PATH: str = os.getenv(
        "DATABASE_PATH",
        str(BASE_DIR / "data" / "football_data.db")
    )

    @classmethod
    def validate(cls) -> None:
        if not cls.API_FOOTBALL_KEY:
            raise ValueError(
                "La variable API_FOOTBALL_KEY est manquante dans le fichier .env"
            )


settings = Settings()