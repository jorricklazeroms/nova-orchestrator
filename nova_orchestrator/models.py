from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

JobStatus = str


@dataclass
class JobRecord:
    id: int
    type: str
    payload: dict[str, Any]
    status: JobStatus
    created_at: datetime
    updated_at: datetime
    started_at: datetime | None
    finished_at: datetime | None
    attempt_count: int
    last_error: str | None


@dataclass
class JobLogRecord:
    id: int
    job_id: int
    level: str
    message: str
    created_at: datetime
