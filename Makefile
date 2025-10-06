# Makefile for Neon CRM Python SDK

.PHONY: help install install-dev test test-unit test-regression-readonly test-regression-writeops test-regression-all test-verbose test-watch list-regression-resources test-resource test-resource-readonly test-resource-writeops test-notebooks test-notebooks-examples test-notebooks-analysis lint format type-check clean build publish-test publish docs-build docs-serve docs-deploy docs-check api-schemas api-validate api-serve api-clean example clean-notebooks

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
	@echo "  test-regression-all        Run all regression tests (read-only + write operations)"
	@echo "  test-verbose  Run tests with verbose output"
	@echo "  test-watch    Run tests in watch mode"
	@echo ""
	@echo "Notebook Testing:"
	@echo "  test-notebooks              Execute all notebooks to verify they run without errors"
	@echo "  test-notebooks-examples     Execute only example notebooks"
	@echo "  test-notebooks-analysis     Execute only analysis notebooks"
	@echo ""
	@echo "Resource-specific Testing:"
	@echo "  list-regression-resources  List all available regression test resources"
	@echo "  test-resource RESOURCE=<name>          Run all tests for specific resource"
	@echo "  test-resource-readonly RESOURCE=<name> Run read-only tests for specific resource"
	@echo "  test-resource-writeops RESOURCE=<name> Run write tests for specific resource"
	@echo ""
	@echo "Build & Distribution:"
	@echo "  clean         Clean build artifacts and cache files"
	@echo "  build         Build package for distribution"
	@echo "  publish-test  Publish to TestPyPI"
	@echo "  publish       Publish to PyPI"
	@echo ""
	@echo "Documentation:"
	@echo "  docs-build    Build user documentation website (MkDocs)"
	@echo "  docs-serve    Serve documentation locally with live reload"
	@echo "  docs-deploy   Deploy documentation to GitHub Pages"
	@echo "  docs-check    Check documentation build with strict warnings"
	@echo ""
	@echo "API Schemas (for tooling):"
	@echo "  api-schemas   Generate machine-readable API schemas (OpenAPI, JSON)"
	@echo "  api-validate  Validate OpenAPI specification"
	@echo "  api-serve     Serve OpenAPI spec in Swagger UI"
	@echo "  api-clean     Clean generated API schema files"
	@echo ""
	@echo "Examples:"
	@echo "  example       Run the basic usage example"
	@echo ""
	@echo "Utilities:"
	@echo "  check-all     Run all checks (format, lint, type-check, test)"
	@echo "  clean-notebooks Clear all output from Jupyter notebooks"

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
	@echo "Running flake8 linting..."
	$(PYTHON) -m flake8 src/ tests/ examples/

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
	$(PYTHON) -m pytest tests/unit/ -v --cov=neon_crm --cov-report=term-missing

test-regression-readonly:
	@echo "Running regression tests (read-only operations)..."
	@echo "⚠️  These tests connect to the actual Neon CRM API but only perform read operations."
	@echo "   Set NEON_ORG_ID and NEON_API_KEY environment variables."
	@echo "   Set NEON_ENVIRONMENT=production for production or leave unset for trial."
	@echo ""
	$(PYTHON) -m pytest tests/regression/resources/ -m "regression and readonly" -v -s

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
	$(PYTHON) -m pytest tests/regression/resources/ -m "regression and writeops" -v -s

test-regression-all:
	@echo "🚨 WARNING: ALL REGRESSION TESTS 🚨"
	@echo "These tests will connect to the Neon CRM API and may modify data!"
	@echo "Required environment variables:"
	@echo "  NEON_ORG_ID=your_org_id"
	@echo "  NEON_API_KEY=your_api_key"
	@echo "  NEON_ENVIRONMENT=trial (recommended, NEVER use production for write tests!)"
	@echo ""
	@echo "Press Ctrl+C now to cancel, or Enter to continue..."
	@read confirm
	$(PYTHON) -m pytest tests/regression/resources/ -m "regression" -v -s

list-regression-resources:
	@echo "Available regression test resources:"
	@echo "=================================="
	@echo "  accounts            - Account management tests"
	@echo "  activities          - Activity tracking tests"
	@echo "  base_resource       - Base resource functionality tests"
	@echo "  campaigns           - Campaign management tests"
	@echo "  custom_fields       - Custom field configuration tests"
	@echo "  custom_objects      - Custom object tests"
	@echo "  donations           - Donation processing tests"
	@echo "  events              - Event management tests"
	@echo "  grants              - Grant tracking tests"
	@echo "  households          - Household management tests"
	@echo "  memberships         - Membership management tests"
	@echo "  online_store        - Online store tests"
	@echo "  orders              - Order processing tests"
	@echo "  payments            - Payment processing tests"
	@echo "  pledges             - Pledge management tests"
	@echo "  properties          - Property management tests"
	@echo "  recurring_donations - Recurring donation tests"
	@echo "  soft_credits        - Soft credit tests"
	@echo "  volunteers          - Volunteer management tests"
	@echo "  webhooks            - Webhook configuration tests"
	@echo ""
	@echo "Usage examples:"
	@echo "  make test-resource RESOURCE=accounts"
	@echo "  make test-resource-readonly RESOURCE=donations"
	@echo "  make test-resource-writeops RESOURCE=webhooks"

