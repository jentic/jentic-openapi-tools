# jentic-openapi-traverse

A Python library for traversing OpenAPI documents. This package is part of the Jentic OpenAPI Tools ecosystem and provides two types of traversal:

1. **Datamodel Traversal** - OpenAPI-aware semantic traversal with visitor pattern
2. **JSON Traversal** - Generic depth-first traversal of JSON-like structures

## Installation

```bash
pip install jentic-openapi-traverse
```

**Prerequisites:**
- Python 3.11+

---

## Datamodel Traversal

OpenAPI-aware semantic traversal using the visitor pattern. Works with low-level datamodels from `jentic-openapi-datamodels` package, preserving source location information and providing structured access to OpenAPI nodes.

### Quick Start

```python
from jentic.apitools.openapi.parser.core import OpenAPIParser
from jentic.apitools.openapi.traverse.datamodels.low import traverse, DataModelLowVisitor

# Parse OpenAPI document
parser = OpenAPIParser("datamodel-low")
doc = parser.parse("file:///path/to/openapi.yaml")

# Create visitor
class OperationCollector(DataModelLowVisitor):
    def __init__(self):
        self.operations = []

    def visit_Operation(self, path):
        self.operations.append({
            "path": path.format_path(path_format="jsonpointer"),
            "operation_id": path.node.operation_id.value if path.node.operation_id else None
        })

# Traverse
visitor = OperationCollector()
traverse(doc, visitor)

print(f"Found {len(visitor.operations)} operations")
```

### Visitor Pattern

The datamodel traversal uses a flexible visitor pattern with multiple hook types:

#### Hook Methods

**Generic hooks** (fire for ALL nodes):
- `visit_enter(path)` - Called before processing any node
- `visit_leave(path)` - Called after processing any node and its children

**Class-specific hooks** (fire for matching node types):
- `visit_ClassName(path)` - Main visitor for specific node type
- `visit_enter_ClassName(path)` - Called before visit_ClassName
- `visit_leave_ClassName(path)` - Called after children are visited

#### Dispatch Order

For each node, hooks are called in this order:
1. `visit_enter(path)` - generic enter
2. `visit_enter_ClassName(path)` - specific enter
3. `visit_ClassName(path)` - main visitor
4. [child traversal - automatic unless skipped]
5. `visit_leave_ClassName(path)` - specific leave
6. `visit_leave(path)` - generic leave

#### Control Flow

Visitor methods control traversal by their return value:

- `None` (or no return) - **Continue normally** (children visited automatically)
- `False` - **Skip children** of this node (but continue to siblings)
- `BREAK` - **Stop entire traversal** immediately

```python
from jentic.apitools.openapi.traverse.datamodels.low import traverse, BREAK

class ControlFlowExample:
    def visit_PathItem(self, path):
        if path.parent_key == "/internal":
            return False  # Skip internal paths and their children

    def visit_Operation(self, path):
        if some_error_condition:
            return BREAK  # Stop entire traversal
```

### NodePath Context

Every visitor method receives a `NodePath` object with context about the current node:

```python
class PathInspector:
    def visit_Operation(self, path):
        # Current node
        print(f"Node: {path.node.__class__.__name__}")

        # Parent information
        print(f"Parent field: {path.parent_field}")  # e.g., "get", "post"
        print(f"Parent key: {path.parent_key}")      # e.g., "/users" (for path items)

        # Ancestry (computed properties)
        print(f"Parent: {path.parent.__class__.__name__}")
        print(f"Ancestors: {len(path.ancestors)}")
        root = path.get_root()

        # Complete path formatting (RFC 6901 JSONPointer / RFC 9535 JSONPath)
        print(f"JSONPointer: {path.format_path()}")
        # Output: /paths/~1users/get

        print(f"JSONPath: {path.format_path(path_format='jsonpath')}")
        # Output: $['paths']['/users']['get']
```

#### Path Reconstruction

NodePath uses a linked chain structure (`parent_path`) internally to preserve complete path information from root to current node. This enables accurate JSONPointer and JSONPath reconstruction:

```python
class PathFormatter:
    def visit_Response(self, path):
        # Complete paths from root to current node
        pointer = path.format_path()
        # /paths/~1users/get/responses/200

        jsonpath = path.format_path(path_format='jsonpath')
        # $['paths']['/users']['get']['responses']['200']
```

**Special handling for patterned fields:**
- Patterned fields like `Paths.paths` don't duplicate in paths: `/paths/{key}` (not `/paths/paths/{key}`)
- Fixed dict fields like `webhooks`, `callbacks`, `schemas` include their field name: `/webhooks/{key}`, `/components/schemas/{key}`

**Computed properties:**
- `path.parent` - Returns parent node (computed from parent_path chain)
- `path.ancestors` - Returns tuple of ancestor nodes from root to parent (computed on access)

