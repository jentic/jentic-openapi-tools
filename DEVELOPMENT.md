# Development Guide

## Overview

This is a Python monorepo managed with [uv](https://docs.astral.sh/uv/) containing the following packages:

- `jentic-openapi-tools` - Root meta-package that installs all workspace packages
- `jentic-openapi-common` - Common utilities and shared functionality
- `jentic-openapi-datamodels` - OpenAPI data models
- `jentic-openapi-parser` - OpenAPI document parsing
- `jentic-openapi-traverse` - OpenAPI document traversal utilities
- `jentic-openapi-transformer` - OpenAPI document transformation
- `jentic-openapi-transformer-redocly` - Redocly-based transformation backend
- `jentic-openapi-validator` - OpenAPI document validation
- `jentic-openapi-validator-redocly` - Redocly-based validation backend
- `jentic-openapi-validator-spectral` - Spectral-based validation backend
- `jentic-openapi-validator-speclynx` - SpecLynx ApiDOM-based validation backend

## Initial Setup

### Prerequisites

- [uv](https://docs.astral.sh/uv/) - Python package and project manager
- Node.js and npm (for JavaScript tooling dependencies like Redocly and Spectral)
- Python 3.11 or higher

### Installation

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install all packages and dependencies
uv sync --all-packages

# Install npm dependencies
npm install
```

### Optional Configuration

```bash
# Pin Python version (optional)
uv python pin 3.11  # or your preferred version

# Install pre-commit hooks (recommended)
uv run pre-commit install

# Set up commit message template (recommended)
git config commit.template .gitmessage
```

## Daily Development Workflows

### Running Tests

Run all tests across all packages:
```bash
uv run poe test
```

Run tests for a specific package:
```bash
uv run --package jentic-openapi-common pytest packages/jentic-openapi-common/tests -q
uv run --package jentic-openapi-datamodels pytest packages/jentic-openapi-datamodels/tests -q
uv run --package jentic-openapi-parser pytest packages/jentic-openapi-parser/tests -q
uv run --package jentic-openapi-traverse pytest packages/jentic-openapi-traverse/tests -q
uv run --package jentic-openapi-transformer pytest packages/jentic-openapi-transformer/tests -q
uv run --package jentic-openapi-transformer-redocly pytest packages/jentic-openapi-transformer-redocly/tests -q
uv run --package jentic-openapi-validator pytest packages/jentic-openapi-validator/tests -q
uv run --package jentic-openapi-validator-redocly pytest packages/jentic-openapi-validator-redocly/tests -q
uv run --package jentic-openapi-validator-spectral pytest packages/jentic-openapi-validator-spectral/tests -q
uv run --package jentic-openapi-validator-speclynx pytest packages/jentic-openapi-validator-speclynx/tests -q
```

Run a single test suite:
```bash
uv run --package jentic-openapi-transformer-redocly pytest -s packages/jentic-openapi-transformer-redocly/tests/test_redocly_bundle.py::TestRedoclyBundlerIntegration
```

Run tests by pattern:
```bash
uv run pytest packages/**/tests -s -v -k test_redocly_bundle
```

### Code Quality

Lint code:
```bash
uv run poe lint
uv run poe lint:fix  # auto-fix issues
```

Type checking:
```bash
uv run poe typecheck
```

### Building Packages

Build all packages:
```bash
uv build --all-packages
```

Build a specific package:
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
uv build --package jentic-openapi-validator-speclynx
```

### Commits

This project uses [Conventional Commits](https://www.conventionalcommits.org/) for automated versioning and changelog generation. Please follow this format for your commit messages.

## Using Packages in Other Projects

There are several ways to use these packages in your own projects, depending on your needs:

### Option 1: Git Dependency (Production Use)

Install packages directly from the Git repository. Add to your project's `pyproject.toml`:

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
    "jentic-openapi-validator-speclynx @ git+https://github.com/jentic/jentic-openapi-tools.git#subdirectory=packages/jentic-openapi-validator-speclynx",
]
```

### Option 2: Local Path Dependencies (Testing Unreleased Changes)

Use local file paths when testing changes before they're committed. Add to your project's `pyproject.toml`:

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
    "jentic-openapi-validator-speclynx @ file:///path/to/jentic-openapi-tools/packages/jentic-openapi-validator-speclynx",
]
```

### Option 3: Editable Installation (Active Development)

Use editable installs when actively developing these packages alongside your project. Changes are immediately reflected without reinstalling:

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
pip install -e /path/to/jentic-openapi-tools/packages/jentic-openapi-validator-speclynx
```

To uninstall an editable package:
```bash
pip uninstall jentic-openapi-parser
```
