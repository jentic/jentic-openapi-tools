# jentic-openapi-datamodels

Low-level data models for OpenAPI specifications.

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
- **OpenAPI 3.0.x**: Fully implemented
- **OpenAPI 3.1.x**: Fully implemented with JSON Schema 2020-12 support
- **OpenAPI 3.2.x**: Planned for future release

## Installation

```bash
pip install jentic-openapi-datamodels
```

**Prerequisites:**
- Python 3.11+

## Quick Start

### Parsing OpenAPI 3.0 Documents

The main use case is parsing complete OpenAPI Documents:

```python
from ruamel.yaml import YAML
from jentic.apitools.openapi.datamodels.low.v30 import build

# Parse OpenAPI document
yaml = YAML()
root = yaml.compose("""
openapi: 3.0.4
info:
  title: Pet Store API
  version: 1.0.0
paths:
  /pets:
    get:
      summary: List all pets
      responses:
        '200':
          description: A list of pets
""")

# Build OpenAPI document model
openapi_doc = build(root)

# Access document fields via Python naming (snake_case)
print(openapi_doc.openapi.value)  # "3.0.4"
print(openapi_doc.info.value.title.value)  # "Pet Store API"
print(openapi_doc.info.value.version.value)  # "1.0.0"

# Access nested fields with full type safety
for path_key, path_item in openapi_doc.paths.value.path_items.items():
    print(f"Path: {path_key.value}")  # "/pets"
    if path_item.value.get:
        operation = path_item.value.get.value
        print(f"  Summary: {operation.summary.value}")  # "List all pets"
```

### Parsing OpenAPI 3.1 Documents with JSON Schema 2020-12

OpenAPI 3.1 fully supports JSON Schema 2020-12, including advanced features like boolean schemas, conditional validation and vocabulary declarations:

```python
from ruamel.yaml import YAML
from jentic.apitools.openapi.datamodels.low.v31 import build

# Parse OpenAPI 3.1 document with JSON Schema 2020-12 features
yaml = YAML()
root = yaml.compose("""
openapi: 3.1.2
info:
  title: Pet Store API
  version: 1.0.0
paths:
  /pets:
    get:
      responses:
        '200':
          description: Pet list
          content:
            application/json:
              schema:
                type: array
                prefixItems:
                  - type: string
                  - type: integer
                items: false
                contains:
                  type: object
                  required: [id]
""")

openapi_doc = build(root)

# Access JSON Schema 2020-12 features
schema = openapi_doc.paths.value.path_items["/pets"].value.get.value.responses.value["200"].value.content.value["application/json"].value.schema
print(schema.prefix_items.value[0].type.value)  # "string"
print(schema.items.value)  # False (boolean schema)
print(schema.contains.value.required.value[0].value)  # "id"
```

### Parsing Individual Spec Objects

You can also parse individual OpenAPI specification objects:

```python
from ruamel.yaml import YAML
from jentic.apitools.openapi.datamodels.low.v30.security_scheme import build as build_security_scheme

# Parse a Security Scheme object
yaml = YAML()
root = yaml.compose("""
type: http
scheme: bearer
bearerFormat: JWT
""")

security_scheme = build_security_scheme(root)

# Access via Python field names (snake_case)
print(security_scheme.bearer_format.value)  # "JWT"

# Access source location information
print(security_scheme.bearer_format.key_node.value)  # "bearerFormat"
print(security_scheme.bearer_format.key_node.start_mark.line)  # Line number
```

You can also parse OpenAPI 3.1 Schema objects with JSON Schema 2020-12 features:

```python
from ruamel.yaml import YAML
from jentic.apitools.openapi.datamodels.low.v31.schema import build as build_schema

# Parse a Schema object with JSON Schema 2020-12 features
yaml = YAML()
root = yaml.compose("""
type: object
properties:
  id:
    type: integer
  tags:
    type: array
    prefixItems:
      - type: string
      - type: string
    items: false
patternProperties:
  "^x-":
    type: string
unevaluatedProperties: false
if:
  properties:
    premium:
      const: true
then:
  required: [support_tier]
""")

schema = build_schema(root)

# Access JSON Schema 2020-12 fields via Python naming (snake_case)
print(schema.properties.value["id"].type.value)  # "integer"
print(schema.pattern_properties.value["^x-"].type.value)  # "string"
print(schema.unevaluated_properties.value)  # False
print(schema.prefix_items.value[0].type.value)  # "string"

# Access conditional schema fields
print(schema.if_.value.properties.value["premium"].const.value)  # True
print(schema.then_.value.required.value[0].value)  # "support_tier"

# Access source location information
print(schema.type.key_node.start_mark.line)  # Line number for "type" key
```

