MAIN = src

.PHONY: install run debug lint lint-strict clean

install:
	uv sync

run:
	uv run python -m $(MAIN)

debug:
	uv run python -m pdb -m src

lint:
	uv run flake8 . --exclude=.venv,data
	uv run mypy . \
		--exclude '(\.venv|data)' \
		--warn-return-any \
		--warn-unused-ignores \
		--ignore-missing-imports \
		--disallow-untyped-defs \
		--check-untyped-defs

lint-strict:
	uv run flake8 .
	uv run mypy . --strict

clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	rm -rf build/ dist/ .coverage htmlcov/ .pytest_cache/
