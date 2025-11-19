# jentic-openapi-common

Common utilities for OpenAPI tools packages. This package provides shared functionality using PEP 420 namespace packages as contribution points.

## Installation

```bash
uv add jentic-openapi-common
```

## Modules

### uri

URI/URL/path utilities for working with OpenAPI document references.

**Available functions:**

- `is_uri_like(s: str | None) -> bool` - Check if a string looks like a URI/URL/path
- `is_http_https_url(s: str | None) -> bool` - Check if string is an HTTP(S) URL
- `is_file_uri(s: str | None) -> bool` - Check if string is a file:// URI
- `is_path(s: str | None) -> bool` - Check if string is a filesystem path (not a URL)
- `resolve_to_absolute(uri: str, base_uri: str | None = None) -> str` - Resolve relative URIs to absolute

**Exceptions:**

- `URIResolutionError` - Raised when URI resolution fails

### path_security

Path security utilities for validating and securing filesystem access. Provides defense-in-depth protection against path traversal attacks, directory escapes, and unauthorized file access.

**Available functions:**

- `validate_path(path, *, allowed_base=None, allowed_extensions=None, resolve_symlinks=True, as_string=True) -> str | Path` - Validate and canonicalize a filesystem path with security checks. Returns `str` by default, or `Path` when `as_string=False`

**Exceptions:**

- `PathSecurityError` - Base exception for path security violations
- `PathTraversalError` - Path attempts to escape allowed base directory
- `InvalidExtensionError` - Path has disallowed file extension
- `SymlinkSecurityError` - Path contains symlinks when not allowed or symlink escapes boundary

### subproc

Subprocess execution utilities with enhanced error handling and cross-platform support.

### version_detection

OpenAPI/Swagger version detection utilities. Provides functions to detect and extract version information from OpenAPI documents in text (YAML/JSON) or Mapping formats.

**Available functions:**

- `get_version(document: str | Mapping[str, Any]) -> str | None` - Extract version string from document (e.g., "3.0.4", "2.0")
- `is_openapi_20(document: str | Mapping[str, Any]) -> bool` - Check if document is OpenAPI 2.0 (Swagger 2.0)
- `is_openapi_30(document: str | Mapping[str, Any]) -> bool` - Check if document is OpenAPI 3.0.x
- `is_openapi_31(document: str | Mapping[str, Any]) -> bool` - Check if document is OpenAPI 3.1.x
- `is_openapi_32(document: str | Mapping[str, Any]) -> bool` - Check if document is OpenAPI 3.2.x

**Version Detection Behavior:**

- **Text input**: Validates against regex patterns, only returns/matches valid versions per specification
- **Mapping input**:
  - `get_version()` returns whatever version string is present (for extraction/inspection)
  - `is_openapi_*()` validates against patterns (for version checking)

## Usage Examples

### URI Utilities

```python
from jentic.apitools.openapi.common.uri import (
    is_uri_like,
    is_http_https_url,
    is_file_uri,
    is_path,
    resolve_to_absolute,
    URIResolutionError,
)

# Check URI types
is_uri_like("https://example.com/spec.yaml")  # True
is_http_https_url("https://example.com/spec.yaml")  # True
is_file_uri("file:///home/user/spec.yaml")  # True
is_path("/home/user/spec.yaml")  # True
is_path("https://example.com/spec.yaml")  # False

# Resolve relative URIs
absolute = resolve_to_absolute("../spec.yaml", "/home/user/project/docs/")
# Returns: "/home/user/project/spec.yaml"

absolute = resolve_to_absolute("spec.yaml")  # Resolves against current working directory
```

### Path Security

```python
from pathlib import Path
from jentic.apitools.openapi.common.path_security import (
    validate_path,
    PathSecurityError,
    PathTraversalError,
    InvalidExtensionError,
    SymlinkSecurityError,
)

# Basic validation - converts to absolute path (returns string by default)
safe_path = validate_path("./specs/openapi.yaml")
print(safe_path)  # '/current/working/dir/specs/openapi.yaml'
print(type(safe_path))  # <class 'str'>

# Request Path object with as_string=False
safe_path_obj = validate_path("./specs/openapi.yaml", as_string=False)
print(safe_path_obj)  # Path('/current/working/dir/specs/openapi.yaml')
print(type(safe_path_obj))  # <class 'pathlib.Path'>

# Return type control with as_string parameter
# - as_string=True (default): Returns str - best for subprocess commands
# - as_string=False: Returns Path - best for file operations with pathlib

# Example: Using with subprocess commands (default string return)
import subprocess
doc_path = validate_path("./specs/openapi.yaml")
subprocess.run(["cat", doc_path])  # Works directly, no str() conversion needed

# Example: Using with pathlib operations (Path return)
from pathlib import Path
doc_path = validate_path("./specs/openapi.yaml", as_string=False)
if doc_path.exists():
    content = doc_path.read_text()  # Path methods available

# Boundary enforcement - restrict access to specific directory
try:
    safe_path = validate_path(
        "/var/app/data/spec.yaml",
        allowed_base="/var/app",
    )
    print(f"Access granted: {safe_path}")
except PathTraversalError as e:
    print(f"Access denied: {e}")

# Block directory traversal attacks
try:
    safe_path = validate_path(
        "/var/app/../../../etc/passwd",
        allowed_base="/var/app",
    )
except PathTraversalError:
    print("Path traversal attack blocked!")

# Extension validation - whitelist approach
try:
    safe_path = validate_path(
        "spec.yaml",
        allowed_extensions=(".yaml", ".yml", ".json"),
    )
    print(f"Valid extension: {safe_path}")
except InvalidExtensionError:
    print("Invalid file extension")

# Combined security checks (recommended for web services)
try:
    safe_path = validate_path(
        user_provided_path,
        allowed_base="/var/app/uploads",
        allowed_extensions=(".yaml", ".yml", ".json"),
        resolve_symlinks=True,  # Default: resolve and check symlinks
    )
    # Safe to use safe_path for file operations
    with open(safe_path) as f:
        content = f.read()
except PathSecurityError as e:
    print(f"Security validation failed: {e}")
```

