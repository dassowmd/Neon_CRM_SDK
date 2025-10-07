# Justfile for Neon CRM Python SDK
# https://github.com/casey/just

# Python and pip commands (auto-detect venv)
python := if path_exists("venv/bin/python") == "true" { "venv/bin/python" } else { "python3" }
pip := if path_exists("venv/bin/pip") == "true" { "venv/bin/pip" } else { "pip3" }

# Default recipe (list all recipes)
default:
    @just --list

# Show help information
help:
    @echo "Neon CRM Python SDK - Available Commands:"
    @echo ""
    @echo "Development:"
    @echo "  just setup-dev     Set up complete development environment with venv"
    @echo "  just install       Install package in production mode"
    @echo "  just install-dev   Install package in development mode with dev dependencies"
    @echo "  just format        Format code with black and ruff"
    @echo "  just lint          Run linting checks (ruff)"
    @echo "  just type-check    Run type checking with mypy"
    @echo "  just pre-commit    Install and run pre-commit hooks"
    @echo ""
    @echo "Testing:"
    @echo "  just test                      Run all tests with coverage"
    @echo "  just test-unit                 Run unit tests only (mocked, fast)"
    @echo "  just test-regression-readonly  Run regression tests (read-only, safe)"
    @echo "  just test-regression-writeops  Run regression tests (MODIFIES DATABASE)"
    @echo "  just test-regression-all       Run all regression tests"
    @echo "  just test-verbose              Run tests with verbose output"
    @echo "  just test-watch                Run tests in watch mode"
    @echo ""
    @echo "Notebook Testing:"
    @echo "  just test-notebooks          Execute all notebooks"
    @echo "  just test-notebooks-examples Execute only example notebooks"
    @echo "  just test-notebooks-analysis Execute only analysis notebooks"
    @echo ""
    @echo "Resource-specific Testing:"
    @echo "  just list-regression-resources        List available test resources"
    @echo "  just test-resource <name>             Run all tests for resource"
    @echo "  just test-resource-readonly <name>    Run read-only tests for resource"
    @echo "  just test-resource-writeops <name>    Run write tests for resource"
    @echo ""
    @echo "Build & Distribution:"
    @echo "  just clean         Clean build artifacts and cache files"
    @echo "  just build         Build package for distribution"
    @echo "  just publish-test  Publish to TestPyPI"
    @echo "  just publish       Publish to PyPI"
    @echo ""
    @echo "Documentation:"
    @echo "  just docs-build    Build user documentation website (MkDocs)"
    @echo "  just docs-serve    Serve documentation locally with live reload"
    @echo "  just docs-check    Check documentation build with strict warnings"
    @echo ""
    @echo "API Schemas (for tooling):"
    @echo "  just api-schemas   Generate machine-readable API schemas (OpenAPI, JSON)"
    @echo "  just api-validate  Validate OpenAPI specification"
    @echo "  just api-serve     Serve OpenAPI spec in Swagger UI"
    @echo "  just api-clean     Clean generated API schema files"
    @echo ""
    @echo "Examples:"
    @echo "  just example       Run the basic usage example"
    @echo ""
    @echo "Utilities:"
    @echo "  just check-all      Run all checks (format, lint, type-check, test)"
    @echo "  just clean-notebooks Clear all output from Jupyter notebooks"
    @echo "  just info           Show package information"
    @echo "  just check-env      Check environment setup"

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
    {{pip}} install -e ".[dev]"
    @echo "✓ Package installed in development mode"
    @echo "Installing pre-commit hooks..."
    {{python}} -m pre_commit install
    @echo "✓ Pre-commit hooks installed"
    @echo ""
    @echo "🎉 Development environment setup complete!"
    @echo ""
    @echo "You can now run:"
    @echo "  just test-unit    # Run unit tests"
    @echo "  just lint         # Check code quality"
    @echo "  just format       # Format code"

# Installation
install:
    {{pip}} install .

install-dev:
    {{pip}} install -e ".[dev]"

# Code quality
format:
    @echo "Formatting code with black..."
    {{python}} -m black src/ tests/ examples/
    @echo "Sorting imports and fixing code with ruff..."
    {{python}} -m ruff check --fix src/ tests/ examples/

lint:
    @echo "Running ruff linting..."
    {{python}} -m ruff check src/ tests/ examples/
    @echo "Running flake8 linting..."
    {{python}} -m flake8 src/ tests/ examples/

type-check:
    @echo "Running mypy type checking..."
    {{python}} -m mypy src/neon_crm/

pre-commit:
    @echo "Installing pre-commit hooks..."
    {{python}} -m pre_commit install
    @echo "Running pre-commit on all files..."
    {{python}} -m pre_commit run --all-files

