# jentic-openapi-validator-spectral

A [Spectral](https://github.com/stoplightio/spectral) validator strategy for the Jentic OpenAPI Tools ecosystem. This package provides OpenAPI document validation using Stoplight's Spectral CLI with comprehensive error reporting and flexible configuration options.

## Features

- **Multiple input formats**: Validate OpenAPI documents from file URIs or Python dictionaries
- **Custom rulesets**: Use built-in rules or provide your own Spectral ruleset
- **Configurable timeouts**: Control execution time limits for different use cases
- **Rich diagnostics**: Detailed validation results with line/column information
- **Type-safe API**: Full typing support with Literal types and comprehensive docstrings

## Installation

```bash
pip install jentic-openapi-validator-spectral
```

**Prerequisites:**
- Node.js and npm (for Spectral CLI)
- Python 3.11+

The Spectral CLI will be automatically downloaded via npx on first use, or you can install it globally:

```bash
npm install -g @stoplight/spectral-cli
```

## Quick Start

### Basic Usage

```python
from jentic.apitools.openapi.validator.spectral import SpectralValidator

# Create validator with defaults
validator = SpectralValidator()

# Validate from file URI
result = validator.validate("file:///path/to/openapi.yaml")
print(f"Valid: {result.valid}")

# Check for validation issues
if not result.valid:
    for diagnostic in result.diagnostics:
        print(f"Error: {diagnostic.message}")
```

### Validate Dictionary Documents

```python
# Validate from dictionary
openapi_doc = {
    "openapi": "3.0.0",
    "info": {"title": "My API", "version": "1.0.0"},
    "paths": {}
}

result = validator.validate(openapi_doc)
print(f"Document is valid: {result.valid}")
```

## Configuration Options

### Custom Spectral CLI Path

```python
# Use local Spectral installation
validator = SpectralValidator(spectral_path="/usr/local/bin/spectral")

# Use specific version via npx
validator = SpectralValidator(spectral_path="npx @stoplight/spectral-cli@^6.15.0")
```

### Custom Rulesets

```python
# Use custom ruleset file
validator = SpectralValidator(ruleset_path="/path/to/custom-rules.yaml")

# The validator automatically falls back to bundled rulesets if no custom path is provided
```

### Timeout Configuration

```python
# Short timeout for CI/CD (10 seconds)
validator = SpectralValidator(timeout=10.0)

# Extended timeout for large documents (2 minutes)
validator = SpectralValidator(timeout=120.0)

# Combined configuration (45 seconds)
validator = SpectralValidator(
    spectral_path="/usr/local/bin/spectral",
    ruleset_path="/path/to/strict-rules.yaml",
    timeout=45.0
)
```

## Advanced Usage

### Error Handling

```python
from jentic.apitools.openapi.common.subproc import SubprocessExecutionError

try:
    result = validator.validate("file:///path/to/openapi.yaml")

    if result.valid:
        print("✅ Document is valid")
    else:
        print("❌ Validation failed:")
        for diagnostic in result.diagnostics:
            severity = diagnostic.severity.name
            line = diagnostic.range.start.line + 1
            print(f"  {severity}: {diagnostic.message} (line {line})")

except FileNotFoundError as e:
    print(f"Ruleset file not found: {e}")
except SubprocessExecutionError as e:
    print(f"Spectral execution failed: {e}")
except TypeError as e:
    print(f"Invalid document type: {e}")
```

### Supported Document Formats

```python
# Check what formats the validator supports
formats = validator.accepts()
print(formats)  # ['uri', 'dict']

# Validate different input types
if "uri" in validator.accepts():
    result = validator.validate("file:///path/to/spec.yaml")

if "dict" in validator.accepts():
    result = validator.validate({"openapi": "3.0.0", ...})
```

## Custom Rulesets

Create a custom Spectral ruleset file:

```yaml
# custom-rules.yaml
extends: ["spectral:oas"]

rules:
  info-contact: error
  info-description: error
  operation-description: error
  operation-summary: warn
  path-params: error

  # Custom rule
  no-empty-paths:
    description: "Paths object should not be empty"
    given: "$.paths"
    then:
      function: truthy
    severity: error
```

Use it with the validator:

```python
validator = SpectralValidator(ruleset_path="./custom-rules.yaml")
result = validator.validate("file:///path/to/openapi.yaml")
```

## Testing

### Integration Tests

The integration tests require Spectral CLI to be available. They will be automatically skipped if Spectral is not installed.

**Run the integration test:**

```bash
uv run --package jentic-openapi-validator pytest packages/jentic-openapi-validator -v
```

## API Reference

### SpectralValidator

```python
class SpectralValidator(BaseValidatorStrategy):
    def __init__(
        self,
        spectral_path: str = "npx @stoplight/spectral-cli@^6.15.0",
        ruleset_path: str | None = None,
        timeout: float = 30.0,
    ) -> None
```

**Parameters:**
- `spectral_path`: Path to Spectral CLI executable
- `ruleset_path`: Path to a custom ruleset file (optional)
- `timeout`: Maximum execution time in seconds

**Methods:**

- `accepts() -> list[Literal["uri", "dict"]]`: Returns supported document format identifiers
- `validate(document: str | dict) -> ValidationResult`: Validates an OpenAPI document

**Exceptions:**
- `FileNotFoundError`: Custom ruleset file doesn't exist
- `RuntimeError`: Spectral execution fails
- `SubprocessExecutionError`: Spectral times out or fails to start