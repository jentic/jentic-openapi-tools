# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build and Development Commands

This is a Python monorepo managed with [uv](https://docs.astral.sh/uv/) and [poethepoet](https://poethepoet.naez.io/).

**Prerequisites:** Python 3.11+, Node.js >=20.19.0 and npm.

```bash
# Install dependencies
uv sync --all-packages
npm install  # Required for Redocly, Spectral, and SpecLynx backends

# Run all tests
uv run poe test

# Run tests for a specific package
uv run --package jentic-openapi-validator pytest packages/jentic-openapi-validator/tests -q

# Run a single test file
uv run pytest packages/jentic-openapi-validator/tests/test_validate_default.py -v

# Run a single test by pattern
uv run pytest packages/**/tests -s -v -k test_name_pattern

# Lint and format
uv run poe lint          # Check linting
uv run poe lint:fix      # Auto-fix issues

# Type checking
uv run poe typecheck

# Build all packages
uv build --all-packages

# Build specific package
uv build --package jentic-openapi-validator
```

## Code Style

- Ruff with line-length=100, target-version=py311
- Ruff enforces import sorting (isort) with 2 blank lines after imports
- Pyright in `standard` type checking mode

## Architecture

### Package Structure

The monorepo contains these namespace packages under `jentic.apitools.openapi.*`:

| Package | Purpose |
|---------|---------|
| `jentic-openapi-common` | Shared utilities: path security, subprocess handling, URI parsing, version detection |
| `jentic-openapi-datamodels` | OpenAPI data models with source tracking (YAML node locations) |
| `jentic-openapi-parser` | Document parsing with pluggable backends |
| `jentic-openapi-traverse` | Document traversal (visitor pattern for datamodels, generic JSON traversal) |
| `jentic-openapi-transformer` | Document transformation/bundling core |
| `jentic-openapi-transformer-redocly` | Redocly bundler backend |
| `jentic-openapi-validator` | Document validation core + CLI (`jentic-openapi-tools` command) |
| `jentic-openapi-validator-spectral` | Spectral validation backend |
| `jentic-openapi-validator-redocly` | Redocly validation backend |
| `jentic-openapi-validator-speclynx` | SpecLynx ApiDOM validation backend |

### Dependencies Between Packages

```
common <- datamodels <- parser <- validator <- validator-spectral
                  ^          \            \<- validator-redocly
                  |                        \<- validator-speclynx
                  +-- traverse <- transformer <- transformer-redocly
```

### Plugin-Based Backend System

Core packages (parser, validator, transformer) use Python entry points for backend discovery:

**Entry point groups:**
- `jentic.apitools.openapi.parser.backends`
- `jentic.apitools.openapi.validator.backends`
- `jentic.apitools.openapi.transformer.bundler.backends`

**Pattern:**
1. Base classes define the interface (e.g., `BaseValidatorBackend` in `backends/base.py`)
2. Backends implement the interface and declare `accepts()` for supported input formats: `"uri"`, `"text"`, `"dict"`
3. Backends register via entry points in their package's `pyproject.toml`
4. Core classes discover backends at runtime via `importlib.metadata.entry_points()`

**Backend execution tiering** (validator-specific, used when `parallel=True`):
- `"cpu"` (default): Fast pure-Python backends. Run sequentially in main thread.
- `"io"`: Backends that release the GIL (subprocess/network). Run in `ThreadPoolExecutor`. Must be thread-safe.
- `"cpu-heavy"`: Long-running pure-Python backends. Run in `ProcessPoolExecutor` with `spawn`. Must be picklable.

All three tiers execute simultaneously when parallel mode is enabled.

### Key Conventions

- All packages use [PEP 420](https://peps.python.org/pep-0420/) implicit namespace packages (`jentic.apitools.openapi.*`) - no `__init__.py` files in namespace directories
- Build system uses `uv_build` with `namespace = true`
- Source code lives in `packages/<name>/src/jentic/apitools/openapi/<module>/`
- Tests live in `packages/<name>/tests/`
- ValidationResult uses LSP diagnostics format (via `lsprotocol`)

### Commit Conventions

Commits follow [Conventional Commits](https://www.conventionalcommits.org/) (enforced by pre-commit hook in `--strict` mode).

**Scopes** (from `.gitmessage`): `parser`, `transformer`, `validator`, `validator-spectral`, `tools` (for root package changes).

**Branch naming**: `feature/<description>` or `fix/<description>`. Include issue number after the slash if applicable (e.g., `fix/1234-fix-parsing`).

**PR merging**: Squash and merge with conventional commit format.

### Pre-commit Hooks

Configured hooks: conventional-commit validation (strict), ruff check, ruff format, uv lock sync, pyright. Install with `uv run pre-commit install`.

## Common Utilities (`jentic-openapi-common`)

- **Path Security**: `validate_path()` — defense against path traversal attacks. Raises `PathTraversalError`, `InvalidExtensionError`, `SymlinkSecurityError`.
- **URI Utilities**: `is_uri_like()`, `is_http_https_url()`, `resolve_to_absolute()`, `file_uri_to_path()`
- **Subprocess Execution**: `run_subprocess()` — standardized external tool calls with timeout support
- **Version Detection**: `get_version()`, `is_openapi_30()`, `is_openapi_31()`

## Parser Backends

| Backend | Return Type | Use Case |
|---------|-------------|----------|
| `pyyaml` (default) | `dict` | Simple parsing |
| `ruamel-safe` | `CommentedMap` | Better YAML 1.2 support |
| `ruamel-roundtrip` | `CommentedMap` | Preserves comments/formatting |
| `ruamel-ast` | `MappingNode` | Full YAML AST with source positions |
| `datamodel-low` | `OpenAPI30`/`OpenAPI31` | Typed datamodels with source tracking |

## Validator Backends

| Backend | Type | Accepts | Notes |
|---------|------|---------|-------|
| `default` | Pure Python | uri, dict | Built-in rule system |
| `openapi-spec` | Python lib | dict | `openapi_spec_validator` wrapper |
| `spectral` | External CLI | uri, dict | Requires Node.js |
| `redocly` | External CLI | uri, dict | Requires Node.js |
| `speclynx` | External CLI | uri, dict | Requires Node.js, uses SpecLynx ApiDOM |
