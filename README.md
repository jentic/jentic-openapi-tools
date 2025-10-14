# Jentic OpenAPI Tools


## Development

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.3/install.sh | bash
uv sync --all-packages
nvm install && npm install
```

Optional setup:
```bash
uv python pin 3.11 # or your preferred version
uv run pre-commit install # install pre-commit hooks
git config commit.template .gitmessage # commit message template
```


### run per-package tests (from root)

```bash
uv run --package jentic-openapi-common                 pytest packages/jentic-openapi-common/tests -q
uv run --package jentic-openapi-datamodels             pytest packages/jentic-openapi-datamodels/tests -q
uv run --package jentic-openapi-parser                 pytest packages/jentic-openapi-parser/tests -q
uv run --package jentic-openapi-traverse               pytest packages/jentic-openapi-traverse/tests -q
uv run --package jentic-openapi-transformer            pytest packages/jentic-openapi-transformer/tests -q
uv run --package jentic-openapi-transformer-redocly    pytest packages/jentic-openapi-transformer-redocly/tests -q
uv run --package jentic-openapi-validator              pytest packages/jentic-openapi-validator/tests -q
uv run --package jentic-openapi-validator-redocly      pytest packages/jentic-openapi-validator-redocly/tests -q
uv run --package jentic-openapi-validator-spectral     pytest packages/jentic-openapi-validator-spectral/tests -q
# Run single test suite
uv run --package jentic-openapi-transformer-redocly pytest -s packages/jentic-openapi-transformer-redocly/tests/test_redocly_bundle.py::TestRedoclyBundlerIntegration
# Run by pattern
uv run pytest packages/**/tests -s -v -k test_redocly_bundle
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
uv build --package jentic-openapi-datamodels
uv build --package jentic-openapi-parser
uv build --package jentic-openapi-traverse
uv build --package jentic-openapi-transformer
uv build --package jentic-openapi-transformer-redocly
uv build --package jentic-openapi-validator
uv build --package jentic-openapi-validator-redocly
uv build --package jentic-openapi-validator-spectral
```

### Conventional Commits

This project uses [Conventional Commits](https://www.conventionalcommits.org/) for automated versioning and changelog generation.


## Clients Development

### Usage in a client project

#### Option 1: Git Dependency

You can install the packages directly from your Git repository. In your client project's `pyproject.toml`, add dependencies like this:

```toml
[project]
dependencies = [
    "jentic-openapi-common @ git+https://github.com/jentic/jentic-openapi-tools.git#subdirectory=packages/jentic-openapi-common",
    "jentic-openapi-datamodels @ git+https://github.com/jentic/jentic-openapi-tools.git#subdirectory=packages/jentic-openapi-datamodels",
    "jentic-openapi-parser @ git+https://github.com/jentic/jentic-openapi-tools.git#subdirectory=packages/jentic-openapi-parser",
    "jentic-openapi-traverse @ git+https://github.com/jentic/jentic-openapi-tools.git#subdirectory=packages/jentic-openapi-traverse",
    "jentic-openapi-transformer @ git+https://github.com/jentic/jentic-openapi-tools.git#subdirectory=packages/jentic-openapi-transformer",
    "jentic-openapi-transformer-redocly @ git+https://github.com/jentic/jentic-openapi-tools.git#subdirectory=packages/jentic-openapi-transformer-redocly",
    "jentic-openapi-validator @ git+https://github.com/jentic/jentic-openapi-tools.git#subdirectory=packages/jentic-openapi-validator",
    "jentic-openapi-validator-redocly @ git+https://github.com/jentic/jentic-openapi-tools.git#subdirectory=packages/jentic-openapi-validator-redocly",
    "jentic-openapi-validator-spectral @ git+https://github.com/jentic/jentic-openapi-tools.git#subdirectory=packages/jentic-openapi-validator-spectral",
]
```

#### Option 2: Local Path Dependencies

If you're developing locally and want to use the packages from a local path, you can use:

```toml
[project]
dependencies = [
    "jentic-openapi-common @ file:///path/to/jentic-openapi-tools/packages/jentic-openapi-common",
    "jentic-openapi-datamodels @ file:///path/to/jentic-openapi-tools/packages/jentic-openapi-datamodels",
    "jentic-openapi-parser @ file:///path/to/jentic-openapi-tools/packages/jentic-openapi-parser",
    "jentic-openapi-traverse @ file:///path/to/jentic-openapi-tools/packages/jentic-openapi-traverse",
    "jentic-openapi-transformer @ file:///path/to/jentic-openapi-tools/packages/jentic-openapi-transformer",
    "jentic-openapi-transformer-redocly @ file:///path/to/jentic-openapi-tools/packages/jentic-openapi-transformer-redocly",
    "jentic-openapi-validator @ file:///path/to/jentic-openapi-tools/packages/jentic-openapi-validator",
    "jentic-openapi-validator-redocly @ file:///path/to/jentic-openapi-tools/packages/jentic-openapi-validator-redocly",
    "jentic-openapi-validator-spectral @ file:///path/to/jentic-openapi-tools/packages/jentic-openapi-validator-spectral",
]
```

#### Option 3: Editable Installation for Development

For active development where you want changes to be immediately reflected:

```bash
pip install -e /path/to/jentic-openapi-tools/packages/jentic-openapi-common
pip install -e /path/to/jentic-openapi-tools/packages/jentic-openapi-datamodels
pip install -e /path/to/jentic-openapi-tools/packages/jentic-openapi-parser
pip install -e /path/to/jentic-openapi-tools/packages/jentic-openapi-traverse
pip install -e /path/to/jentic-openapi-tools/packages/jentic-openapi-transformer
pip install -e /path/to/jentic-openapi-tools/packages/jentic-openapi-transformer-redocly
pip install -e /path/to/jentic-openapi-tools/packages/jentic-openapi-validator
pip install -e /path/to/jentic-openapi-tools/packages/jentic-openapi-validator-redocly
pip install -e /path/to/jentic-openapi-tools/packages/jentic-openapi-validator-spectral
```

Uninstalling Editable Packages:
```bash
pip uninstall -e jentic-openapi-parser
```
