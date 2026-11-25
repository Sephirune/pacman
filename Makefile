MAIN    = pac-man.py
CONFIG  = config.json
PYTHON  = uv run python3

.PHONY: install run debug test lint lint-strict package clean fclean

install:
	uv sync

run:
	$(PYTHON) $(MAIN) $(CONFIG)

debug:
	$(PYTHON) -m pdb $(MAIN) $(CONFIG)

test:
	uv run pytest -q

lint:
	uv run flake8 .
	uv run mypy . \
		--exclude '(\.venv|build|dist)' \
		--warn-return-any \
		--warn-unused-ignores \
		--ignore-missing-imports \
		--disallow-untyped-defs \
		--check-untyped-defs

lint-strict:
	uv run flake8 .
	uv run mypy . --strict --exclude '(\.venv|build|dist)' \
		--ignore-missing-imports

# Builds a standalone game in dist/pac-man/ (+ a zip ready for itch.io).
package:
	uv run pyinstaller --noconfirm --clean pac-man.spec
	cp $(CONFIG) dist/pac-man/
	cp PLAYING.txt dist/pac-man/
	cd dist && rm -f pac-man.zip && \
		$(PYTHON) -m zipfile -c pac-man.zip pac-man/

clean:
	find . -type f -name "*.pyc" -not -path "./.venv/*" -delete
	find . -type d -name "__pycache__" -not -path "./.venv/*" -exec rm -rf {} +
	rm -rf .mypy_cache .pytest_cache .coverage htmlcov/

fclean: clean
	rm -rf build/ dist/
