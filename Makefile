format:
	python3 -m ruff check . --fix

test:
	python3 -m pytest microtrax/tests --cov=microtrax --cov-report=html --cov-report=term-missing