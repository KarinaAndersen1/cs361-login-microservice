.PHONY: run test lint

VENV?=.venv
PYTHON?=python

run:
	uvicorn login_service.main:app --reload --host 0.0.0.0 --port 8000

test:
	pytest -q

lint:
	$(PYTHON) -m compileall src