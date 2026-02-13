from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

from .models import JobLogRecord, JobRecord


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def datetime_to_str(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.isoformat()


def str_to_datetime(value: str | None) -> datetime | None:
    if value is None:
        return None
    return datetime.fromisoformat(value)


class JobStore:
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    type TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    started_at TEXT,
                    finished_at TEXT,
                    attempt_count INTEGER NOT NULL DEFAULT 0,
                    last_error TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS job_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id INTEGER NOT NULL,
                    level TEXT NOT NULL,
                    message TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(job_id) REFERENCES jobs(id)
                )
                """
            )

    def create_job(self, job_type: str, payload: dict[str, Any]) -> JobRecord:
        now = utc_now()
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO jobs (type, payload, status, created_at, updated_at)
                VALUES (?, ?, 'queued', ?, ?)
                """,
                (job_type, json.dumps(payload), datetime_to_str(now), datetime_to_str(now)),
            )
            job_id = int(cursor.lastrowid)
            self._insert_log(conn, job_id, "info", "Job queued")
            row = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
        return self._row_to_job(row)

    def list_jobs(self) -> list[JobRecord]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM jobs ORDER BY id DESC").fetchall()
        return [self._row_to_job(row) for row in rows]

    def get_job(self, job_id: int) -> JobRecord | None:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
        if row is None:
            return None
        return self._row_to_job(row)

    def get_job_logs(self, job_id: int) -> list[JobLogRecord]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM job_logs WHERE job_id = ? ORDER BY id ASC", (job_id,)
            ).fetchall()
        return [self._row_to_log(row) for row in rows]

    def fetch_next_queued_job(self) -> JobRecord | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM jobs WHERE status = 'queued' ORDER BY id ASC LIMIT 1"
            ).fetchone()
        if row is None:
            return None
        return self._row_to_job(row)

    def mark_running(self, job_id: int) -> None:
        now = utc_now()
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE jobs
                SET status = 'running',
                    started_at = ?,
                    updated_at = ?,
                    last_error = NULL
                WHERE id = ?
                """,
                (datetime_to_str(now), datetime_to_str(now), job_id),
            )
            self._insert_log(conn, job_id, "info", "Job started")

    def mark_succeeded(self, job_id: int) -> None:
        now = utc_now()
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE jobs
                SET status = 'succeeded',
                    finished_at = ?,
                    updated_at = ?,
                    attempt_count = attempt_count + 1,
                    last_error = NULL
                WHERE id = ?
                """,
                (datetime_to_str(now), datetime_to_str(now), job_id),
            )
            self._insert_log(conn, job_id, "info", "Job completed")

    def mark_failed(self, job_id: int, message: str) -> None:
        now = utc_now()
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE jobs
                SET status = 'failed',
                    finished_at = ?,
                    updated_at = ?,
                    attempt_count = attempt_count + 1,
                    last_error = ?
                WHERE id = ?
                """,
                (datetime_to_str(now), datetime_to_str(now), message, job_id),
            )
            self._insert_log(conn, job_id, "error", f"Job failed: {message}")

    def retry_job(self, job_id: int) -> JobRecord | None:
        now = utc_now()
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
            if row is None or row["status"] != "failed":
                return None
            conn.execute(
                """
                UPDATE jobs
                SET status = 'queued',
                    updated_at = ?,
                    started_at = NULL,
                    finished_at = NULL,
                    last_error = NULL
                WHERE id = ?
                """,
                (datetime_to_str(now), job_id),
            )
            self._insert_log(conn, job_id, "info", "Job retried")
            updated = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
        return self._row_to_job(updated)

    def _insert_log(self, conn: sqlite3.Connection, job_id: int, level: str, message: str) -> None:
        conn.execute(
            """
            INSERT INTO job_logs (job_id, level, message, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (job_id, level, message, datetime_to_str(utc_now())),
        )

    @staticmethod
    def _row_to_job(row: sqlite3.Row) -> JobRecord:
        return JobRecord(
            id=int(row["id"]),
            type=str(row["type"]),
            payload=json.loads(str(row["payload"])),
            status=str(row["status"]),
            created_at=str_to_datetime(row["created_at"]) or utc_now(),
            updated_at=str_to_datetime(row["updated_at"]) or utc_now(),
            started_at=str_to_datetime(row["started_at"]),
            finished_at=str_to_datetime(row["finished_at"]),
            attempt_count=int(row["attempt_count"]),
            last_error=row["last_error"],
        )

    @staticmethod
    def _row_to_log(row: sqlite3.Row) -> JobLogRecord:
        return JobLogRecord(
            id=int(row["id"]),
            job_id=int(row["job_id"]),
            level=str(row["level"]),
            message=str(row["message"]),
            created_at=str_to_datetime(row["created_at"]) or utc_now(),
        )
