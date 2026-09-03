.PHONY: install install-infra run seed test lint docker-up docker-down clean

install:
	python -m pip install -e .

install-infra:
	python -m pip install -e ".[infra]"

run:
	python app.py

seed:
	python scripts/seed_demo.py

test:
	python -m unittest discover -s tests -v

lint:
	python -m compileall -q app.py src tests scripts
	python -m ruff check .

docker-up:
	docker compose up --build

docker-down:
	docker compose down

clean:
	python -c "import shutil; shutil.rmtree('runtime_data', ignore_errors=True)"
