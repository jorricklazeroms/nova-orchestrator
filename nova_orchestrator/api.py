from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .service import JobService
from .store import JobStore
from .worker import JobWorker


class JobCreateRequest(BaseModel):
    type: str = Field(min_length=1)
    payload: dict[str, Any]


class JobResponse(BaseModel):
    id: int
    type: str
    payload: dict[str, Any]
    status: str
    created_at: str
    updated_at: str
    started_at: str | None
    finished_at: str | None
    attempt_count: int
    last_error: str | None


class JobDetailResponse(JobResponse):
    logs: list[dict[str, str]]


def _to_job_response(data: Any) -> JobResponse:
    return JobResponse(
        id=data.id,
        type=data.type,
        payload=data.payload,
        status=data.status,
        created_at=data.created_at.isoformat(),
        updated_at=data.updated_at.isoformat(),
        started_at=data.started_at.isoformat() if data.started_at else None,
        finished_at=data.finished_at.isoformat() if data.finished_at else None,
        attempt_count=data.attempt_count,
        last_error=data.last_error,
    )


def create_app(db_path: str | None = None, disable_worker: bool = False) -> FastAPI:
    resolved_path = db_path or str(Path(".data") / "jobs.sqlite3")
    worker_enabled = not disable_worker and os.getenv("ORCHESTRATOR_DISABLE_WORKER") != "1"

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        store = JobStore(resolved_path)
        service = JobService(store)
        app.state.service = service
        app.state.worker = None

        if worker_enabled:
            worker = JobWorker(service)
            worker.start()
            app.state.worker = worker

        try:
            yield
        finally:
            if app.state.worker is not None:
                app.state.worker.stop()

    app = FastAPI(title="Nova Orchestrator", version="0.1.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/jobs", response_model=JobResponse, status_code=201)
    def create_job(payload: JobCreateRequest) -> JobResponse:
        job = app.state.service.create_job(payload.type, payload.payload)
        return _to_job_response(job)

    @app.get("/jobs", response_model=list[JobResponse])
    def list_jobs() -> list[JobResponse]:
        jobs = app.state.service.list_jobs()
        return [_to_job_response(job) for job in jobs]

    @app.get("/jobs/{job_id}", response_model=JobDetailResponse)
    def get_job(job_id: int) -> JobDetailResponse:
        job = app.state.service.get_job(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail="Job not found")
        return JobDetailResponse(
            **_to_job_response(job).model_dump(),
            logs=app.state.service.get_job_logs(job_id),
        )

    @app.post("/jobs/{job_id}/retry", response_model=JobResponse)
    def retry_job(job_id: int) -> JobResponse:
        job = app.state.service.retry_job(job_id)
        if job is None:
            raise HTTPException(status_code=400, detail="Only failed jobs can be retried")
        return _to_job_response(job)

    @app.post("/worker/tick")
    def worker_tick() -> dict[str, bool]:
        processed = app.state.service.process_next_job()
        return {"processed": processed}

    return app
