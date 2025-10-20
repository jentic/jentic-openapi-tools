# jentic-openapi-validator-spectral

A [Spectral](https://github.com/stoplightio/spectral) validator backend for the Jentic OpenAPI Tools ecosystem. This package provides OpenAPI document validation using Stoplight's Spectral CLI with comprehensive error reporting and flexible configuration options.

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
from jentic.apitools.openapi.validator.backends.spectral import SpectralValidatorBackend

# Create validator with defaults
validator = SpectralValidatorBackend()

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
validator = SpectralValidatorBackend(spectral_path="/usr/local/bin/spectral")

# Use specific version via npx
validator = SpectralValidatorBackend(spectral_path="npx --yes @stoplight/spectral-cli@^6.15.0")
```

### Custom Rulesets

```python
# Use custom ruleset file
validator = SpectralValidatorBackend(ruleset_path="/path/to/custom-rules.yaml")

# The validator automatically falls back to bundled rulesets if no custom path is provided
```

### Timeout Configuration

```python
# Short timeout for CI/CD (10 seconds)
validator = SpectralValidatorBackend(timeout=10.0)

# Extended timeout for large documents (2 minutes)
validator = SpectralValidatorBackend(timeout=120.0)

# Combined configuration (45 seconds)
validator = SpectralValidatorBackend(
    spectral_path="/usr/local/bin/spectral",
    ruleset_path="/path/to/strict-rules.yaml",
    timeout=45.0
)
```

### Path Security

Use `allowed_base_dir` to restrict file access when processing untrusted input or running as a web service:

```python
from jentic.apitools.openapi.common.path_security import (
    PathTraversalError,
    InvalidExtensionError,
)

# Restrict file access to /var/app/documents directory
validator = SpectralValidatorBackend(
    allowed_base_dir="/var/app/documents"
)

# Valid paths within allowed directory work normally
result = validator.validate("/var/app/documents/specs/openapi.yaml")

# Path traversal attempts are blocked
try:
    result = validator.validate("/var/app/documents/../../etc/passwd")
except PathTraversalError as e:
    print(f"Security violation: {e}")

# Invalid file extensions are rejected
try:
    result = validator.validate("/var/app/documents/malicious.exe")
except InvalidExtensionError as e:
    print(f"Invalid file type: {e}")

# HTTP(S) URLs bypass path validation (as expected)
result = validator.validate("https://example.com/openapi.yaml")

# Combined security configuration for web services
validator = SpectralValidatorBackend(
    allowed_base_dir="/var/app/uploads",
    ruleset_path="/var/app/config/custom-rules.yaml",  # Also validated
    timeout=600.0
)
```

**Security Benefits:**
- Prevents path traversal attacks (`../../etc/passwd`)
- Restricts access to allowed directories only (when `allowed_base_dir` is set)
- Validates file extensions (`.yaml`, `.yml`, `.json`) - **always enforced**, even when `allowed_base_dir=None`
- Checks symlinks don't escape boundaries (when `allowed_base_dir` is set)
- Validates both document and ruleset paths

**Note:** File extension validation (`.yaml`, `.yml`, `.json`) is always performed for filesystem paths, regardless of whether `allowed_base_dir` is set. When `allowed_base_dir=None`, only the base directory containment check is skipped.

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
validator = SpectralValidatorBackend(ruleset_path="./custom-rules.yaml")
result = validator.validate("file:///path/to/openapi.yaml")
```

## Testing

### Integration Tests

The integration tests require Spectral CLI to be available. They will be automatically skipped if Spectral is not installed.

**Run the integration test:**

```bash
uv run --package jentic-openapi-validator-spectral pytest packages/jentic-openapi-validator-spectral -v
```

## API Reference

### SpectralValidator

```python
class SpectralValidatorBackend(BaseValidatorBackend):
    def __init__(
        self,
        spectral_path: str = "npx --yes @stoplight/spectral-cli@^6.15.0",
        ruleset_path: str | None = None,
        timeout: float = 600.0,
        allowed_base_dir: str | Path | None = None,
    ) -> None
```

**Parameters:**
- `spectral_path`: Path to Spectral CLI executable
- `ruleset_path`: Path to a custom ruleset file (optional)
- `timeout`: Maximum execution time in seconds
- `allowed_base_dir`: Optional base directory for path security validation. When set, all document and ruleset paths are validated to be within this directory, providing defense against path traversal attacks. When `None` (default), only file extension validation is performed (no base directory containment check). Recommended for web services or untrusted input (optional)

**Methods:**

- `accepts() -> list[Literal["uri", "dict"]]`: Returns supported document format identifiers
- `validate(document: str | dict) -> ValidationResult`: Validates an OpenAPI document

**Exceptions:**
- `FileNotFoundError`: Custom ruleset file doesn't exist
- `RuntimeError`: Spectral execution fails
- `SubprocessExecutionError`: Spectral times out or fails to start
- `TypeError`: Unsupported document type
- `PathTraversalError`: Document or ruleset path attempts to escape allowed_base_dir (only when `allowed_base_dir` is set)
- `InvalidExtensionError`: Document or ruleset path has disallowed file extension (always checked for filesystem paths)