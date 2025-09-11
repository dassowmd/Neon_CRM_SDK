# Makefile for Neon CRM Python SDK

.PHONY: help install install-dev test test-verbose lint format type-check clean build publish-test publish docs serve-docs example

# Default target
help:
	@echo "Neon CRM Python SDK - Available Commands:"
	@echo ""
	@echo "Development:"
	@echo "  setup-dev     Set up complete development environment with venv (recommended)"
	@echo "  install       Install package in production mode"
	@echo "  install-dev   Install package in development mode with dev dependencies"
	@echo "  format        Format code with black and ruff"
	@echo "  lint          Run linting checks (ruff)"
	@echo "  type-check    Run type checking with mypy"
	@echo "  pre-commit    Install and run pre-commit hooks"
	@echo ""
	@echo "Testing:"
	@echo "  test          Run all tests with coverage"
	@echo "  test-unit     Run unit tests only (mocked, fast)"
	@echo "  test-regression-readonly   Run regression tests (read-only, safe for production)"
	@echo "  test-regression-writeops   Run regression tests (write operations, MODIFIES DATABASE)"
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

# Development environment setup
setup-dev:
	@echo "Setting up complete development environment..."
	@if [ ! -d "venv" ]; then \
		echo "Creating virtual environment..."; \
		python3 -m venv venv; \
		echo "✓ Virtual environment created in ./venv/"; \
	else \
		echo "✓ Virtual environment already exists"; \
	fi
	@echo "Installing package with dev dependencies..."
	$(PIP) install -e ".[dev]"
	@echo "✓ Package installed in development mode"
	@echo "Installing pre-commit hooks..."
	$(PYTHON) -m pre_commit install
	@echo "✓ Pre-commit hooks installed"
	@echo ""
	@echo "🎉 Development environment setup complete!"
	@echo ""
	@echo "You can now run:"
	@echo "  make test-unit              # Run unit tests"
	@echo "  make lint                   # Check code quality"
	@echo "  make format                 # Format code"
	@echo ""
	@echo "Note: All make commands automatically use the venv when available."

# Python and pip commands (auto-detect venv)
PYTHON := $(shell if [ -f "venv/bin/python" ]; then echo "venv/bin/python"; else echo "python3"; fi)
PIP := $(shell if [ -f "venv/bin/pip" ]; then echo "venv/bin/pip"; else echo "pip3"; fi)

# Installation
install:
	$(PIP) install .

install-dev:
	$(PIP) install -e ".[dev]"

# Code quality
format:
	@echo "Formatting code with black..."
	$(PYTHON) -m black src/ tests/ examples/
	@echo "Sorting imports and fixing code with ruff..."
	$(PYTHON) -m ruff check --fix src/ tests/ examples/

lint:
	@echo "Running ruff linting..."
	$(PYTHON) -m ruff check src/ tests/ examples/

type-check:
	@echo "Running mypy type checking..."
	$(PYTHON) -m mypy src/neon_crm/

pre-commit:
	@echo "Installing pre-commit hooks..."
	$(PYTHON) -m pre_commit install
	@echo "Running pre-commit on all files..."
	$(PYTHON) -m pre_commit run --all-files

# Testing
test:
	@echo "Running all tests with coverage..."
	$(PYTHON) -m pytest tests/ --cov=neon_crm --cov-report=term-missing --cov-report=html

test-unit:
	@echo "Running unit tests (mocked, fast)..."
	$(PYTHON) -m pytest tests/unit/ -m unit -v --cov=neon_crm --cov-report=term-missing

test-regression-readonly:
	@echo "Running regression tests (read-only operations)..."
	@echo "⚠️  These tests connect to the actual Neon CRM API but only perform read operations."
	@echo "   Set NEON_ORG_ID and NEON_API_KEY environment variables."
	@echo "   Set NEON_ENVIRONMENT=production for production or leave unset for trial."
	@echo ""
	$(PYTHON) -m pytest tests/regression/test_readonly.py -m "regression and readonly" -v -s

test-regression-writeops:
	@echo "🚨 WARNING: WRITE OPERATIONS TESTS 🚨"
	@echo "These tests will CREATE, UPDATE, and DELETE records in your Neon CRM database!"
	@echo "Required environment variables:"
	@echo "  NEON_ORG_ID=your_org_id"
	@echo "  NEON_API_KEY=your_api_key"
	@echo "  NEON_ENVIRONMENT=trial (NEVER use production!)"
	@echo "  NEON_ALLOW_WRITE_TESTS=true (explicit confirmation required)"
	@echo ""
	@echo "Press Ctrl+C now to cancel, or Enter to continue..."
	@read confirm
	$(PYTHON) -m pytest tests/regression/test_writeops.py -m "regression and writeops" -v -s

test-verbose:
	@echo "Running tests with verbose output..."
	$(PYTHON) -m pytest tests/ -v --cov=neon_crm --cov-report=term-missing

test-watch:
	@echo "Running tests in watch mode..."
	$(PYTHON) -m pytest_watch tests/ -- --cov=neon_crm

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
	$(PYTHON) -m build

publish-test: build
	@echo "Publishing to TestPyPI..."
	@echo "Make sure you have set up your TestPyPI credentials in ~/.pypirc"
	$(PYTHON) -m twine upload --repository testpypi dist/*

publish: build
	@echo "Publishing to PyPI..."
	@echo "Make sure you have set up your PyPI credentials in ~/.pypirc"
	$(PYTHON) -m twine upload dist/*

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
	$(PYTHON) examples/basic_usage.py

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
	$(PYTHON) -m pytest tests/ -x

quick-check:
	@echo "Running quick checks..."
	$(PYTHON) -m ruff check src/
	$(PYTHON) -m pytest tests/ -x

# Package info
info:
	@echo "Package Information:"
	@echo "==================="
	@$(PYTHON) -c "import sys; sys.path.insert(0, 'src'); import neon_crm; print(f'Version: {neon_crm.__version__}')"
	@echo "Python version: $(shell $(PYTHON) --version)"
	@echo "Python path: $(PYTHON)"
	@echo "Pip path: $(PIP)"
	@echo "Installed packages:"
	@$(PIP) list | grep -E "(neon-crm|httpx|pydantic|pytest)"

# Environment checks
check-env:
	@echo "Environment Check:"
	@echo "=================="
	@echo "Python: $(PYTHON)"
	@echo "Pip: $(PIP)"
	@echo "Virtual environment: $(if $(findstring venv,$(PYTHON)),✓ Using venv,⚠️  Not using venv)"
	@if [ -f "pyproject.toml" ]; then echo "✓ pyproject.toml found"; else echo "✗ pyproject.toml missing"; fi
	@if [ -d "src/neon_crm" ]; then echo "✓ Source directory found"; else echo "✗ Source directory missing"; fi
	@if [ -d "tests" ]; then echo "✓ Tests directory found"; else echo "✗ Tests directory missing"; fi