### Field Name Mapping

YAML `camelCase` fields automatically map to Python `snake_case`:
- `bearerFormat` → `bearer_format`
- `authorizationUrl` → `authorization_url`
- `openIdConnectUrl` → `openid_connect_url`

Special cases for Python reserved keywords and `$` fields:

- `in` → `in_`
- `if` → `if_`
- `then` → `then_`
- `else` → `else_`
- `not` → `not_`
- `$ref` → `ref_`
- `$id` → `id_`
- `$schema` → `schema_`

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
from jentic.apitools.openapi.datamodels.low.v30 import build

# FieldSource: Fixed specification fields in OpenAPI document
yaml = YAML()
root = yaml.compose("""
openapi: 3.0.4
info:
  title: Pet Store API
  version: 1.0.0
paths: {}
""")
openapi_doc = build(root)

field = openapi_doc.info.value.title  # FieldSource[str]
print(field.value)  # "Pet Store API" - The actual value
print(field.key_node)  # YAML node for "title"
print(field.value_node)  # YAML node for "Pet Store API"

# KeySource/ValueSource: Dictionary fields (extensions, mapping)
# Extensions in OpenAPI objects use KeySource/ValueSource
root = yaml.compose("""
openapi: 3.0.4
info:
  title: API
  version: 1.0.0
  x-custom: value
  x-another: data
paths: {}
""")
openapi_doc = build(root)

for key, value in openapi_doc.info.value.extensions.items():
    print(key.value)  # KeySource[str]: "x-custom" or "x-another"
    print(key.key_node)  # YAML node for the extension key
    print(value.value)  # ValueSource: "value" or "data"
    print(value.value_node)  # YAML node for the extension value
```

### Location Ranges

Access precise location ranges within the source document using start_mark and end_mark:

```python
from ruamel.yaml import YAML
from jentic.apitools.openapi.datamodels.low.v30 import build

yaml_content = """
openapi: 3.0.4
info:
  title: Pet Store API
  version: 1.0.0
  description: A sample Pet Store API
paths: {}
"""

yaml = YAML()
root = yaml.compose(yaml_content)
openapi_doc = build(root)

# Access location information for any field
field = openapi_doc.info.value.title

# Key location (e.g., "title")
print(f"Key start: line {field.key_node.start_mark.line}, col {field.key_node.start_mark.column}")
print(f"Key end: line {field.key_node.end_mark.line}, col {field.key_node.end_mark.column}")

# Value location (e.g., "Pet Store API")
print(f"Value start: line {field.value_node.start_mark.line}, col {field.value_node.start_mark.column}")
print(f"Value end: line {field.value_node.end_mark.line}, col {field.value_node.end_mark.column}")

# Full field range (from key start to value end)
start = field.key_node.start_mark
end = field.value_node.end_mark
print(f"Field range: ({start.line}:{start.column}) to ({end.line}:{end.column})")
```

### Invalid Data Handling

Low-level models preserve invalid data without validation:

```python
from ruamel.yaml import YAML
from jentic.apitools.openapi.datamodels.low.v30 import build

yaml = YAML()
root = yaml.compose("""
openapi: 3.0.4
info:
  title: 123  # Intentionally wrong type for demonstration (should be string)
  version: 1.0.0
paths: {}
""")

openapi_doc = build(root)
print(openapi_doc.info.value.title.value)  # 123 (preserved as-is)
print(type(openapi_doc.info.value.title.value))  # <class 'int'>

# Invalid data is preserved with full source tracking for validation tools
print(openapi_doc.info.value.title.value_node.start_mark.line)  # Line number
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
