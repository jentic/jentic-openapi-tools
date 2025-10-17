# jentic-openapi-parser

A Python library for parsing OpenAPI documents using pluggable parser backends. This package is part of the Jentic OpenAPI Tools ecosystem and provides a flexible, extensible architecture for OpenAPI document parsing with support for multiple YAML/JSON parsing libraries.

## Features

- **Pluggable Backend Architecture**: Support for multiple parsing strategies via entry points
- **Multiple Input Formats**: Parse OpenAPI documents from file URIs or text strings (JSON/YAML)
- **Multiple Parser Backends**: Choose from PyYAML, ruamel.yaml, or ruamel.yaml roundtrip modes
- **Enhanced JSON Serialization**: Built-in support for datetime, UUID, Path, Decimal, Enum, and attrs classes
- **Type Safety**: Full type hints with overloaded methods for precise return types
- **Extensible Design**: Easy integration of third-party parser backends

## Installation

```bash
pip install jentic-openapi-parser
```

**Prerequisites:**
- Python 3.11+

## Quick Start

### Basic Parsing

```python
from jentic.apitools.openapi.parser.core import OpenAPIParser

# Create parser with default backend (pyyaml)
parser = OpenAPIParser()

# Parse from file URI
doc = parser.parse("file:///path/to/openapi.yaml")
print(doc["info"]["title"])

# Parse from JSON string
json_doc = '{"openapi":"3.1.0","info":{"title":"My API","version":"1.0.0"}}'
doc = parser.parse(json_doc)

# Parse from YAML string
yaml_doc = """
openapi: 3.1.0
info:
  title: My API
  version: 1.0.0
"""
doc = parser.parse(yaml_doc)
```

### Parse with Type Conversion

```python
from ruamel.yaml import CommentedMap

# Parse with specific return type
parser = OpenAPIParser("ruamel-roundtrip")
doc = parser.parse(yaml_doc, return_type=CommentedMap)

# Parse with strict type checking
doc = parser.parse(yaml_doc, return_type=CommentedMap, strict=True)
```

### Using Different Backends

```python
# Use PyYAML backend (default)
parser = OpenAPIParser("pyyaml")
doc = parser.parse("file:///path/to/openapi.yaml")

# Use ruamel.yaml backend (safe mode)
parser = OpenAPIParser("ruamel-safe")
doc = parser.parse("file:///path/to/openapi.yaml")

# Use ruamel.yaml roundtrip mode (preserves comments and formatting info)
parser = OpenAPIParser("ruamel-roundtrip")
doc = parser.parse("file:///path/to/openapi.yaml", return_type=CommentedMap)
# Access line/column information
print(doc.lc.line, doc.lc.col)
```

## Configuration Options

### Backend Selection

```python
# Use backend by name
parser = OpenAPIParser("pyyaml")

# Pass backend instance directly
from jentic.apitools.openapi.parser.backends.pyyaml import PyYAMLParserBackend
backend = PyYAMLParserBackend()
parser = OpenAPIParser(backend=backend)

# Pass backend class
parser = OpenAPIParser(backend=PyYAMLParserBackend)
```

### Custom Configuration

```python
import logging

# Configure with custom logger and timeouts
logger = logging.getLogger(__name__)
parser = OpenAPIParser(
    backend="pyyaml",
    logger=logger,
    conn_timeout=10,  # Connection timeout in seconds
    read_timeout=30   # Read timeout in seconds
)
```

## Working with Return Types

The parser supports flexible return type handling:

```python
from ruamel.yaml import CommentedMap

parser = OpenAPIParser("ruamel-roundtrip")

# Without return_type: Returns plain dict
doc = parser.parse(yaml_doc)
assert isinstance(doc, dict)

# With return_type: Returns specified type
doc = parser.parse(yaml_doc, return_type=CommentedMap)
assert isinstance(doc, CommentedMap)

# With strict=True: Raises error if type doesn't match
try:
    doc = parser.parse(yaml_doc, return_type=list, strict=True)
except TypeConversionError:
    print("Type mismatch!")
```

## API Reference

### OpenAPIParser

