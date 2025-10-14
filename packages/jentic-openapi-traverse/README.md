# jentic-openapi-traverse

A Python library for traversing OpenAPI documents. This package is part of the Jentic OpenAPI Tools ecosystem and provides two types of traversal:

1. **JSON Traversal** (current) - Generic depth-first traversal of JSON-like structures
2. **Datamodel Traversal** (planned) - OpenAPI-aware semantic traversal with visitor pattern

## Installation

```bash
pip install jentic-openapi-traverse
```

**Prerequisites:**
- Python 3.11+

---

## JSON Traversal (Current Implementation)

Generic depth-first traversal of any JSON-like structure (dicts, lists, scalars).
Works with raw parsed OpenAPI documents or any other JSON data.

### Quick Start

```python
from jentic.apitools.openapi.traverse.json import traverse

# Traverse a nested structure
data = {
    "openapi": "3.1.0",
    "info": {"title": "My API", "version": "1.0.0"},
    "paths": {
        "/users": {
            "get": {"summary": "List users"}
        }
    }
}

# Walk all nodes
for node in traverse(data):
    print(f"{node.format_path()}: {node.value}")
```

Output:
```
openapi: 3.1.0
info: {'title': 'My API', 'version': '1.0.0'}
info.title: My API
info.version: 1.0.0
paths: {'/users': {'get': {'summary': 'List users'}}}
paths./users: {'get': {'summary': 'List users'}}
paths./users.get: {'summary': 'List users'}
paths./users.get.summary: List users
```

### Working with Paths

```python
from jentic.apitools.openapi.traverse.json import traverse

data = {
    "users": [
        {"name": "Alice", "email": "alice@example.com"},
        {"name": "Bob", "email": "bob@example.com"}
    ]
}

for node in traverse(data):
    # Access path information
    print(f"Path: {node.path}")
    print(f"Segment: {node.segment}")
    print(f"Full path: {node.full_path}")
    print(f"Formatted: {node.format_path()}")
    print(f"Depth: {len(node.ancestors)}")
    print()
```

### Custom Path Formatting

```python
for node in traverse(data):
    # Default dot separator
    print(node.format_path())  # e.g., "paths./users.get.summary"

    # Custom separator
    print(node.format_path(separator="/"))  # e.g., "paths//users/get/summary"
```

### Finding Specific Nodes

```python
# Find all $ref references in a document
refs = [
    node.value["$ref"]
    for node in traverse(openapi_doc)
    if isinstance(node.value, dict) and "$ref" in node.value
]

# Find all nodes at a specific path segment
schemas = [
    node.value
    for node in traverse(openapi_doc)
    if node.segment == "schema"
]

# Find deeply nested values
response_descriptions = [
    node.value
    for node in traverse(openapi_doc)
    if node.segment == "description" and "responses" in node.path
]
```

### API Reference

#### `traverse(root: JSONValue) -> Iterator[TraversalNode]`

Performs depth-first traversal of a JSON-like structure.

**Parameters:**
- `root`: The data structure to traverse (dict, list, or scalar)

**Returns:**
- Iterator of `TraversalNode` objects

**Yields:**
- For dicts: one node per key-value pair
- For lists: one node per index-item pair
- Scalars at root don't yield nodes (but are accessible via parent nodes)

#### `TraversalNode`

Immutable dataclass representing a node encountered during traversal.

**Attributes:**
- `path: JSONPath` - Path from root to the parent container (tuple of segments)
- `parent: JSONContainer` - The parent container (dict or list)
- `segment: PathSeg` - The key (for dicts) or index (for lists) within parent
- `value: JSONValue` - The actual value at `parent[segment]`
- `ancestors: tuple[JSONValue, ...]` - Ordered tuple of values from root down to (but not including) parent

**Properties:**
- `full_path: JSONPath` - Complete path from root to this value (`path + (segment,)`)

**Methods:**
- `format_path(separator: str = ".") -> str` - Format the full path as a human-readable string

### Usage Examples

#### Collecting All Schemas

```python
from jentic.apitools.openapi.traverse.json import traverse

def collect_schemas(openapi_doc):
    """Collect all schema objects from an OpenAPI document."""
    schemas = []

    for node in traverse(openapi_doc):
        if node.segment == "schema" and isinstance(node.value, dict):
            schemas.append({
                "path": node.format_path(),
                "schema": node.value
            })

    return schemas
```


#### Analyzing Document Structure

```python
def analyze_depth(data):
    """Analyze the depth distribution of a document."""
    max_depth = 0
    depth_counts = {}

    for node in traverse(data):
        depth = len(node.ancestors)
        max_depth = max(max_depth, depth)
        depth_counts[depth] = depth_counts.get(depth, 0) + 1

    return {
        "max_depth": max_depth,
        "depth_distribution": depth_counts
    }
```

### Testing

The package includes comprehensive test coverage for JSON traversal:

```bash
uv run --package jentic-openapi-traverse pytest packages/jentic-openapi-traverse/tests -v
```