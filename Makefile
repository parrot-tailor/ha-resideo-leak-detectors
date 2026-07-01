SHELL = /bin/bash

# Create the venv with the interpreter pinned in .python-version (3.14.4 via
# pyenv) and install the dev/test toolchain, which pulls the pinned Home
# Assistant (see requirements-dev.txt).
.PHONY: deps
.ONESHELL:
deps:
	set -e
	@echo "Setting up the Python environment..."
	python3 -m venv venv
	. venv/bin/activate
	pip install -U pip
	pip install -U -r requirements-dev.txt
	@echo "Dependencies installed."

# Auto-fix formatting and lint issues.
.PHONY: format
.ONESHELL:
format:
	set -e
	. venv/bin/activate
	ruff format
	ruff check --fix

.PHONY: lint
.ONESHELL:
lint:
	@echo "Running format check, lint, and typecheck..."
	set -e
	. venv/bin/activate
	ruff check
	ruff format --check --diff
	npx -y markdownlint-cli2 "*.md"
	pyright --venvpath . --warnings

.PHONY: test
.ONESHELL:
test:
	set -e
	. venv/bin/activate
	python -m pytest

# Full local gate: lint + type check + the entire test suite.
.PHONY: check
.ONESHELL:
check: lint
	@echo "Running the full test suite..."
	set -e
	. venv/bin/activate
	python -m pytest
	@echo "All checks passed."

.PHONY: clean
clean:
	@echo "Cleaning up..."
	rm -rf **/__pycache__
	rm -rf .pytest_cache .ruff_cache htmlcov
	rm -f .coverage .coverage.* junit.xml
	rm -rf venv
	@echo "Cleanup complete."
