# Common tasks. `just` with no arguments lists them.

default:
    @just --list

# Install the package with dev tools.
install:
    pip install -e ".[dev]"

# Point git at the repo's hooks.
install-hooks:
    git config core.hooksPath .githooks

# Everything CI runs.
ci: lint test

lint:
    ruff check .
    ruff format --check .

fmt:
    ruff format .
    ruff check --fix .

test:
    pytest

# Create or update the GitHub labels.
labels:
    bash scripts/labels.sh
