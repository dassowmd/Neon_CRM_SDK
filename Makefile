# Makefile for Neon CRM Python SDK

.PHONY: help install install-dev test test-verbose lint format type-check clean build publish-test publish docs serve-docs example

# Default target
help:
	@echo "Neon CRM Python SDK - Available Commands:"
	@echo ""
	@echo "Development:"
	@echo "  install       Install package in production mode"
	@echo "  install-dev   Install package in development mode with dev dependencies"
	@echo "  format        Format code with black and ruff"
	@echo "  lint          Run linting checks (ruff)"
	@echo "  type-check    Run type checking with mypy"
	@echo "  pre-commit    Install and run pre-commit hooks"
	@echo ""
	@echo "Testing:"
	@echo "  test          Run tests with coverage"
	@echo "  test-verbose  Run tests with verbose output"
	@echo "  test-watch    Run tests in watch mode"
	@echo ""
	@echo "Build & Distribution:"
	@echo "  clean         Clean build artifacts and cache files"
	@echo "  build         Build package for distribution"
	@echo "  publish-test  Publish to TestPyPI"
	@echo "  publish       Publish to PyPI"
	@echo ""
	@echo "Documentation:"
	@echo "  docs          Build documentation"
	@echo "  serve-docs    Serve documentation locally"
	@echo ""
	@echo "Examples:"
	@echo "  example       Run the basic usage example"
	@echo ""
	@echo "Utilities:"
	@echo "  check-all     Run all checks (format, lint, type-check, test)"

# Installation
install:
	pip install .

install-dev:
	pip install -e ".[dev]"

# Code quality
format:
	@echo "Formatting code with black..."
	black src/ tests/ examples/
	@echo "Sorting imports and fixing code with ruff..."
	ruff check --fix src/ tests/ examples/

lint:
	@echo "Running ruff linting..."
	ruff check src/ tests/ examples/

type-check:
	@echo "Running mypy type checking..."
	mypy src/neon_crm/

pre-commit:
	@echo "Installing pre-commit hooks..."
	pre-commit install
	@echo "Running pre-commit on all files..."
	pre-commit run --all-files

# Testing
test:
	@echo "Running tests with coverage..."
	pytest tests/ --cov=neon_crm --cov-report=term-missing --cov-report=html

test-verbose:
	@echo "Running tests with verbose output..."
	pytest tests/ -v --cov=neon_crm --cov-report=term-missing

test-watch:
	@echo "Running tests in watch mode..."
	pytest-watch tests/ -- --cov=neon_crm

# Build and distribution
clean:
	@echo "Cleaning build artifacts..."
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

build: clean
	@echo "Building package..."
	python -m build

publish-test: build
	@echo "Publishing to TestPyPI..."
	@echo "Make sure you have set up your TestPyPI credentials in ~/.pypirc"
	python -m twine upload --repository testpypi dist/*

publish: build
	@echo "Publishing to PyPI..."
	@echo "Make sure you have set up your PyPI credentials in ~/.pypirc"
	python -m twine upload dist/*

# Documentation
docs:
	@echo "Building documentation..."
	@if [ -d "docs" ]; then \
		cd docs && mkdocs build; \
	else \
		echo "Documentation directory not found. Run 'make setup-docs' first."; \
	fi

serve-docs:
	@echo "Serving documentation locally..."
	@if [ -d "docs" ]; then \
		cd docs && mkdocs serve; \
	else \
		echo "Documentation directory not found. Run 'make setup-docs' first."; \
	fi

setup-docs:
	@echo "Setting up documentation structure..."
	mkdir -p docs
	@echo "site_name: Neon CRM Python SDK" > docs/mkdocs.yml
	@echo "site_description: Python SDK for the Neon CRM API" >> docs/mkdocs.yml
	@echo "repo_url: https://github.com/your-username/neon-crm-python" >> docs/mkdocs.yml
	@echo "docs_dir: ." >> docs/mkdocs.yml
	@echo "nav:" >> docs/mkdocs.yml
	@echo "  - Home: ../README.md" >> docs/mkdocs.yml
	@echo "  - Changelog: ../CHANGELOG.md" >> docs/mkdocs.yml
	mkdir -p docs/api
	@echo "Documentation structure created in docs/"

# Examples
example:
	@echo "Running basic usage example..."
	@echo "Note: Set NEON_ORG_ID and NEON_API_KEY environment variables to test with real API"
	python examples/basic_usage.py

# Comprehensive checks
check-all: format lint type-check test
	@echo "All checks completed successfully!"

# Development workflow
dev-setup: install-dev pre-commit
	@echo "Development environment setup complete!"

# Release workflow
release-check: clean format lint type-check test build
	@echo "Release checks completed successfully!"
	@echo "Package is ready for release."
	@echo "Run 'make publish-test' to publish to TestPyPI first."

# Quick development commands
quick-test:
	@echo "Running quick tests (no coverage)..."
	pytest tests/ -x

quick-check:
	@echo "Running quick checks..."
	ruff check src/
	pytest tests/ -x

# Package info
info:
	@echo "Package Information:"
	@echo "==================="
	@python -c "import sys; sys.path.insert(0, 'src'); import neon_crm; print(f'Version: {neon_crm.__version__}')"
	@echo "Python version: $(shell python --version)"
	@echo "Installed packages:"
	@pip list | grep -E "(neon-crm|httpx|pydantic|pytest)"

# Environment checks
check-env:
	@echo "Environment Check:"
	@echo "=================="
	@echo "Python: $(shell which python)"
	@echo "Pip: $(shell which pip)"
	@echo "Virtual environment: $(VIRTUAL_ENV)"
	@if [ -f "pyproject.toml" ]; then echo "✓ pyproject.toml found"; else echo "✗ pyproject.toml missing"; fi
	@if [ -d "src/neon_crm" ]; then echo "✓ Source directory found"; else echo "✗ Source directory missing"; fi
	@if [ -d "tests" ]; then echo "✓ Tests directory found"; else echo "✗ Tests directory missing"; fi