```python
class OpenAPIParser:
    def __init__(
        self,
        backend: str | BaseParserBackend | Type[BaseParserBackend] | None = None,
        *,
        logger: logging.Logger | None = None,
        conn_timeout: int = 5,
        read_timeout: int = 10,
    ) -> None
```

**Parameters:**
- `backend`: Parser backend to use. Can be:
  - `str`: Name of a backend registered via entry points (e.g., "pyyaml", "ruamel-safe", "ruamel-roundtrip")
  - `BaseParserBackend`: Instance of a parser backend
  - `Type[BaseParserBackend]`: Class of a parser backend (will be instantiated)
  - Defaults to `"pyyaml"` if `None`
- `logger`: Custom logger instance (optional)
- `conn_timeout`: Connection timeout in seconds for URI loading
- `read_timeout`: Read timeout in seconds for URI loading

**Methods:**

- `parse(document: str) -> dict[str, Any]`
  - Parse without type conversion, returns plain dict

- `parse(document: str, *, return_type: type[T], strict: bool = False) -> T`
  - Parse with optional type conversion
  - `document`: File URI or text string (JSON/YAML)
  - `return_type`: Expected return type (e.g., `dict`, `CommentedMap`)
  - `strict`: If `True`, raises `TypeConversionError` if result doesn't match `return_type`
  - Returns: Parsed document

- `load_uri(uri: str) -> str`
  - Load content from a URI (HTTP(S), file://, or local file path)

- `list_backends() -> list[str]`
  - Static method to list all available parser backends

### JSON Serialization

The parser includes enhanced JSON serialization utilities for working with OpenAPI documents:

```python
from jentic.apitools.openapi.parser.core import json_dumps

# Serialize with special type support
from datetime import datetime
from pathlib import Path
from uuid import UUID

data = {
    "timestamp": datetime(2025, 10, 1, 12, 0, 0),
    "id": UUID("550e8400-e29b-41d4-a716-446655440000"),
    "path": Path("/var/log/app.log")
}

json_str = json_dumps(data, indent=2)
# Output:
# {
#   "id": "550e8400-e29b-41d4-a716-446655440000",
#   "path": "/var/log/app.log",
#   "timestamp": "2025-10-01T12:00:00"
# }
```

**Supported Types:**
- `datetime` / `date` - Serialized to ISO 8601 format
- `UUID` - Converted to string
- `Path` - Converted to string
- `Decimal` - Converted to float
- `Enum` - Serialized using enum value
- `attrs` classes - Converted to dictionaries

### Exceptions

```python
from jentic.apitools.openapi.parser.core.exceptions import (
    OpenAPIParserError,        # Base exception
    DocumentParseError,        # Parsing failed
    DocumentLoadError,         # URI loading failed
    InvalidBackendError,       # Backend initialization failed
    BackendNotFoundError,      # Backend not found
    TypeConversionError,       # Type conversion failed
)
```

## Available Backends

### pyyaml (Default)
Standard PyYAML-based parser. Fast and reliable for basic parsing needs.

**Accepts:** `text` (JSON/YAML strings)

```python
parser = OpenAPIParser("pyyaml")
doc = parser.parse(content)
```

### ruamel-safe
ruamel.yaml-based parser with safe loading. Provides better YAML 1.2 support than PyYAML.

**Accepts:** `text` (JSON/YAML strings), `uri` (file paths/URLs)

```python
parser = OpenAPIParser("ruamel-safe")
doc = parser.parse(content)
```

### ruamel-roundtrip
ruamel.yaml roundtrip mode that preserves comments, formatting, and provides line/column information.

**Accepts:** `text` (JSON/YAML strings), `uri` (file paths/URLs)

```python
from ruamel.yaml import CommentedMap

parser = OpenAPIParser("ruamel-roundtrip")
doc = parser.parse(content, return_type=CommentedMap)

# Access line/column information
print(f"Line: {doc.lc.line}, Column: {doc.lc.col}")
```

## Testing

Run the test suite:

```bash
uv run --package jentic-openapi-parser pytest packages/jentic-openapi-parser -v
```