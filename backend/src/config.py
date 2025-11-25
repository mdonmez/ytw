from pydantic_settings import BaseSettings
from pathlib import Path
import tempfile


class Settings(BaseSettings):
    TEMP_DIR: Path = Path(tempfile.gettempdir())
    LOG_LEVEL: str = "INFO"

    MAX_WORKERS: int = 100
    PROGRESS_UPDATE_INTERVAL: float = 0.5
    PROCESSING_PROGRESS: float = 99.0


settings = Settings()
