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

### subproc

Subprocess execution utilities with enhanced error handling and cross-platform support.

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