# Testing
test:
    @echo "Running all tests with coverage..."
    {{python}} -m pytest tests/ --cov=neon_crm --cov-report=term-missing --cov-report=html

test-unit:
    @echo "Running unit tests (mocked, fast)..."
    {{python}} -m pytest tests/unit/ -v --cov=neon_crm --cov-report=term-missing

test-regression-readonly:
    @echo "Running regression tests (read-only operations)..."
    @echo "⚠️  These tests connect to the actual Neon CRM API but only perform read operations."
    @echo "   Set NEON_ORG_ID and NEON_API_KEY environment variables."
    @echo ""
    {{python}} -m pytest tests/regression/resources/ -m "regression and readonly" -v -s

test-regression-writeops:
    @echo "🚨 WARNING: WRITE OPERATIONS TESTS 🚨"
    @echo "These tests will CREATE, UPDATE, and DELETE records in your Neon CRM database!"
    @echo "Required environment variables:"
    @echo "  NEON_ORG_ID=your_org_id"
    @echo "  NEON_API_KEY=your_api_key"
    @echo "  NEON_ENVIRONMENT=trial (NEVER use production!)"
    @echo "  NEON_ALLOW_WRITE_TESTS=true"
    @echo ""
    @echo "Press Ctrl+C now to cancel, or Enter to continue..."
    @read confirm
    {{python}} -m pytest tests/regression/resources/ -m "regression and writeops" -v -s

test-regression-all:
    @echo "🚨 WARNING: ALL REGRESSION TESTS 🚨"
    @echo "These tests will connect to the Neon CRM API and may modify data!"
    @echo "Press Ctrl+C now to cancel, or Enter to continue..."
    @read confirm
    {{python}} -m pytest tests/regression/resources/ -m "regression" -v -s

test-verbose:
    {{python}} -m pytest tests/ -v --cov=neon_crm --cov-report=term-missing

test-watch:
    {{python}} -m pytest_watch tests/ -- --cov=neon_crm

# Notebook testing
test-notebooks:
    @echo "🧪 Executing all notebooks as regression tests..."
    @echo "⚠️  This will execute all example and analysis notebooks."
    @echo "   Set NEON_ORG_ID and NEON_API_KEY environment variables."
    @echo ""
    {{python}} test_notebooks_execution.py

test-notebooks-examples:
    @echo "🧪 Executing example notebooks..."
    {{python}} test_notebooks_execution.py --pattern "examples/*.ipynb"

test-notebooks-analysis:
    @echo "🧪 Executing analysis notebooks..."
    {{python}} test_notebooks_execution.py --pattern "analysis/*.ipynb"

# Resource-specific testing
list-regression-resources:
    @echo "Available regression test resources:"
    @echo "===================================="
    @echo "  accounts            - Account management tests"
    @echo "  activities          - Activity tracking tests"
    @echo "  campaigns           - Campaign management tests"
    @echo "  custom_fields       - Custom field configuration tests"
    @echo "  donations           - Donation processing tests"
    @echo "  events              - Event management tests"
    @echo "  memberships         - Membership management tests"
    @echo "  volunteers          - Volunteer management tests"
    @echo "  webhooks            - Webhook configuration tests"
    @echo ""
    @echo "Usage: just test-resource <name>"

test-resource resource:
    #!/usr/bin/env bash
    if [ ! -f "tests/regression/resources/test_{{resource}}.py" ]; then
        echo "❌ Error: Resource '{{resource}}' not found"
        echo "Run 'just list-regression-resources' to see available resources"
        exit 1
    fi
    echo "Running all tests for resource: {{resource}}"
    {{python}} -m pytest tests/regression/resources/test_{{resource}}.py -m "regression" -v -s

test-resource-readonly resource:
    #!/usr/bin/env bash
    if [ ! -f "tests/regression/resources/test_{{resource}}.py" ]; then
        echo "❌ Error: Resource '{{resource}}' not found"
        exit 1
    fi
    echo "Running read-only tests for resource: {{resource}}"
    {{python}} -m pytest tests/regression/resources/test_{{resource}}.py -m "regression and readonly" -v -s

test-resource-writeops resource:
    #!/usr/bin/env bash
    if [ ! -f "tests/regression/resources/test_{{resource}}.py" ]; then
        echo "❌ Error: Resource '{{resource}}' not found"
        exit 1
    fi
    echo "🚨 WARNING: WRITE OPERATIONS TEST FOR {{resource}} 🚨"
    echo "This will CREATE, UPDATE, and DELETE {{resource}} records!"
    echo "Press Ctrl+C now to cancel, or Enter to continue..."
    read confirm
    {{python}} -m pytest tests/regression/resources/test_{{resource}}.py -m "regression and writeops" -v -s

