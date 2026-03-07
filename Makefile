lint:
	ruff check .

fix:
	ruff check . --fix --unsafe-fixes

format:
	ruff format .

test:
	pytest tests/

all: fix format lint
