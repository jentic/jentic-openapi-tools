# jentic-openapi-datamodels

Low-level and high-level data models for OpenAPI specifications.

## Overview

This package provides data model classes for representing OpenAPI specification objects in Python. The models are designed to be:

- **Dict-like**: Implement `MutableMapping` for easy data access
- **Unvalidated**: Separate parsing from validation for performance
- **Extensible**: Support OpenAPI specification extensions (x-* fields)
- **Version-aware**: Currently implements OpenAPI 3.0.x (3.1.x planned)

## Structure

- `datamodels.low.v30`: Low-level models for OpenAPI 3.0.x

## Usage

```python
from jentic.apitools.openapi.datamodels.low.v30 import Schema

# Create a schema from raw data
schema = Schema({
    "type": "object",
    "properties": {
        "name": {"type": "string"}
    }
})

# Access via properties
print(schema.type)  # "object"

# Access via dict
print(schema["type"])  # "object"

# Convert back to dict
data = schema.to_mapping()
```
