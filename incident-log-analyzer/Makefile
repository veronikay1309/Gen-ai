.PHONY: install generate-data run test lint clean

install:
	python3 -m venv venv
	./venv/bin/pip install -r requirements.txt

generate-data:
	./venv/bin/python3 src/generate_sample_logs.py

run:
	PYTHONPATH=. ./venv/bin/python3 src/main.py --log-file data/system.log --output-dir output

test:
	PYTHONPATH=. ./venv/bin/pytest tests/ -v --cov=src

lint:
	./venv/bin/pip install flake8 black --quiet
	./venv/bin/flake8 src tests || true
	./venv/bin/black --check src tests || true

clean:
	rm -rf __pycache__ src/__pycache__ tests/__pycache__ .pytest_cache .coverage htmlcov output/ data/ venv/