### Enter/Leave Hooks

Use enter/leave hooks for pre/post processing logic:

```python
class DepthTracker(DataModelLowVisitor):
    def __init__(self):
        self.current_depth = 0
        self.max_depth = 0

    def visit_enter(self, path):
        self.current_depth += 1
        self.max_depth = max(self.max_depth, self.current_depth)
        print("  " * self.current_depth + f"Entering {path.node.__class__.__name__}")

    def visit_leave(self, path):
        print("  " * self.current_depth + f"Leaving {path.node.__class__.__name__}")
        self.current_depth -= 1
```

### Examples

#### Collecting All Schemas

```python
class SchemaCollector(DataModelLowVisitor):
    def __init__(self):
        self.schemas = {}

    def visit_Schema(self, path):
        schema_name = path.parent_key if path.parent_field == "schemas" else None
        if schema_name:
            self.schemas[schema_name] = path.node

visitor = SchemaCollector()
traverse(doc, visitor)
print(f"Found {len(visitor.schemas)} schemas")
```

#### Validating Security Requirements

```python
class SecurityValidator(DataModelLowVisitor):
    def __init__(self):
        self.errors = []

    def visit_Operation(self, path):
        if not path.node.security:
            self.errors.append(f"Missing security at {path.format_path()}")

    def visit_SecurityRequirement(self, path):
        # Validate security requirement
        if not path.node.schemes:
            self.errors.append(f"Empty security requirement at {path.format_path()}")

visitor = SecurityValidator()
traverse(doc, visitor)
if visitor.errors:
    for error in visitor.errors:
        print(f"Security error: {error}")
```

#### Finding Deprecated Operations

```python
class DeprecatedFinder:
    def __init__(self):
        self.deprecated_ops = []

    def visit_Operation(self, path):
        if path.node.deprecated and path.node.deprecated.value:
            self.deprecated_ops.append({
                "path": path.format_path(),
                "operation_id": path.node.operation_id.value if path.node.operation_id else None,
                "method": path.parent_field
            })
        return False  # Skip children (we don't need to go deeper)

visitor = DeprecatedFinder()
traverse(doc, visitor)
```

#### Early Exit on Error

```python
class ErrorDetector(DataModelLowVisitor):
    def __init__(self):
        self.error_found = False
        self.error_location = None

    def visit_Operation(self, path):
        if not path.node.responses:
            self.error_found = True
            self.error_location = path.format_path()
            return BREAK  # Stop traversal immediately
```

### Merging Multiple Visitors

Run multiple visitors in a single traversal pass (parallel visitation) using `merge_visitors`:

```python
from jentic.apitools.openapi.traverse.datamodels.low import merge_visitors

# Create separate visitors
schema_collector = SchemaCollector()
security_validator = SecurityValidator()
deprecated_finder = DeprecatedFinder()

# Merge and traverse once
merged = merge_visitors(schema_collector, security_validator, deprecated_finder)
traverse(doc, merged)

# Each visitor maintains independent state
print(f"Schemas: {len(schema_collector.schemas)}")
print(f"Security errors: {len(security_validator.errors)}")
print(f"Deprecated: {len(deprecated_finder.deprecated_ops)}")
```

**Per-Visitor Control Flow:**
- Each visitor can independently skip subtrees or break
- If `visitor1` returns `False`, only `visitor1` skips children
- Other visitors continue normally
- This follows ApiDOM's per-visitor semantics

### Duck Typing

You don't need to inherit from `DataModelLowVisitor` - duck typing works:

```python
class SimpleCounter:  # No inheritance
    def __init__(self):
        self.count = 0

    def visit_Operation(self, path):
        self.count += 1

visitor = SimpleCounter()
traverse(doc, visitor)
```

The `DataModelLowVisitor` base class is optional and provides no functionality - it's purely for organizational purposes.

### API Reference

#### `traverse(root, visitor) -> None`

Traverse OpenAPI datamodel tree using visitor pattern.

**Parameters:**
- `root` - Root datamodel object (OpenAPI30, OpenAPI31, or any datamodel node)
- `visitor` - Object with `visit_*` methods (duck typing)

**Returns:**
- None (traversal is side-effect based)

#### `BREAK`

Sentinel value to stop traversal immediately. Return this from any visitor method.

```python
from jentic.apitools.openapi.traverse.datamodels.low import BREAK

def visit_Operation(self, path):
    if should_stop:
        return BREAK
```

#### `merge_visitors(*visitors) -> object`

Merge multiple visitors into one composite visitor.

**Parameters:**
- `*visitors` - Variable number of visitor objects

**Returns:**
- Composite visitor object with per-visitor state tracking


## JSON Traversal

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