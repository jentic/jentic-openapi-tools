# jentic-openapi-transformer

A Python library for transforming and bundling OpenAPI documents. This package is part of the Jentic OpenAPI Tools ecosystem and provides a flexible, extensible architecture for OpenAPI document transformation with support for pluggable backends.

## Features

- **Pluggable Backend Architecture**: Support for multiple bundling strategies via entry points
- **Multiple Input Formats**: Accept OpenAPI documents as file paths, URIs, or Python dictionaries
- **Flexible Output Types**: Return bundled documents as JSON strings or Python dictionaries
- **Type Safety**: Full type hints with overloaded methods for precise return types
- **Extensible Design**: Easy integration of third-party bundling backends

## Installation

```bash
pip install jentic-openapi-transformer
```

**Prerequisites:**
- Python 3.11+

**Optional Backends:**

For advanced bundling with external reference resolution:

```bash
pip install jentic-openapi-transformer-redocly
```

## Quick Start

### Basic Bundling

```python
from jentic.apitools.openapi.transformer.bundler.core import OpenAPIBundler

# Create a bundler with the default backend
bundler = OpenAPIBundler()

# Bundle from a file URI and return as dictionary
result = bundler.bundle("file:///path/to/openapi.yaml", return_type=dict)
print(result["info"]["title"])

# Bundle from a file URI and return as JSON string
json_result = bundler.bundle("file:///path/to/openapi.yaml", return_type=str)
print(json_result)
```

### Bundle from Dictionary

```python
# Bundle an OpenAPI document from a Python dictionary
openapi_doc = {
    "openapi": "3.1.0",
    "info": {"title": "My API", "version": "1.0.0"},
    "paths": {
        "/users": {
            "get": {
                "summary": "Get users",
                "responses": {"200": {"description": "Success"}}
            }
        }
    }
}

result = bundler.bundle(openapi_doc, return_type=dict)
```

### Using Different Backends

```python
# Use the default backend (no external reference resolution)
bundler = OpenAPIBundler("default")
result = bundler.bundle("/path/to/openapi.yaml", return_type=dict)

# Use the Redocly backend (requires jentic-openapi-transformer-redocly)
bundler = OpenAPIBundler("redocly")
result = bundler.bundle("/path/to/openapi.yaml", return_type=dict)
```

## Configuration Options

### Backend Selection

```python
# Use default backend by name
bundler = OpenAPIBundler("default")

# Pass a backend instance directly
from jentic.apitools.openapi.transformer.bundler.backends.default import DefaultBundlerBackend
backend = DefaultBundlerBackend()
bundler = OpenAPIBundler(backend=backend)

# Pass a backend class
bundler = OpenAPIBundler(backend=DefaultBundlerBackend)
```

### Custom Parser

```python
from jentic.apitools.openapi.parser.core import OpenAPIParser

# Use a custom parser instance
parser = OpenAPIParser()
bundler = OpenAPIBundler(parser=parser)
```

### Return Type Control

```python
# Return as dictionary (typed)
dict_result: dict = bundler.bundle(document, return_type=dict)

# Return as JSON string (typed)
str_result: str = bundler.bundle(document, return_type=str)

# Return as plain (auto-detected type)
plain_result = bundler.bundle(document)
```

### Strict Mode

```python
# Enable strict type checking for return type
try:
    result = bundler.bundle(document, return_type=dict, strict=True)
except TypeError as e:
    print(f"Type mismatch: {e}")
```

## Testing

Run the test suite:

```bash
uv run --package jentic-openapi-transformer pytest packages/jentic-openapi-transformer -v
```

### Integration Tests

The package includes integration tests for backend discovery and bundling. Tests requiring external backends (like Redocly) will be automatically skipped if the backend package is not installed.

## API Reference

### OpenAPIBundler

```python
class OpenAPIBundler:
    def __init__(
        self,
        backend: str | BaseBundlerBackend | Type[BaseBundlerBackend] | None = None,
        parser: OpenAPIParser | None = None,
    ) -> None
```

**Parameters:**
- `backend`: Backend name, instance, or class. Defaults to "default"
- `parser`: Custom OpenAPIParser instance (optional)

**Methods:**

- `bundle(document: str | dict, base_url: str | None = None, *, return_type: type[T] | None = None, strict: bool = False) -> T`
  - Bundles an OpenAPI document with specified return type
  - `document`: File path, URI, JSON/YAML string, or dictionary
  - `base_url`: Optional base URL for resolving relative references
  - `return_type`: Desired output type (str, dict, or None for auto)
  - `strict`: Enable strict return type validation

## Available Backends

### base
Abstract base class for custom bundler backends. Not for direct use.

### default
Basic bundling backend without external reference resolution. Suitable for single-file OpenAPI documents.

### redocly (Optional)
Advanced bundling backend using Redocly CLI with full reference resolution across multiple files.

Install: `pip install jentic-openapi-transformer-redocly`
