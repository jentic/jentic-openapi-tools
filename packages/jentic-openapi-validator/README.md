# jentic-openapi-validator

A Python library for validating OpenAPI documents using pluggable validator backends. This package is part of the Jentic OpenAPI Tools ecosystem and provides a flexible, extensible architecture for OpenAPI document validation.

## Features

- **Pluggable Backend Architecture**: Support for multiple validation strategies via entry points
- **Multiple Input Formats**: Validate OpenAPI documents from file URIs, JSON/YAML strings, or Python dictionaries
- **Parallel Execution**: Run multiple backends concurrently using `ProcessPoolExecutor` for improved performance
- **Aggregated Results**: Collect diagnostics from all configured backends into a single result
- **Type Safety**: Full type hints with comprehensive docstrings
- **Extensible Design**: Easy integration of third-party validator backends

## Installation

```bash
pip install jentic-openapi-validator
```

**Prerequisites:**
- Python 3.11+

**Optional Backends:**

For advanced validation with Spectral:

```bash
pip install jentic-openapi-validator-spectral
```

For validation with Redocly:

```bash
pip install jentic-openapi-validator-redocly
```

## Quick Start

### Basic Validation

```python
from jentic.apitools.openapi.validator.core import OpenAPIValidator

# Create validator with default backend
validator = OpenAPIValidator()

# Validate from file URI
result = validator.validate("file:///path/to/openapi.yaml")
print(f"Valid: {result.valid}")

# Check for validation issues
if not result.valid:
    for diagnostic in result.diagnostics:
        print(f"Error: {diagnostic.message}")
```

### Validate from String

```python
# Validate JSON/YAML string
openapi_json = '{"openapi":"3.1.0","info":{"title":"My API","version":"1.0.0"},"paths":{}}'
result = validator.validate(openapi_json)

if result:  # ValidationResult supports boolean context
    print("Validation passed!")
```

### Validate from Dictionary

```python
# Validate from dictionary
openapi_doc = {
    "openapi": "3.1.0",
    "info": {"title": "My API", "version": "1.0.0"},
    "paths": {}
}

result = validator.validate(openapi_doc)
print(f"Found {len(result)} issues")  # ValidationResult supports len()
```

## Configuration Options

### Using Multiple Backends

```python
# Use openapi-spec backend only (default)
validator = OpenAPIValidator()

# Use multiple backends (requires backends to be installed)
validator = OpenAPIValidator(backends=["openapi-spec", "spectral"])

# Results from all backends are aggregated
result = validator.validate(document)
```

### Backend Selection

```python
# Use backend by name
validator = OpenAPIValidator(backends=["openapi-spec"])

# Pass backend instance
from jentic.apitools.openapi.validator.backends.openapi_spec import OpenAPISpecValidatorBackend
backend = OpenAPISpecValidatorBackend()
validator = OpenAPIValidator(backends=[backend])

# Pass backend class
validator = OpenAPIValidator(backends=[OpenAPISpecValidatorBackend])
```

### Custom Parser

```python
from jentic.apitools.openapi.parser.core import OpenAPIParser

# Use a custom parser instance
parser = OpenAPIParser()
validator = OpenAPIValidator(parser=parser)
```

### Parallel Execution

When using multiple backends, you can run them in parallel for improved performance:

```python
# Run backends in parallel using ProcessPoolExecutor
validator = OpenAPIValidator(backends=["default", "openapi-spec", "spectral"])
result = validator.validate(document, parallel=True)

# Limit the number of worker processes
result = validator.validate(document, parallel=True, max_workers=2)
```

Parallel execution uses `ProcessPoolExecutor` for true parallelism that bypasses Python's GIL. This is particularly beneficial when using multiple backends, especially I/O-bound backends like Spectral and Redocly that spawn subprocesses.

**Notes:**
- `parallel=False` by default (opt-in)
- With a single backend, `parallel=True` has no effect (runs sequentially)
- Diagnostics from all backends are aggregated regardless of execution mode

## Working with ValidationResult

The `ValidationResult` class provides convenient methods for working with validation diagnostics:

```python
result = validator.validate(document)

# Boolean context - True if valid
if result:
    print("Valid!")

# Get diagnostic count
print(f"Found {len(result)} issues")

# Check validity
if not result.valid:
    print("Validation failed")

# Access all diagnostics
for diagnostic in result.diagnostics:
    print(f"{diagnostic.severity}: {diagnostic.message}")
```

## Testing

Run the test suite:

```bash
uv run --package jentic-openapi-validator pytest packages/jentic-openapi-validator -v
```

### Integration Tests

The package includes integration tests for backend discovery and validation. Tests requiring external backends (like Spectral) will be automatically skipped if the backend package is not installed or the required CLI is not available.

## API Reference

### OpenAPIValidator

```python
class OpenAPIValidator:
    def __init__(
        self,
        backends: Sequence[str | BaseValidatorBackend | Type[BaseValidatorBackend]] | None = None,
        parser: OpenAPIParser | None = None,
    ) -> None
```

**Parameters:**
- `backends`: Sequence of validator backends to use. Each item can be:
  - `str`: Name of a backend registered via entry points (e.g., "default", "openapi-spec", "redocly", "spectral")
  - `BaseValidatorBackend`: Instance of a validator backend
  - `Type[BaseValidatorBackend]`: Class of a validator backend (will be instantiated)
  - Defaults to `["default"]` if `None`
- `parser`: Custom OpenAPIParser instance (optional)

**Methods:**

- `validate(document: str | dict, *, base_url: str | None = None, target: str | None = None, parallel: bool = False, max_workers: int | None = None) -> ValidationResult`
  - Validates an OpenAPI document using all configured backends
  - `document`: File URI, JSON/YAML string, or dictionary
  - `base_url`: Optional base URL for resolving relative references
  - `target`: Optional target identifier for validation context
  - `parallel`: If `True` and multiple backends are configured, run validation in parallel using `ProcessPoolExecutor`. Defaults to `False`.
  - `max_workers`: Maximum number of worker processes for parallel execution. If `None`, defaults to the number of processors on the machine. Only used when `parallel=True`.
  - Returns: `ValidationResult` with aggregated diagnostics

### ValidationResult

```python
@dataclass
class ValidationResult:
    diagnostics: list[Diagnostic]
    valid: bool  # Computed automatically
```

**Attributes:**
- `diagnostics`: List of all diagnostics from validation
- `valid`: `True` if no diagnostics were found, `False` otherwise

**Methods:**
- `__bool__()`: Returns `valid` for use in boolean context
- `__len__()`: Returns number of diagnostics
- `__repr__()`: Returns string representation

## Available Backends

### default
Basic validation backend that checks for required OpenAPI fields and structure. Suitable for basic document validation.

### openapi-spec
Validation backend using the `openapi-spec-validator` library for JSON Schema-based validation of OpenAPI documents. CPU-bound validation.

### redocly (Optional)
Validation backend using Redocly CLI for comprehensive OpenAPI linting and validation. I/O-bound (spawns Node.js subprocess).

Install: `pip install jentic-openapi-validator-redocly`

### spectral (Optional)
Advanced validation backend using Spectral CLI with comprehensive rule checking. I/O-bound (spawns Node.js subprocess).

Install: `pip install jentic-openapi-validator-spectral`
