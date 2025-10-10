# jentic-openapi-validator

A Python library for validating OpenAPI documents using pluggable validator backends. This package is part of the Jentic OpenAPI Tools ecosystem and provides a flexible, extensible architecture for OpenAPI document validation.

## Features

- **Pluggable Backend Architecture**: Support for multiple validation strategies via entry points
- **Multiple Input Formats**: Validate OpenAPI documents from file URIs, JSON/YAML strings, or Python dictionaries
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
        backends: list[str | BaseValidatorBackend | Type[BaseValidatorBackend]] | None = None,
        parser: OpenAPIParser | None = None,
    ) -> None
```

**Parameters:**
- `backends`: List of validator backends to use. Each item can be:
  - `str`: Name of a backend registered via entry points (e.g., "openapi-spec", "spectral")
  - `BaseValidatorBackend`: Instance of a validator backend
  - `Type[BaseValidatorBackend]`: Class of a validator backend (will be instantiated)
  - Defaults to `["openapi-spec"]` if `None`
- `parser`: Custom OpenAPIParser instance (optional)

**Methods:**

- `validate(document: str | dict) -> ValidationResult`
  - Validates an OpenAPI document using all configured backends
  - `document`: File URI, JSON/YAML string, or dictionary
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

### spectral (Optional)
Advanced validation backend using Spectral CLI with comprehensive rule checking.

Install: `pip install jentic-openapi-validator-spectral`