# Build and distribution
clean: api-clean
    @echo "Cleaning build artifacts..."
    rm -rf build/ dist/ *.egg-info/ .pytest_cache/ htmlcov/ .coverage
    find . -type d -name __pycache__ -exec rm -rf {} +
    find . -type f -name "*.pyc" -delete

build: clean
    @echo "Building package..."
    {{python}} -m build

publish-test: build
    @echo "Publishing to TestPyPI..."
    {{python}} -m twine upload --repository testpypi dist/*

publish: build
    @echo "Publishing to PyPI..."
    {{python}} -m twine upload dist/*

# Documentation (User-facing website)
docs-build:
    @echo "Installing documentation dependencies..."
    {{pip}} install -r docs/requirements.txt
    @echo "Building MkDocs documentation..."
    mkdocs build
    @echo "✅ Documentation built in ./site/"
    @echo "   Open ./site/index.html in your browser to view"

docs-serve:
    @echo "Installing documentation dependencies..."
    {{pip}} install -r docs/requirements.txt
    @echo "Starting MkDocs development server..."
    @echo "📖 Documentation will be available at: http://127.0.0.1:8000"
    @echo "   Press Ctrl+C to stop the server"
    @echo "   Changes to markdown files will automatically reload"
    mkdocs serve

docs-check:
    @echo "Installing documentation dependencies..."
    {{pip}} install -r docs/requirements.txt
    @echo "Checking MkDocs build with strict mode..."
    mkdocs build --strict
    @echo "✅ Documentation build passed strict checks"

# API Schemas (Machine-readable, for tooling)
api-schemas:
    @echo "Generating machine-readable schemas..."
    {{python}} tools/generate_schemas.py
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

api-validate:
    @echo "Validating API specifications..."
    {{python}} tools/validate_openapi.py

api-serve: api-schemas
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

api-clean:
    @echo "Cleaning generated API schemas..."
    rm -f docs/api/schemas.json docs/api/resource_metadata.json docs/api/types.json docs/api/capabilities.json
    @echo "✅ API schemas cleaned"

# Examples
example:
    @echo "Running basic usage example..."
    {{python}} examples/basic_usage.py

# Comprehensive checks
check-all: format lint type-check test
    @echo "✅ All checks completed successfully!"

# Package info
info:
    @echo "Package Information:"
    @echo "==================="
    {{python}} -c "import sys; sys.path.insert(0, 'src'); import neon_crm; print(f'Version: {neon_crm.__version__}')"
    @echo "Python: {{python}}"
    @echo "Pip: {{pip}}"

# Environment checks
check-env:
    @echo "Environment Check:"
    @echo "=================="
    @echo "Python: {{python}}"
    @echo "Pip: {{pip}}"
    @echo "Virtual environment: {{ if path_exists("venv/bin/python") == "true" { "✓ Using venv" } else { "⚠️  Not using venv" } }}"
    @if [ -f "pyproject.toml" ]; then echo "✓ pyproject.toml found"; fi
    @if [ -d "src/neon_crm" ]; then echo "✓ Source directory found"; fi
    @if [ -d "tests" ]; then echo "✓ Tests directory found"; fi

# Notebook utilities
clean-notebooks:
    @echo "🧹 Clearing output from all Jupyter notebooks..."
    @if command -v nbstripout >/dev/null 2>&1; then \
        echo "Using nbstripout..."; \
        find . -name "*.ipynb" -not -path "./venv/*" -not -path "./.git/*" -exec nbstripout {} \; && \
        echo "✅ All notebooks cleared"; \
    elif command -v jupyter >/dev/null 2>&1; then \
        echo "Using jupyter nbconvert..."; \
        find . -name "*.ipynb" -not -path "./venv/*" -not -path "./.git/*" -exec jupyter nbconvert --clear-output --inplace {} \; && \
        echo "✅ All notebooks cleared"; \
    else \
        echo "Using Python fallback..."; \
        find . -name "*.ipynb" -not -path "./venv/*" -not -path "./.git/*" | while read notebook; do \
            {{python}} -c "import json; nb=json.load(open('$$notebook')); [c.pop('outputs',None) or c.pop('execution_count',None) for c in nb.get('cells',[])]; json.dump(nb,open('$$notebook','w'),indent=1)"; \
        done; \
        echo "✅ All notebooks processed"; \
    fi

# Quick commands
quick-test:
    {{python}} -m pytest tests/ -x

quick-check:
    {{python}} -m ruff check src/
    {{python}} -m pytest tests/ -x

# Release workflow
release-check: clean format lint type-check test build
    @echo "✅ Release checks completed successfully!"
    @echo "Package is ready for release."
    @echo "Run 'just publish-test' to publish to TestPyPI first."
