# Jentic OpenAPI Tools

A comprehensive Python toolkit for parsing, validating, and transforming OpenAPI documents with pluggable backend architecture.

[![Discord](https://img.shields.io/badge/JOIN%20OUR%20DISCORD-COMMUNITY-7289DA?style=plastic&logo=discord&logoColor=white)](https://discord.gg/yrxmDZWMqB)
[![Contributor Covenant](https://img.shields.io/badge/Contributor%20Covenant-3.0-40c463.svg)](https://github.com/jentic/jentic-openapi-tools/blob/HEAD/CODE_OF_CONDUCT.md)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://github.com/jentic/jentic-openapi-tools/blob/HEAD/LICENSE)
[![PyPI version](https://badge.fury.io/py/jentic-openapi-tools.svg)](https://badge.fury.io/py/jentic-openapi-tools)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

## Features

- **Pluggable Backend Architecture** - Support for multiple parsing, validation, and transformation strategies via entry points
- **Type Safety** - Full type hints with comprehensive type checking throughout
- **Multiple Input Formats** - Accept OpenAPI documents from file URIs, JSON/YAML strings, or Python dictionaries
- **Flexible Output Types** - Return results as dictionaries, strings, or custom types
- **Extensible Design** - Easy integration of third-party backends through standard Python entry points
- **Path Security** - Built-in defense against path traversal attacks
- **Production Ready** - Comprehensive test coverage and error handling

## Installation

Install all packages at once using the meta-package:

```bash
pip install jentic-openapi-tools
```

Or install individual packages as needed:

```bash
pip install jentic-openapi-parser
pip install jentic-openapi-validator
pip install jentic-openapi-transformer
```

**Prerequisites:**
- Python 3.11 or higher
- Node.js and npm (required for Redocly and Spectral backends)

## Quick Start

### Parsing OpenAPI Documents

```python
from jentic.apitools.openapi.parser.core import OpenAPIParser

# Create parser with default backend
parser = OpenAPIParser()

# Parse from file
doc = parser.parse("file:///path/to/openapi.yaml")
print(doc["info"]["title"])

# Parse from YAML/JSON string
yaml_doc = """
openapi: 3.1.0
info:
  title: My API
  version: 1.0.0
paths: {}
"""
doc = parser.parse(yaml_doc)
```

### Validating OpenAPI Documents

```python
from jentic.apitools.openapi.validator.core import OpenAPIValidator

# Create validator
validator = OpenAPIValidator()

# Validate from file
result = validator.validate("file:///path/to/openapi.yaml")

if result.valid:
    print("Document is valid!")
else:
    for diagnostic in result.diagnostics:
        print(f"Error: {diagnostic.message}")
```

### Transforming OpenAPI Documents

```bash
# Install with Redocly backend support
pip install jentic-openapi-transformer[redocly]
```

```python
from jentic.apitools.openapi.transformer.bundler.core import OpenAPIBundler

# Bundle OpenAPI document with external reference resolution
bundler = OpenAPIBundler("redocly")
result = bundler.bundle("file:///path/to/openapi.yaml", return_type=dict)
print(result["info"]["title"])
```

## Packages

This monorepo contains the following packages:

| Package | Description |
|---------|-------------|
| **[jentic-openapi-tools](https://github.com/jentic/jentic-openapi-tools/tree/HEAD)** | Meta-package that installs all workspace packages |
| **[jentic-openapi-common](https://github.com/jentic/jentic-openapi-tools/tree/HEAD/packages/jentic-openapi-common)** | Common utilities and shared functionality |
| **[jentic-openapi-datamodels](https://github.com/jentic/jentic-openapi-tools/tree/HEAD/packages/jentic-openapi-datamodels)** | OpenAPI data models and structures |
| **[jentic-openapi-parser](https://github.com/jentic/jentic-openapi-tools/tree/HEAD/packages/jentic-openapi-parser)** | OpenAPI document parsing with pluggable backends |
| **[jentic-openapi-traverse](https://github.com/jentic/jentic-openapi-tools/tree/HEAD/packages/jentic-openapi-traverse)** | OpenAPI document traversal utilities |
| **[jentic-openapi-transformer](https://github.com/jentic/jentic-openapi-tools/tree/HEAD/packages/jentic-openapi-transformer)** | OpenAPI document transformation and bundling |
| **[jentic-openapi-transformer-redocly](https://github.com/jentic/jentic-openapi-tools/tree/HEAD/packages/jentic-openapi-transformer-redocly)** | Redocly-based transformation backend |
| **[jentic-openapi-validator](https://github.com/jentic/jentic-openapi-tools/tree/HEAD/packages/jentic-openapi-validator)** | OpenAPI document validation with pluggable backends |
| **[jentic-openapi-validator-redocly](https://github.com/jentic/jentic-openapi-tools/tree/HEAD/packages/jentic-openapi-validator-redocly)** | Redocly-based validation backend |
| **[jentic-openapi-validator-spectral](https://github.com/jentic/jentic-openapi-tools/tree/HEAD/packages/jentic-openapi-validator-spectral)** | Spectral-based validation backend |

Each package has its own detailed README with comprehensive API documentation and examples.

## Documentation

- **[Development Guide](https://github.com/jentic/jentic-openapi-tools/blob/HEAD/DEVELOPMENT.md)** - Setup instructions, testing, and development workflows
- **[Contributing Guidelines](https://github.com/jentic/jentic-openapi-tools/blob/HEAD/CONTRIBUTING.md)** - How to contribute to the project
- **Package READMEs** - See individual package directories for detailed API documentation

## Architecture

The Jentic OpenAPI Tools follow a modular architecture with a plugin-based backend system:

- **Core Packages** - Provide base functionality and abstractions
- **Backend Packages** - Implement specific parsing, validation, or transformation strategies
- **Entry Points** - Backends register themselves via Python entry points for automatic discovery

This design allows you to:
- Start with default backends and add advanced ones as needed
- Implement custom backends for specific requirements
- Use multiple backends simultaneously for comprehensive validation

---

Built and maintained by [Jentic](https://jentic.com)
