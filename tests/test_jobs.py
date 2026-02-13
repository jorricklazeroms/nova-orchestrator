from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from nova_orchestrator.api import create_app


def build_client(tmp_path: Path) -> TestClient:
    db_file = tmp_path / "jobs.sqlite3"
    app = create_app(db_path=str(db_file), disable_worker=True)
    return TestClient(app)


def test_create_job(tmp_path: Path) -> None:
    with build_client(tmp_path) as client:
        response = client.post(
            "/jobs",
            json={"type": "email", "payload": {"to": "team@example.com"}},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["id"] > 0
        assert body["status"] == "queued"
        assert body["attempt_count"] == 0


def test_process_job_to_success(tmp_path: Path) -> None:
    with build_client(tmp_path) as client:
        created = client.post("/jobs", json={"type": "sync", "payload": {"source": "crm"}}).json()
        tick = client.post("/worker/tick")
        assert tick.status_code == 200
        assert tick.json()["processed"] is True

        detail = client.get(f"/jobs/{created['id']}")
        assert detail.status_code == 200
        body = detail.json()
        assert body["status"] == "succeeded"
        assert body["attempt_count"] == 1
        assert any("completed" in log["message"].lower() for log in body["logs"])


def test_retry_failed_job(tmp_path: Path) -> None:
    with build_client(tmp_path) as client:
        created = client.post("/jobs", json={"type": "export", "payload": {"fail": True}}).json()
        client.post("/worker/tick")

        failed = client.get(f"/jobs/{created['id']}")
        assert failed.status_code == 200
        assert failed.json()["status"] == "failed"
        assert failed.json()["last_error"] == "Simulated job failure"

        retried = client.post(f"/jobs/{created['id']}/retry")
        assert retried.status_code == 200
        assert retried.json()["status"] == "queued"
        assert retried.json()["attempt_count"] == 1
