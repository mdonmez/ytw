from typing import Literal
from pydantic import BaseModel


class DownloadRequest(BaseModel):
    url: str
    type: Literal["video", "audio"] = "video"


class TaskResponse(BaseModel):
    task_id: str


class TaskState(BaseModel):
    task_id: str
    status: Literal["starting", "downloading", "processing", "done", "error"]
    progress: float = 0.0
    total_bytes: int | None = None
    file_path: str | None = None
    temp_dir: str
    error: str | None = None
