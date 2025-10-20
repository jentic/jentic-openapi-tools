# jentic-openapi-transformer-redocly

A Python library that provides OpenAPI document bundling functionality using [Redocly CLI](https://redocly.com/docs/cli/). This package is part of the Jentic OpenAPI Tools ecosystem and implements the transformer backend pattern for bundling OpenAPI documents by resolving external references.

## Features

- **Multiple Input Formats**: Support for file paths, URIs, and Python dictionaries
- **External Reference Resolution**: Automatically resolves `$ref` references across multiple files
- **Robust Error Handling**: Comprehensive error reporting with detailed messages
- **Timeout Configuration**: Configurable timeout for long-running bundling operations
- **Type Safety**: Full type hints and comprehensive documentation


## Installation

```bash
pip install jentic-openapi-transformer-redocly
```

**Prerequisites:**
- Node.js and npm (for Redocly CLI)
- Python 3.11+

The Redocly CLI will be automatically downloaded via npx on first use, or you can install it globally:

```bash
npm install -g @redocly/cli
```

## Quick Start

### Basic Usage

```python
from jentic.apitools.openapi.transformer.bundler.backends.redocly import RedoclyBundlerBackend

# Create a bundler instance
bundler = RedoclyBundlerBackend()

# Bundle an OpenAPI document from a file path
result = bundler.bundle("/path/to/your/openapi.yaml")
print(result)  # Bundled OpenAPI document as JSON string
```

### Using with Dictionary Input

```python
# Bundle an OpenAPI document from a Python dictionary
openapi_dict = {
    "openapi": "3.0.3",
    "info": {"title": "My API", "version": "1.0.0"},
    "paths": {
        "/users": {
            "get": {
                "responses": {"200": {"description": "Success"}}
            }
        }
    }
}

result = bundler.bundle(openapi_dict)
parsed_result = json.loads(result)
```

### Custom Configuration

```python
# Custom Redocly CLI path and timeout
bundler = RedoclyBundlerBackend(
    redocly_path="redocly",  # Use global redocly installation
    timeout=60.0  # 60 second timeout
)

result = bundler.bundle("https://petstore3.swagger.io/api/v3/openapi.json")
```

## Advanced Usage

## Error Handling

The bundler provides detailed error reporting for various failure scenarios:

```python
from jentic.apitools.openapi.transformer.bundler.backends.redocly import RedoclyBundlerBackend
from jentic.apitools.openapi.common.subproc import SubprocessExecutionError

bundler = RedoclyBundlerBackend()

try:
    result = bundler.bundle("/path/to/openapi.yaml")
except TypeError as e:
    print(f"Unsupported document type: {e}")
except SubprocessExecutionError as e:
    print(f"Redocly CLI execution failed: {e}")
except RuntimeError as e:
    print(f"Bundling failed: {e}")
```

### Supported Input Formats

The bundler accepts the following input formats (returned by `accepts()` method):

- **`"uri"`**: File paths or URIs pointing to OpenAPI documents
- **`"dict"`**: Python dictionaries containing OpenAPI document data

## Testing

### Integration Tests

The integration tests require Redocly CLI to be available. They will be automatically skipped if Redocly is not installed.

**Run the integration test:**

```bash
uv run --package jentic-openapi-transformer-redocly pytest packages/jentic-openapi-transformer-redocly -v
```

## API Reference

### RedoclyBundler

```python
class RedoclyBundlerBackend(BaseBundlerBackend):
    def __init__(
        self,
        redocly_path: str = "npx --yes @redocly/cli@^2.4.0",
        timeout: float = 600.0,
        allowed_base_dir: str | Path | None = None,
    ) -> None
```

**Parameters:**
- `redocly_path`: Path to Redocly CLI executable
- `timeout`: Maximum execution time in seconds
- `allowed_base_dir`: Optional base directory for path security validation. When set, all document paths are validated to be within this directory, providing defense against path traversal attacks. When `None` (default), only file extension validation is performed (no base directory containment check). Recommended for web services or untrusted input (optional)

**Methods:**

- `accepts() -> list[str]`: Returns supported document format identifiers
- `bundle(document: str | dict, base_url: str | None = None) -> str`: Bundles an OpenAPI document

**Exceptions:**
- `TypeError`: Document type is not supported
- `RuntimeError`: Redocly execution fails or produces invalid output
- `SubprocessExecutionError`: Redocly times out or fails to start
- `PathTraversalError`: Document path attempts to escape allowed_base_dir (only when `allowed_base_dir` is set)
- `InvalidExtensionError`: Document path has disallowed file extension (always checked for filesystem paths)
