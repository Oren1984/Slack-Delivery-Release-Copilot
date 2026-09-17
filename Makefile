.PHONY: venv install seed reset api demo test lint typecheck docker-up docker-down docker-build

venv:
	python -m venv .venv

install:
	pip install -r requirements.txt

seed:
	python scripts/seed_demo.py

reset:
	python scripts/reset_demo.py

api:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

demo:
	streamlit run demo/streamlit_app.py

test:
	pytest -q

lint:
	ruff check .

typecheck:
	mypy app

docker-build:
	docker compose build

docker-up:
	docker compose up --build

docker-down:
	docker compose down
