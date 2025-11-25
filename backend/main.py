import logging
from fastapi import FastAPI, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse

from .schemas import DownloadRequest, TaskResponse
from .downloader import DownloadManager
from .config import settings

logging.basicConfig(
    level=settings.LOG_LEVEL, format="%(asctime)s %(levelname)s: %(message)s"
)

app = FastAPI()
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)

manager = DownloadManager()


@app.post("/download", response_model=TaskResponse)
async def start_download(
    request: DownloadRequest,
    bg: BackgroundTasks,
    mgr: DownloadManager = Depends(lambda: manager),
):
    return TaskResponse(task_id=mgr.start_task(request, bg))


@app.get("/progress/{task_id}")
async def stream_progress(
    task_id: str, mgr: DownloadManager = Depends(lambda: manager)
):
    return StreamingResponse(
        mgr.generate_progress_stream(task_id), media_type="text/event-stream"
    )


@app.get("/file/{task_id}")
async def download_file(
    task_id: str, bg: BackgroundTasks, mgr: DownloadManager = Depends(lambda: manager)
):
    file_path, temp_dir = mgr.retrieve_file_path(task_id)
    bg.add_task(mgr.cleanup_resources, task_id, temp_dir)
    return FileResponse(path=file_path, filename=file_path.name)
