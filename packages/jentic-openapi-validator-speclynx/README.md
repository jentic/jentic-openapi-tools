# jentic-openapi-validator-speclynx

A [SpecLynx ApiDOM](https://github.com/speclynx/apidom) validator backend for the Jentic OpenAPI Tools ecosystem.
This package provides OpenAPI document validation using SpecLynx ApiDOM with comprehensive error reporting and flexible
configuration options.

## Features

- **Multiple input formats**: Validate OpenAPI documents from file URIs or Python dictionaries
- **Custom plugins**: Use built-in plugins or provide your own validation plugins
- **Configurable timeouts**: Control execution time limits for different use cases
- **Rich diagnostics**: Detailed validation results with line/column information
- **Type-safe API**: Full typing support with Literal types and comprehensive docstrings

## Installation

```bash
pip install jentic-openapi-validator-speclynx
```

**Prerequisites:**

- Node.js and npm (for SpecLynx CLI)
- Python 3.11+

The SpecLynx dependencies will be automatically installed via npm on first use.

## Quick Start

### Basic Usage

```python
from jentic.apitools.openapi.validator.backends.speclynx import SpeclynxValidatorBackend

# Create validator with defaults
validator = SpeclynxValidatorBackend()

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

### Custom Plugins Directory

```python
# Use additional plugins directory (merged with built-in plugins)
validator = SpeclynxValidatorBackend(plugins_dir="/path/to/custom-plugins")

# The validator loads all .mjs files from both:
# 1. Built-in plugins directory (always loaded)
# 2. Custom plugins directory (merged with built-in plugins)
```

### Timeout Configuration

```python
# Short timeout for CI/CD (10 seconds)
validator = SpeclynxValidatorBackend(timeout=10.0)

# Extended timeout for large documents (2 minutes)
validator = SpeclynxValidatorBackend(timeout=120.0)

# Combined configuration (45 seconds)
validator = SpeclynxValidatorBackend(
    plugins_dir="/path/to/custom-plugins",
    timeout=45.0
)
```

### Custom SpecLynx Path

By default, the validator uses the bundled SpecLynx CLI via npx. You can override this to use a custom installation:

```python
# Use custom speclynx installation
validator = SpeclynxValidatorBackend(speclynx_path="/usr/local/bin/speclynx")

# Install additional npm packages for custom plugins that have dependencies
# The -p flag installs packages before running the CLI
validator = SpeclynxValidatorBackend(
    speclynx_path="npx --yes -p lodash -p moment jentic-openapi-validator-speclynx-0.1.0.tgz"
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
validator = SpeclynxValidatorBackend(
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
validator = SpeclynxValidatorBackend(
    allowed_base_dir="/var/app/uploads",
    plugins_dir="/var/app/config/custom-plugins",
    timeout=600.0
)
```

**Security Benefits:**

- Prevents path traversal attacks (`../../etc/passwd`)
- Restricts access to allowed directories only (when `allowed_base_dir` is set)
- Validates file extensions (`.yaml`, `.yml`, `.json`) - **always enforced**, even when `allowed_base_dir=None`
- Checks symlinks don't escape boundaries (when `allowed_base_dir` is set)

**Note:** File extension validation (`.yaml`, `.yml`, `.json`) is always performed for filesystem paths, regardless of
whether `allowed_base_dir` is set. When `allowed_base_dir=None`, only the base directory containment check is skipped.

## Advanced Usage

### Error Handling

```python
from jentic.apitools.openapi.common.subproc import SubprocessExecutionError

try:
    result = validator.validate("file:///path/to/openapi.yaml")

    if result.valid:
        print("Document is valid")
    else:
        print("Validation failed:")
        for diagnostic in result.diagnostics:
            severity = diagnostic.severity.name
            line = diagnostic.range.start.line + 1
            print(f"  {severity}: {diagnostic.message} (line {line})")

except SubprocessExecutionError as e:
    print(f"SpecLynx execution failed: {e}")
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

## Custom Plugins

Create custom validation plugins as ES modules (`.mjs` files). Plugins use the ApiDOM visitor pattern:

```javascript
// custom-plugin.mjs
import {toValue} from '@speclynx/apidom-core';
import {DiagnosticSeverity} from 'vscode-languageserver-types';

export default ({diagnostics}) => () => ({
    pre() {
    },
    visitor: {
        InfoElement(path) {
            const info = path.node;
            const version = info.get('version');

            if (version && typeof toValue(version) !== 'string') {
                diagnostics.push({
                    severity: DiagnosticSeverity.Error,
                    message: 'info.version must be a string',
                    code: 'invalid-info-version-type',
                    range: {
                        start: {line: 0, character: 0},
                        end: {line: 0, character: 0}
                    },
                    data: {path: ['info', 'version']}
                });
            }
        }
    },
    post() {
    },
});
```

Use it with the validator:

```python
validator = SpeclynxValidatorBackend(plugins_dir="./custom-plugins")
result = validator.validate("file:///path/to/openapi.yaml")
```

**Note:** Custom plugins are merged with built-in plugins. Both the built-in plugins and your custom plugins will run
during validation.

## Testing

### Integration Tests

The integration tests require Node.js to be available. They will be automatically skipped if Node.js is not installed.

**Run the integration test:**

```bash
uv run --package jentic-openapi-validator-speclynx pytest packages/jentic-openapi-validator-speclynx -v
```

## API Reference

### SpeclynxValidatorBackend

```python
class SpeclynxValidatorBackend(BaseValidatorBackend):
    def __init__(
            self,
            speclynx_path: str = "npx --yes jentic-openapi-validator-speclynx-0.1.0.tgz",
            timeout: float = 600.0,
            allowed_base_dir: str | Path | None = None,
            plugins_dir: str | Path | None = None,
    ) -> None
```

**Parameters:**

- `speclynx_path`: Path to the SpecLynx CLI executable. Default uses bundled npm tarball via npx. Can be a custom path
  like `/usr/local/bin/speclynx` or an npx command with additional packages (optional)
- `timeout`: Maximum execution time in seconds (default: 600.0)
- `allowed_base_dir`: Optional base directory for path security validation. When set, all document paths are validated
  to be within this directory, providing defense against path traversal attacks. When `None` (default), only file
  extension validation is performed (no base directory containment check). Recommended for web services or untrusted
  input (optional)
- `plugins_dir`: Optional directory containing additional validation plugins (`.mjs` files). When specified, custom
  plugins are merged with built-in plugins (both are loaded). If `None` (default), only built-in plugins are used
  (optional)

**Methods:**

- `accepts() -> list[Literal["uri", "dict"]]`: Returns supported document format identifiers
- `validate(document: str | dict, *, base_url: str | None = None, target: str | None = None) -> ValidationResult`:
  Validates an OpenAPI document

**Exceptions:**

- `RuntimeError`: SpecLynx execution fails
- `SubprocessExecutionError`: SpecLynx times out or fails to start
- `TypeError`: Unsupported document type
- `PathTraversalError`: Document path attempts to escape allowed_base_dir (only when `allowed_base_dir` is set)
- `InvalidExtensionError`: Document path has disallowed file extension (always checked for filesystem paths)