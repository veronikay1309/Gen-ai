.PHONY: install generate-data run test lint clean

install:
	python3 -m venv venv
	./venv/bin/pip install -r requirements.txt

generate-data:
	./venv/bin/python3 src/generate_sample_data.py

run:
	./venv/bin/python3 -m src.pipeline --config configs/pipeline_config.yaml

test:
	PYTHONPATH=. ./venv/bin/pytest tests/ -v --cov=src

lint:
	./venv/bin/pip install flake8 black --quiet
	./venv/bin/flake8 src tests || true
	./venv/bin/black --check src tests || true

clean:
	rm -rf __pycache__ src/__pycache__ tests/__pycache__ .pytest_cache .coverage htmlcov output/ dead_letter/ venv/
