from semantic_release.cli.commands.version import build_distributions

# jentic-openapi-datamodels

Low-level and high-level data models for OpenAPI specifications.

This package provides data model classes for representing OpenAPI specification objects in Python.

## Features

**Low-Level Architecture**
- **Preserve Everything**: All data from source documents preserved exactly as-is, including invalid values
- **Zero Validation**: No validation or coercion during parsing - deferred to higher layers
- **Separation of Concerns**: Low-level model focuses on faithful representation; validation belongs elsewhere

**Source Tracking**
- **Complete Source Fidelity**: Every field tracks its exact YAML node location
- **Precise Error Reporting**: Line and column numbers via `start_mark` and `end_mark`
- **Metadata Preservation**: Full position tracking for accurate diagnostics

**Python Integration**
- **Python-Idiomatic Naming**: snake_case field names (e.g., `bearer_format`, `property_name`)
- **Spec-Aligned Mapping**: Automatic YAML name mapping (e.g., `bearerFormat` ↔ `bearer_format`)
- **Type Safety**: Full type hints with Generic types (`FieldSource[T]`, `KeySource[T]`, `ValueSource[T]`)

**Extensibility**
- **Extension Support**: Automatic extraction of OpenAPI `x-*` specification extensions
- **Unknown Field Tracking**: Capture typos and invalid fields for validation tools
- **Generic Builder Pattern**: Core `build_model()` function with object-specific builders for complex cases

**Performance**
- **Memory Efficient**: Immutable frozen dataclasses with `__slots__` for optimal memory usage
- **Shared Context**: All instances share a single YAML constructor for efficiency

**Version Support**
- **OpenAPI 2.0**: Planned for future release
- **OpenAPI 3.0.x**: Currently implemented
- **OpenAPI 3.1.x**: Planned for future release
- **OpenAPI 3.2.x**: Planned for future release

## Installation

```bash
pip install jentic-openapi-datamodels
```

**Prerequisites:**
- Python 3.11+

## Quick Start

### Basic Usage

```python
from ruamel.yaml import YAML
from jentic.apitools.openapi.datamodels.low.v30.security_scheme import build

# Parse YAML
yaml = YAML()
root = yaml.compose("""
type: http
scheme: bearer
bearerFormat: JWT
""")

# Build low-level model
security_scheme = build(root)

# Access via Python field names (snake_case)
print(security_scheme.bearer_format.value)  # "JWT"

# Access source location information
print(security_scheme.bearer_format.key_node.value)  # "bearerFormat"
print(security_scheme.bearer_format.key_node.start_mark.line)  # Line number
```

### Field Name Mapping

YAML `camelCase` fields automatically map to Python `snake_case`:
- `bearerFormat` → `bearer_format`
- `authorizationUrl` → `authorization_url`
- `openIdConnectUrl` → `openid_connect_url`

Special cases for Python reserved keywords/special characters:
- `$ref` → `ref`
- `in` → `in_`

### Source Tracking

The package provides three immutable wrapper types for preserving source information:

**FieldSource[T]** - For OpenAPI fields with key-value pairs
- Used for: Fixed fields (`name`, `bearer_format`) and patterned fields (status codes, path items, schema properties)
- Tracks: Both key and value nodes
- Example: `SecurityScheme.bearer_format` is `FieldSource[str]`, response status codes are `FieldSource[Response]`

**KeySource[T]** - For dictionary keys
- Used for: keys in OpenAPI fields, `x-*` extensions and mapping dictionaries
- Tracks: Only key node
- Example: Keys in `Discriminator.mapping` are `KeySource[str]`

**ValueSource[T]** - For dictionary values and array items
- Used for: values in OpenAPI fields, in `x-*` extensions, mapping dictionaries and array items
- Tracks: Only value node
- Example: Values in `Discriminator.mapping` are `ValueSource[str]`

```python
from ruamel.yaml import YAML
from jentic.apitools.openapi.datamodels.low.v30.security_scheme import build as build_security_scheme
from jentic.apitools.openapi.datamodels.low.v30.discriminator import build as build_discriminator

# FieldSource: Fixed specification fields
yaml = YAML()
root = yaml.compose("type: http\nscheme: bearer\nbearerFormat: JWT")
security_scheme = build_security_scheme(root)

field = security_scheme.bearer_format  # FieldSource[str]
print(field.value)  # "JWT" - The actual value
print(field.key_node)  # YAML node for "bearerFormat"
print(field.value_node)  # YAML node for "JWT"

# KeySource/ValueSource: Dictionary fields (mapping, extensions)
root = yaml.compose("propertyName: petType\nmapping:\n  dog: Dog\n  cat: Cat")
discriminator = build_discriminator(root)

for key, value in discriminator.mapping.value.items():
    print(key.value)  # KeySource[str]: "dog" or "cat"
    print(key.key_node)  # YAML node for the key
    print(value.value)  # ValueSource[str]: "Dog" or "Cat"
    print(value.value_node)  # YAML node for the value
```

### Location Ranges

Access precise location ranges within the source document using start_mark and end_mark:

```python
from ruamel.yaml import YAML
from jentic.apitools.openapi.datamodels.low.v30.security_scheme import build as build_security_scheme

yaml_content = """
type: http
scheme: bearer
bearerFormat: JWT
description: Bearer token authentication
"""

yaml = YAML()
root = yaml.compose(yaml_content)
security_scheme = build_security_scheme(root)

# Access location information for any field
field = security_scheme.bearer_format

# Key location (e.g., "bearerFormat")
print(f"Key start: line {field.key_node.start_mark.line}, col {field.key_node.start_mark.column}")
print(f"Key end: line {field.key_node.end_mark.line}, col {field.key_node.end_mark.column}")

# Value location (e.g., "JWT")
print(f"Value start: line {field.value_node.start_mark.line}, col {field.value_node.start_mark.column}")
print(f"Value end: line {field.value_node.end_mark.line}, col {field.value_node.end_mark.column}")

# Full field range (from key start to value end)
start = field.key_node.start_mark
end = field.value_node.end_mark
print(f"Field range: ({start.line}:{start.column}) to ({end.line}:{end.column})")
```

### Invalid Data Handling

Low-level models preserve invalid data:

```python
from ruamel.yaml import YAML
from jentic.apitools.openapi.datamodels.low.v30.security_scheme import build as build_security_scheme

yaml = YAML()
root = yaml.compose("bearerFormat: 123")  # Wrong type (should be string)

security_scheme = build_security_scheme(root)
print(security_scheme.bearer_format.value)  # 123 (preserved as-is)
print(type(security_scheme.bearer_format.value))  # <class 'int'>
```

### Error Reporting

This architecture—where the low-level model preserves data without validation and validation tools consume 
that data—allows the low-level model to remain simple while enabling sophisticated validation tools to provide
user-friendly error messages with exact source locations.

## Testing

Run the test suite:

```bash
uv run --package jentic-openapi-datamodels pytest packages/jentic-openapi-datamodels -v
```
