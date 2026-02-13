from __future__ import annotations

from typing import Any

from .models import JobRecord
from .store import JobStore


class JobService:
    def __init__(self, store: JobStore) -> None:
        self.store = store

    def create_job(self, job_type: str, payload: dict[str, Any]) -> JobRecord:
        return self.store.create_job(job_type, payload)

    def list_jobs(self) -> list[JobRecord]:
        return self.store.list_jobs()

    def get_job(self, job_id: int) -> JobRecord | None:
        return self.store.get_job(job_id)

    def get_job_logs(self, job_id: int) -> list[dict[str, str]]:
        logs = self.store.get_job_logs(job_id)
        return [
            {
                "level": item.level,
                "message": item.message,
                "created_at": item.created_at.isoformat(),
            }
            for item in logs
        ]

    def retry_job(self, job_id: int) -> JobRecord | None:
        return self.store.retry_job(job_id)

    def process_next_job(self) -> bool:
        next_job = self.store.fetch_next_queued_job()
        if next_job is None:
            return False

        self.store.mark_running(next_job.id)
        try:
            self._process_payload(next_job.payload)
            self.store.mark_succeeded(next_job.id)
        except Exception as exc:  # noqa: BLE001
            self.store.mark_failed(next_job.id, str(exc))
        return True

    @staticmethod
    def _process_payload(payload: dict[str, Any]) -> None:
        if payload.get("fail") is True or payload.get("should_fail") is True:
            raise RuntimeError("Simulated job failure")
