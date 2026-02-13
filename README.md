# nova-orchestrator

[![CI](https://github.com/jorrick/nova-orchestrator/actions/workflows/ci.yml/badge.svg)](https://github.com/jorrick/nova-orchestrator/actions/workflows/ci.yml)

Nova Orchestrator v0.1 met:
- Backend: FastAPI + SQLite
- Worker: background loop voor queued jobs
- Frontend: React (Vite + TypeScript)

## Features
- `POST /jobs` om jobs te maken (`type` + JSON payload)
- `GET /jobs` met status en timestamps
- `GET /jobs/{id}` met detail + logs
- `POST /jobs/{id}/retry` om gefaalde jobs te requeuen
- `GET /health`
- Worker verwerkt jobs op de achtergrond

## Backend starten
```bash
cd nova-orchestrator
python3 -m venv .venv
source .venv/bin/activate
make dev
make api
```

API draait standaard op `http://localhost:8000`.

## Frontend starten
```bash
cd nova-orchestrator
make web-install
make web-dev
```

Frontend draait standaard op `http://localhost:5173` en praat met `http://localhost:8000`.
Zet eventueel `VITE_API_BASE` om een andere API URL te gebruiken.

## Tests en quality gates
Backend:
```bash
cd nova-orchestrator
make lint
make test
```

Frontend:
```bash
cd nova-orchestrator
make web-test
make web-build
```

## Notes
- Databasepad default: `.data/jobs.sqlite3`
- Voor tests kan de worker uitgezet worden met `ORCHESTRATOR_DISABLE_WORKER=1`

## License
MIT
