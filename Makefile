.PHONY: dev build lint format test api web-install web-dev web-build web-test

dev:
	python -m pip install --upgrade pip
	pip install -e .[dev]

build:
	python -m build

lint:
	ruff check .
	ruff format --check .

format:
	ruff format .

test:
	pytest -q

api:
	uvicorn nova_orchestrator.main:app --reload

web-install:
	cd web && npm install

web-dev:
	cd web && npm run dev

web-build:
	cd web && npm run build

web-test:
	cd web && npm run test -- --run
