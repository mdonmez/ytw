from typing import Literal
from pydantic import BaseModel, field_validator
from .downloader import validate_youtube_url  # Implement function


class DownloadRequest(BaseModel):
    url: str
    type: Literal["video", "audio"] = "video"

    @field_validator("url")
    @classmethod
    def validate_youtube_url_format(cls, v: str) -> str:
        is_valid, error_msg, video_id = validate_youtube_url(v)
        if not is_valid:
            raise ValueError(error_msg)
        return v  # Return original URL if valid


class VideoMetadata(BaseModel):
    thumbnail_url: str
    title: str
    uploader: str
    duration: str  # formatted as "MM:SS"


class TaskResponse(BaseModel):
    task_id: str
    metadata: VideoMetadata


class TaskState(BaseModel):
    task_id: str
    status: Literal["preparing", "downloading", "processing", "finished", "error"]
    progress: float = 0.0
    total_bytes: int | None = None
    file_path: str | None = None
    temp_dir: str
    error: str | None = None
    metadata: dict | None = None  # NEW FIELD
    cancelled: bool = False  # NEW FIELD