test-resource:
	@if [ -z "$(RESOURCE)" ]; then \
		echo "❌ Error: RESOURCE parameter is required"; \
		echo "Usage: make test-resource RESOURCE=accounts"; \
		echo "Run 'make list-regression-resources' to see available resources"; \
		exit 1; \
	fi
	@if [ ! -f "tests/regression/resources/test_$(RESOURCE).py" ]; then \
		echo "❌ Error: Resource '$(RESOURCE)' not found"; \
		echo "Run 'make list-regression-resources' to see available resources"; \
		exit 1; \
	fi
	@echo "Running all tests for resource: $(RESOURCE)"
	$(PYTHON) -m pytest tests/regression/resources/test_$(RESOURCE).py -m "regression" -v -s

test-resource-readonly:
	@if [ -z "$(RESOURCE)" ]; then \
		echo "❌ Error: RESOURCE parameter is required"; \
		echo "Usage: make test-resource-readonly RESOURCE=accounts"; \
		exit 1; \
	fi
	@if [ ! -f "tests/regression/resources/test_$(RESOURCE).py" ]; then \
		echo "❌ Error: Resource '$(RESOURCE)' not found"; \
		echo "Run 'make list-regression-resources' to see available resources"; \
		exit 1; \
	fi
	@echo "Running read-only tests for resource: $(RESOURCE)"
	$(PYTHON) -m pytest tests/regression/resources/test_$(RESOURCE).py -m "regression and readonly" -v -s

test-resource-writeops:
	@if [ -z "$(RESOURCE)" ]; then \
		echo "❌ Error: RESOURCE parameter is required"; \
		echo "Usage: make test-resource-writeops RESOURCE=accounts"; \
		exit 1; \
	fi
	@if [ ! -f "tests/regression/resources/test_$(RESOURCE).py" ]; then \
		echo "❌ Error: Resource '$(RESOURCE)' not found"; \
		echo "Run 'make list-regression-resources' to see available resources"; \
		exit 1; \
	fi
	@echo "🚨 WARNING: WRITE OPERATIONS TEST FOR $(RESOURCE) 🚨"
	@echo "This will CREATE, UPDATE, and DELETE $(RESOURCE) records!"
	@echo "Press Ctrl+C now to cancel, or Enter to continue..."
	@read confirm
	$(PYTHON) -m pytest tests/regression/resources/test_$(RESOURCE).py -m "regression and writeops" -v -s

test-verbose:
	@echo "Running tests with verbose output..."
	$(PYTHON) -m pytest tests/ -v --cov=neon_crm --cov-report=term-missing

test-watch:
	@echo "Running tests in watch mode..."
	$(PYTHON) -m pytest_watch tests/ -- --cov=neon_crm

# Notebook testing
test-notebooks:
	@echo "🧪 Executing all notebooks as regression tests..."
	@echo "⚠️  This will execute all example and analysis notebooks."
	@echo "   Notebooks will be executed in-place and may modify cell outputs."
	@echo "   Set NEON_ORG_ID and NEON_API_KEY environment variables to test with real API."
	@echo ""
	$(PYTHON) test_notebooks_execution.py

test-notebooks-examples:
	@echo "🧪 Executing example notebooks..."
	@echo "⚠️  This will execute all notebooks in examples/ directory."
	@echo ""
	$(PYTHON) test_notebooks_execution.py --pattern "examples/*.ipynb"

test-notebooks-analysis:
	@echo "🧪 Executing analysis notebooks..."
	@echo "⚠️  This will execute all notebooks in analysis/ directory."
	@echo ""
	$(PYTHON) test_notebooks_execution.py --pattern "analysis/*.ipynb"

# Build and distribution
clean: docs-clean
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

# Documentation (User-facing website)
docs-build: ## Build user documentation website (MkDocs)
	@echo "Installing documentation dependencies..."
	$(PIP) install -r docs/requirements.txt
	@echo "Building MkDocs documentation..."
	mkdocs build
	@echo "✅ Documentation built in ./site/"
	@echo "   Open ./site/index.html in your browser to view"

