# Installation

## Requirements

- Python 3.8 or higher
- Neon CRM account with API access

## Install from PyPI

```bash
pip install neon-crm
```

## Install from Source

```bash
git clone https://github.com/your-username/neon-crm-python.git
cd neon-crm-python
pip install -e ".[dev]"
```

## Verify Installation

```python
import neon_crm
print(neon_crm.__version__)
```

## Dependencies

The SDK has minimal dependencies:

- `httpx` - HTTP client with sync/async support
- `pydantic` - Data validation and type safety

## Development Installation

For development, install additional dependencies:

```bash
pip install -e ".[dev,test,docs]"
```

This includes:
- Testing frameworks (pytest, coverage)
- Code formatting (black, ruff)
- Documentation tools (mkdocs, mkdocs-material)

## Next Steps

After installation, continue with the [Quick Start](quickstart.md) guide.
