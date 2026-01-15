# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build and Development Commands

This is a Python monorepo managed with [uv](https://docs.astral.sh/uv/) and [poethepoet](https://poethepoet.naez.io/).

```bash
# Install dependencies
uv sync --all-packages
npm install  # Required for Redocly and Spectral backends

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

## Architecture

### Package Structure

The monorepo contains these namespace packages under `jentic.apitools.openapi.*`:

| Package | Purpose |
|---------|---------|
| `jentic-openapi-common` | Shared utilities: path security, subprocess handling, URI parsing, version detection |
| `jentic-openapi-datamodels` | OpenAPI data models and structures |
| `jentic-openapi-parser` | Document parsing with pluggable backends |
| `jentic-openapi-traverse` | Document traversal utilities |
| `jentic-openapi-transformer` | Document transformation/bundling core |
| `jentic-openapi-transformer-redocly` | Redocly bundler backend |
| `jentic-openapi-validator` | Document validation core |
| `jentic-openapi-validator-spectral` | Spectral validation backend |
| `jentic-openapi-validator-redocly` | Redocly validation backend |
| `jentic-openapi-validator-speclynx` | SpecLynx ApiDOM validation backend |

### Plugin-Based Backend System

Core packages (parser, validator, transformer) use Python entry points for backend discovery:

**Entry point groups:**
- `jentic.apitools.openapi.parser.backends`
- `jentic.apitools.openapi.validator.backends`
- `jentic.apitools.openapi.transformer.bundler.backends`

**Pattern:**
1. Base classes define the interface (e.g., `BaseValidatorBackend` in `backends/base.py`)
2. Backends implement the interface and declare `accepts()` for supported input formats: `"uri"`, `"text"`, `"dict"`
3. Backends register via entry points in `pyproject.toml`
4. Core classes discover backends at runtime via `importlib.metadata.entry_points()`

**Example - Validator backend registration (`pyproject.toml`):**
```toml
[project.entry-points."jentic.apitools.openapi.validator.backends"]
spectral = "jentic.apitools.openapi.validator.backends.spectral:SpectralValidatorBackend"
```

**Example - Using backends:**
```python
from jentic.apitools.openapi.validator.core import OpenAPIValidator

# Use default backend
validator = OpenAPIValidator()

# Use specific backend(s)
validator = OpenAPIValidator(backends=["spectral", "redocly"])

# List available backends
OpenAPIValidator.list_backends()
```

### Key Conventions

- All packages use [PEP 420](https://peps.python.org/pep-0420/) implicit namespace packages (`jentic.apitools.openapi.*`) - no `__init__.py` files in namespace directories
- Build system uses `uv_build` with `namespace = true`
- Source code lives in `packages/<name>/src/jentic/apitools/openapi/<module>/`
- Tests live in `packages/<name>/tests/`
- Commits follow [Conventional Commits](https://www.conventionalcommits.org/) for automated versioning

### Dependencies Between Packages

```
common ← datamodels ← parser ← validator ← validator-spectral
                  ↑         ↘            ↖ validator-redocly
                  │                      ↖ validator-speclynx
                  └─ traverse ← transformer ← transformer-redocly
```

## Common Utilities (`jentic-openapi-common`)

**Path Security** - Defense against path traversal attacks:
```python
from jentic.apitools.openapi.common.path_security import validate_path
safe_path = validate_path(user_input, allowed_base="/workspace", allowed_extensions=('.yaml', '.json'))
# Raises: PathTraversalError, InvalidExtensionError, SymlinkSecurityError
```

**URI Utilities** - Detection and resolution:
```python
from jentic.apitools.openapi.common.uri import is_uri_like, is_http_https_url, resolve_to_absolute, file_uri_to_path
```

**Subprocess Execution** - Standardized external tool calls:
```python
from jentic.apitools.openapi.common.subproc import run_subprocess
result = run_subprocess(["spectral", "lint", "spec.yaml"], fail_on_error=True, timeout=30.0)
```

**Version Detection** - OpenAPI/Swagger version checks:
```python
from jentic.apitools.openapi.common.version_detection import get_version, is_openapi_30, is_openapi_31
```

## Parser Backends

| Backend | Return Type | Use Case |
|---------|-------------|----------|
| `pyyaml` (default) | `dict` | Simple parsing |
| `ruamel-safe` | `CommentedMap` | Better YAML 1.2 support |
| `ruamel-roundtrip` | `CommentedMap` | Preserves comments/formatting |
| `ruamel-ast` | `MappingNode` | Full YAML AST with source positions |
| `datamodel-low` | `OpenAPI30`/`OpenAPI31` | Typed datamodels with source tracking |

```python
from jentic.apitools.openapi.parser.core import OpenAPIParser

parser = OpenAPIParser("ruamel-roundtrip")
doc = parser.parse("spec.yaml", return_type=CommentedMap)
```

## Validator System

**ValidationResult** uses LSP diagnostics format:
```python
from jentic.apitools.openapi.validator.core import OpenAPIValidator

validator = OpenAPIValidator(backends=["spectral", "redocly"])
result = validator.validate("spec.yaml", parallel=True)  # Run backends in parallel

if not result.valid:
    for diagnostic in result.diagnostics:
        print(f"{diagnostic.source}: {diagnostic.message}")
        print(f"  Path: {diagnostic.data['path']}")  # JSON path to issue
```

| Backend | Type | Accepts | Notes |
|---------|------|---------|-------|
| `default` | Pure Python | uri, dict | Built-in rule system |
| `openapi-spec` | Python lib | dict | `openapi_spec_validator` wrapper |
| `spectral` | External CLI | uri, dict | Requires Node.js |
| `redocly` | External CLI | uri, dict | Requires Node.js |
| `speclynx` | External CLI | uri, dict | Requires Node.js, uses SpecLynx ApiDOM |

## Bundler/Transformer

```python
from jentic.apitools.openapi.transformer.bundler.core import OpenAPIBundler

bundler = OpenAPIBundler("redocly")  # Full $ref resolution
result = bundler.bundle("spec.yaml", return_type=dict)
```

## Datamodels (`jentic-openapi-datamodels`)

Low-level models with **source tracking** - every field wraps YAML node locations:
- `FieldSource[T]` - OpenAPI fields with key+value nodes
- `KeySource[T]` - Dictionary keys (extension names, schema names)
- `ValueSource[T]` - Dictionary values and array items

```python
from jentic.apitools.openapi.parser.core import OpenAPIParser
from jentic.apitools.openapi.datamodels.low.v31 import build

parser = OpenAPIParser("ruamel-ast")
doc = build(parser.parse("spec.yaml"))
print(doc.info.value.title.key_node.start_mark.line)  # Source line number
```

## Traversal (`jentic-openapi-traverse`)

**Datamodel traversal** with visitor pattern:
```python
from jentic.apitools.openapi.traverse.datamodels.low import traverse, BREAK

class OperationCollector:
    def __init__(self):
        self.operations = []

    def visit_Operation(self, path):
        self.operations.append(path.format_path("jsonpointer"))  # /paths/~1users/get
        # Return None=continue, False=skip children, BREAK=stop traversal

collector = OperationCollector()
traverse(doc, collector)
```

**JSON traversal** for generic dict/list structures:
```python
from jentic.apitools.openapi.traverse.json import traverse
for node in traverse(openapi_dict):
    print(f"{node.format_path()}: {node.value}")
