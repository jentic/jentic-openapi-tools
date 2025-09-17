# Jentic OpenAPI Tools


## Development

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
uv python pin 3.12
(uv run pre-commit install)
uv sync --all-packages
```

### run per-package tests (from root)

```bash
uv run pytest jentic-openapi-common/tests -q
uv run --package jentic-openapi-parser       pytest packages/jentic-openapi-parser/tests -q
uv run --package jentic-openapi-transformer  pytest packages/jentic-openapi-transformer/tests -q
uv run --package jentic-openapi-validator    pytest packages/jentic-openapi-validator/tests -q
uv run --package jentic-openapi-validator-spectral    pytest packages/jentic-openapi-validator-spectral/tests -q
uv run --package jentic-openapi-bundler-redocly    pytest packages/jentic-openapi-bundler-redocly/tests -q
```

### Run linting
uv run ruff check .
uv run ruff format --check .
uv run pyright

### Build packages

```bash
uv build --package jentic-openapi-parser
uv build --package jentic-openapi-transformer
uv build --package jentic-openapi-validator
uv build --package jentic-openapi-validator-spectral
uv build --package jentic-openapi-bundler-redocly
```

### Conventional Commits

This project uses [Conventional Commits](https://www.conventionalcommits.org/) for automated versioning and changelog generation.


## Clients Development

### Usage in a client project

#### Option 1: Git Dependency

You can install the packages directly from your Git repository. In your client project's , add dependencies like this: 

```
[project]
dependencies = [
    "jentic-openapi-parser @ git+https://github.com/your-username/jentic-openapi-tools.git#subdirectory=packages/jentic-openapi-parser",
    "jentic-openapi-transformer @ git+https://github.com/your-username/jentic-openapi-tools.git#subdirectory=packages/jentic-openapi-transformer",
    "jentic-openapi-validator @ git+https://github.com/your-username/jentic-openapi-tools.git#subdirectory=packages/jentic-openapi-validator"
]
```

#### Option 2: Local Path Dependencies

If you're developing locally and want to use the packages from a local path, you can use:

```
[project]
dependencies = [
    "jentic-openapi-parser @ file:///path/to/jentic-openapi-tools/packages/jentic-openapi-parser",
    "jentic-openapi-transformer @ file:///path/to/jentic-openapi-tools/packages/jentic-openapi-transformer",
    "jentic-openapi-validator @ file:///path/to/jentic-openapi-tools/packages/jentic-openapi-validator"
]
```

#### Option 3: Editable Install for Development

For active development where you want changes to be immediately reflected:

```
pip install -e /path/to/jentic-openapi-tools/packages/jentic-openapi-parser
pip install -e /path/to/jentic-openapi-tools/packages/jentic-openapi-transformer
pip install -e /path/to/jentic-openapi-tools/packages/jentic-openapi-validator
```

```
pip unsinstall -e  jentic-openapi-parser

```
