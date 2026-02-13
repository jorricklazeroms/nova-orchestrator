from __future__ import annotations

import threading
from time import sleep

from .service import JobService


class JobWorker:
    def __init__(self, service: JobService, interval_seconds: float = 0.5) -> None:
        self._service = service
        self._interval_seconds = interval_seconds
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)

    def start(self) -> None:
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        self._thread.join(timeout=2)

    def _run_loop(self) -> None:
        while not self._stop.is_set():
            self._service.process_next_job()
            sleep(self._interval_seconds)
