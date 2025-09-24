# jentic-openapi-common

Common utilities for OpenAPI tools packages. This package provides shared functionality using PEP 420 namespace packages as contribution points.

## Installation

```bash
uv add jentic-openapi-common
```

## Modules

### subproc

Subprocess execution utilities with enhanced error handling and cross-platform support.

## Usage Examples

### Basic Command Execution

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