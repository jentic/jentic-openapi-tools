# Jentic OpenAPI Tools


## Development

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
uv sync --all-packages
```

Optional setup:
```bash
uv python pin 3.11 # or your preferred version
uv run pre-commit install # install pre-commit hooks
git config commit.template .gitmessage # commit message template
```


### run per-package tests (from root)

```bash
uv run --package jentic-openapi-common       pytest packages/jentic-openapi-common/tests -q
uv run --package jentic-openapi-parser       pytest packages/jentic-openapi-parser/tests -q
uv run --package jentic-openapi-transformer  pytest packages/jentic-openapi-transformer/tests -q
uv run --package jentic-openapi-validator    pytest packages/jentic-openapi-validator/tests -q
uv run --package jentic-openapi-validator-spectral    pytest packages/jentic-openapi-validator-spectral/tests -q
uv run --package jentic-openapi-bundler-redocly    pytest packages/jentic-openapi-bundler-redocly/tests -q
```

### Run linting

```bash
uv run poe lint
uv run poe lint:fix
```

### Run type checking

```bash
uv run poe typecheck
```

### Build packages

```bash
uv build --package jentic-openapi-common
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

```toml
[project]
dependencies = [
    "jentic-openapi-common @ git+https://github.com/jentic/jentic-openapi-tools.git#subdirectory=packages/jentic-openapi-common",
    "jentic-openapi-parser @ git+https://github.com/jentic/jentic-openapi-tools.git#subdirectory=packages/jentic-openapi-parser",
    "jentic-openapi-transformer @ git+https://github.com/jentic/jentic-openapi-tools.git#subdirectory=packages/jentic-openapi-transformer",
    "jentic-openapi-validator @ git+https://github.com/jentic/jentic-openapi-tools.git#subdirectory=packages/jentic-openapi-validator"
]
```

#### Option 2: Local Path Dependencies

If you're developing locally and want to use the packages from a local path, you can use:

```toml
[project]
dependencies = [
    "jentic-openapi-common @ file:///path/to/jentic-openapi-tools/packages/jentic-openapi-common",
    "jentic-openapi-parser @ file:///path/to/jentic-openapi-tools/packages/jentic-openapi-parser",
    "jentic-openapi-transformer @ file:///path/to/jentic-openapi-tools/packages/jentic-openapi-transformer",
    "jentic-openapi-validator @ file:///path/to/jentic-openapi-tools/packages/jentic-openapi-validator"
]
```

#### Option 3: Editable Installation for Development

For active development where you want changes to be immediately reflected:

```bash
pip install -e /path/to/jentic-openapi-tools/packages/jentic-openapi-common
pip install -e /path/to/jentic-openapi-tools/packages/jentic-openapi-parser
pip install -e /path/to/jentic-openapi-tools/packages/jentic-openapi-transformer
pip install -e /path/to/jentic-openapi-tools/packages/jentic-openapi-validator
```

Uninstalling Editable Packages:
```bash
pip unsinstall -e  jentic-openapi-parser
```