docs-serve: ## Serve documentation locally with live reload
	@echo "Installing documentation dependencies..."
	$(PIP) install -r docs/requirements.txt
	@echo "Starting MkDocs development server..."
	@echo "📖 Documentation will be available at: http://127.0.0.1:8000"
	@echo "   Press Ctrl+C to stop the server"
	@echo "   Changes to markdown files will automatically reload"
	mkdocs serve

docs-deploy: docs-build ## Deploy documentation to GitHub Pages
	@echo "Deploying documentation to GitHub Pages..."
	@echo "⚠️  This will push to the gh-pages branch"
	@echo "   Make sure you have push access to the repository"
	mkdocs gh-deploy --clean
	@echo "✅ Documentation deployed to GitHub Pages"

docs-check: ## Check documentation build with strict warnings
	@echo "Installing documentation dependencies..."
	$(PIP) install -r docs/requirements.txt
	@echo "Checking MkDocs build with strict mode..."
	mkdocs build --strict
	@echo "✅ Documentation build passed strict checks"

# API Schemas (Machine-readable, for tooling)
api-schemas: ## Generate machine-readable API schemas (OpenAPI, JSON)
	@echo "Generating machine-readable schemas..."
	$(PYTHON) tools/generate_schemas.py
	@echo "✅ API schemas generated successfully!"
	@echo ""
	@echo "Generated files:"
	@echo "  📄 docs/api/openapi.yaml - OpenAPI 3.0 specification"
	@echo "  📄 docs/api/capabilities.yaml - Resource capabilities matrix"
	@echo "  📄 docs/api/field_discovery.yaml - Field discovery documentation"
	@echo "  📄 docs/api/schemas.json - Complete SDK schemas"
	@echo "  📄 docs/api/resource_metadata.json - Resource metadata"
	@echo "  📄 docs/api/types.json - Type definitions"
	@echo "  📄 docs/api/capabilities.json - JSON capabilities matrix"

api-validate: ## Validate OpenAPI specification
	@echo "Validating API specifications..."
	$(PYTHON) tools/validate_openapi.py

api-serve: api-schemas ## Serve OpenAPI spec in Swagger UI
	@echo "Starting API documentation server..."
	@echo "OpenAPI spec will be available at: http://localhost:8080"
	@if command -v swagger-ui-serve >/dev/null 2>&1; then \
		swagger-ui-serve docs/api/openapi.yaml -p 8080; \
	elif command -v npx >/dev/null 2>&1; then \
		npx @apidevtools/swagger-ui-cli -f docs/api/openapi.yaml -p 8080; \
	else \
		echo "❌ No OpenAPI viewer found. Install swagger-ui-serve or npx"; \
		echo "You can view the spec at: docs/api/openapi.yaml"; \
	fi

api-clean: ## Clean generated API schema files
	@echo "Cleaning generated API schemas..."
	@rm -f docs/api/schemas.json
	@rm -f docs/api/resource_metadata.json
	@rm -f docs/api/types.json
	@rm -f docs/api/capabilities.json
	@echo "✅ API schemas cleaned"

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

# Notebook utilities
clean-notebooks:
	@echo "🧹 Clearing output from all Jupyter notebooks..."
	@echo "This will remove all cell outputs while preserving the code and markdown."
	@echo ""
	@if command -v nbstripout >/dev/null 2>&1; then \
		echo "Using nbstripout (recommended)..."; \
		find . -name "*.ipynb" -not -path "./venv/*" -not -path "./.git/*" -exec nbstripout {} \; && \
		echo "✅ All notebooks cleared using nbstripout"; \
	elif command -v jupyter >/dev/null 2>&1; then \
		echo "Using jupyter nbconvert..."; \
		find . -name "*.ipynb" -not -path "./venv/*" -not -path "./.git/*" -exec jupyter nbconvert --clear-output --inplace {} \; && \
		echo "✅ All notebooks cleared using jupyter nbconvert"; \
	else \
		echo "Using Python fallback method..."; \
		find . -name "*.ipynb" -not -path "./venv/*" -not -path "./.git/*" | while read notebook; do \
			echo "🔄 Clearing: $$notebook"; \
			$(PYTHON) -c "import json; nb=json.load(open('$$notebook')); [c.pop('outputs',None) or c.pop('execution_count',None) for c in nb.get('cells',[])]; json.dump(nb,open('$$notebook','w'),indent=1)" && \
			echo "  ✅ Cleared: $$notebook" || echo "  ❌ Failed: $$notebook"; \
		done; \
		echo "✅ All notebooks processed using Python fallback"; \
	fi
	@echo ""
	@echo "📝 To install nbstripout for better performance: pip install nbstripout"
