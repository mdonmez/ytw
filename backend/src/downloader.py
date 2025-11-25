import asyncio
import logging
import shutil
import tempfile
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import Manager
from pathlib import Path

import yt_dlp
from fastnanoid import generate as generate_nanoid
from fastapi import BackgroundTasks, HTTPException

from .schemas import DownloadRequest, TaskState
from .config import settings

logger = logging.getLogger("Downloader")


def _download_worker(
    task_id: str, url: str, media_type: str, temp_dir: str, state: dict
):
    def update_state(**updates):
        current = state.get(task_id, {})
        current.update(updates)
        state[task_id] = current

    try:
        update_state(status="downloading", progress=0.0)

        match media_type:
            case "audio":
                download_format = "bestaudio/best"
            case "video":
                download_format = "bestvideo+bestaudio/best"

        def on_progress(d):
            if d["status"] == "downloading" and (
                total := d.get("total_bytes") or d.get("total_bytes_estimate")
            ):
                progress = round((d.get("downloaded_bytes", 0) / total) * 100, 1)
                update_state(status="downloading", progress=progress, total_bytes=total)
            elif d["status"] == "finished":
                update_state(status="processing", progress=settings.PROCESSING_PROGRESS)

        yt_dlp.YoutubeDL(
            {
                "outtmpl": str(Path(temp_dir) / "%(title)s.%(ext)s"),
                "format": download_format,
                "quiet": True,
                "no_warnings": True,
                "progress_hooks": [on_progress],
            }
        ).download([url])

        if not (files := list(Path(temp_dir).iterdir())):
            raise FileNotFoundError("No file created")

        update_state(status="done", progress=100.0, file_path=str(files[0]))

    except Exception as e:
        logger.error(f"Download failed for {task_id}: {e}")
        update_state(status="error", error=str(e))


class DownloadManager:
    def __init__(self, max_workers: int = settings.MAX_WORKERS):
        self._manager = Manager()
        self._state = self._manager.dict()
        self._pool = ProcessPoolExecutor(max_workers=max_workers)
        logger.info(f"Initialized with {max_workers} workers")

    def _get_task(self, task_id: str) -> TaskState | None:
        return TaskState(**data) if (data := self._state.get(task_id)) else None

    def start_task(
        self, request: DownloadRequest, background_tasks: BackgroundTasks
    ) -> str:
        task_id = generate_nanoid()
        temp_dir = Path(tempfile.mkdtemp(dir=settings.TEMP_DIR))

        initial = TaskState(
            task_id=task_id,
            status="queued",
            progress=0.0,
            temp_dir=str(temp_dir),
            url=request.url,
        )
        self._state[task_id] = initial.model_dump()

        self._pool.submit(
            _download_worker,
            task_id,
            request.url,
            request.type,
            str(temp_dir),
            self._state,
        )

        return task_id

    async def generate_progress_stream(self, task_id: str):
        while True:
            if not (task := self._get_task(task_id)):
                yield "data: error|Task not found\n\n"
                break

            if task.status == "error":
                yield f"data: error|{task.error}\n\n"
                break

            yield f"data: {task.progress}\n\n"

            if task.status == "done":
                yield "data: done\n\n"
                break

            await asyncio.sleep(settings.PROGRESS_UPDATE_INTERVAL)

    def retrieve_file_path(self, task_id: str) -> tuple[Path, Path]:
        if (
            not (task := self._get_task(task_id))
            or task.status != "done"
            or not task.file_path
        ):
            raise HTTPException(status_code=404, detail="File not ready or failed")

        return Path(task.file_path), Path(task.temp_dir)

    def cleanup_resources(self, task_id: str, temp_dir: Path):
        try:
            if temp_dir.exists():
                shutil.rmtree(temp_dir, ignore_errors=True)

            if task_id in self._state:
                del self._state[task_id]

            logger.info(f"Cleaned up task {task_id}")
        except Exception as e:
            logger.error(f"Cleanup error for {task_id}: {e}")
