.PHONY: install-dev test coverage lint clean

install-dev:
	pip install .[dev]

test:
	pytest

coverage:
	pytest --cov=igtools --cov-report=term-missing

clean:
	find . -type d -name "__pycache__" -exec rm -r {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete

all-test: install-dev test clean