### Subprocess Execution

#### Basic Command Execution

```python
from jentic.apitools.openapi.common.subproc import run_subprocess

# Simple command
result = run_subprocess(["echo", "hello"])
print(result.stdout)  # "hello\n"
print(result.returncode)  # 0

# Command with working directory
result = run_subprocess(["pwd"], cwd="/tmp")
print(result.stdout.strip())  # "/tmp"
```

### Error Handling

```python
from jentic.apitools.openapi.common.subproc import (
    run_subprocess,
    SubprocessExecutionError
)

# Handle errors manually
result = run_subprocess(["false"])  # Command that exits with code 1
if result.returncode != 0:
    print(f"Command failed with code {result.returncode}")

# Automatic error handling
try:
    result = run_subprocess(["false"], fail_on_error=True)
except SubprocessExecutionError as e:
    print(f"Command {e.cmd} failed: {e}")
```

### Advanced Usage

```python
from jentic.apitools.openapi.common.subproc import (
    run_subprocess,
    SubprocessExecutionError
)

# Timeout handling
try:
    result = run_subprocess(["sleep", "10"], timeout=1)
except SubprocessExecutionError as e:
    print("Command timed out")

# Custom encoding
result = run_subprocess(["python", "-c", "print('ñ')"], encoding="utf-8")
print(result.stdout)  # "ñ\n"
```

### Version Detection

```python
from jentic.apitools.openapi.common.version_detection import (
    get_version,
    is_openapi_20,
    is_openapi_30,
    is_openapi_31,
    is_openapi_32,
)

# Extract version from text (YAML/JSON)
yaml_doc = """
openapi: 3.0.4
info:
  title: Pet Store API
  version: 1.0.0
"""
version = get_version(yaml_doc)
print(version)  # "3.0.4"

json_doc = '{"openapi": "3.1.2", "info": {"title": "API", "version": "1.0.0"}}'
version = get_version(json_doc)
print(version)  # "3.1.2"

# Extract version from Mapping (returns any version string, even if unsupported)
doc = {"openapi": "3.0.4"}
version = get_version(doc)
print(version)  # "3.0.4"

# Even unsupported versions are returned from Mapping
doc = {"openapi": "3.0.4-rc1"}
version = get_version(doc)
print(version)  # "3.0.4-rc1" (suffix returned as-is)

# But text input validates with regex
version = get_version("openapi: 3.0.4-rc1")
print(version)  # None (suffix doesn't match pattern)

# Version checking with predicates (validates for both text and Mapping)
doc_20 = {"swagger": "2.0"}
print(is_openapi_20(doc_20))  # True
print(is_openapi_30(doc_20))  # False

doc_30 = {"openapi": "3.0.4"}
print(is_openapi_30(doc_30))  # True
print(is_openapi_31(doc_30))  # False

doc_31 = {"openapi": "3.1.2"}
print(is_openapi_31(doc_31))  # True
print(is_openapi_32(doc_31))  # False

doc_32 = {"openapi": "3.2.0"}
print(is_openapi_32(doc_32))  # True

# Predicates validate strictly
doc_suffix = {"openapi": "3.0.4-rc1"}
print(is_openapi_30(doc_suffix))  # False (suffix rejected)

doc_unsupported = {"openapi": "3.3.0"}
print(is_openapi_32(doc_unsupported))  # False (unsupported version)

# Works with YAML text too
yaml_text = "openapi: 3.0.4\ninfo:\n  title: API"
print(is_openapi_30(yaml_text))  # True

# Works with JSON text
json_text = '{"openapi": "3.1.2"}'
print(is_openapi_31(json_text))  # True
```

## Testing

Run the test suite:

```bash
uv run --package jentic-openapi-common pytest packages/jentic-openapi-common -v
```
