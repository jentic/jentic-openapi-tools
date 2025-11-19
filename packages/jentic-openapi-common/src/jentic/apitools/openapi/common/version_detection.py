"""OpenAPI version detection utilities.

This module provides functions to detect OpenAPI specification versions
from both text (YAML/JSON strings) and Mapping objects.
"""

import re
from collections.abc import Mapping
from typing import Any


__all__ = [
    "get_version",
    "is_openapi_20",
    "is_openapi_30",
    "is_openapi_31",
    "is_openapi_32",
]


# Regex patterns for detecting OpenAPI versions in text
# Matches both YAML and JSON formats
# YAML: swagger: 2.0 (with optional quotes)
# JSON: "swagger": "2.0"
_OPENAPI_20_PATTERN = re.compile(
    r'(?P<YAML>^(["\']?)swagger\2\s*:\s*(["\']?)(?P<version_yaml>2\.0)\3(?:\s+|$))'
    r'|(?P<JSON>"swagger"\s*:\s*"(?P<version_json>2\.0)")',
    re.MULTILINE,
)

# YAML: openapi: 3.0.x (with optional quotes)
# JSON: "openapi": "3.0.x"
_OPENAPI_30_PATTERN = re.compile(
    r'(?P<YAML>^(["\']?)openapi\2\s*:\s*(["\']?)(?P<version_yaml>3\.0\.(?:[1-9]\d*|0))\3(?:\s+|$))'
    r'|(?P<JSON>"openapi"\s*:\s*"(?P<version_json>3\.0\.(?:[1-9]\d*|0))")',
    re.MULTILINE,
)

_OPENAPI_31_PATTERN = re.compile(
    r'(?P<YAML>^(["\']?)openapi\2\s*:\s*(["\']?)(?P<version_yaml>3\.1\.(?:[1-9]\d*|0))\3(?:\s+|$))'
    r'|(?P<JSON>"openapi"\s*:\s*"(?P<version_json>3\.1\.(?:[1-9]\d*|0))")',
    re.MULTILINE,
)

_OPENAPI_32_PATTERN = re.compile(
    r'(?P<YAML>^(["\']?)openapi\2\s*:\s*(["\']?)(?P<version_yaml>3\.2\.(?:[1-9]\d*|0))\3(?:\s+|$))'
    r'|(?P<JSON>"openapi"\s*:\s*"(?P<version_json>3\.2\.(?:[1-9]\d*|0))")',
    re.MULTILINE,
)

# All patterns to try for version extraction
_ALL_PATTERNS = [
    _OPENAPI_20_PATTERN,
    _OPENAPI_30_PATTERN,
    _OPENAPI_31_PATTERN,
    _OPENAPI_32_PATTERN,
]


def get_version(document: str | Mapping[str, Any]) -> str | None:
    """Extract the OpenAPI/Swagger version from a document.

    Args:
        document: Either a text string (YAML/JSON) or a Mapping object

    Returns:
        The version string if found, None otherwise

    Examples:
        >>> get_version("swagger: 2.0\\ninfo:\\n  title: API")
        '2.0'
        >>> get_version("openapi: 3.0.4\\ninfo:\\n  title: API")
        '3.0.4'
        >>> get_version('{"openapi": "3.1.2"}')
        '3.1.2'
        >>> get_version({"openapi": "3.2.0"})
        '3.2.0'
        >>> get_version({"swagger": "2.0"})
        '2.0'
        >>> get_version("no version here")
        None
    """
    if isinstance(document, str):
        # Try all patterns and extract version from named groups
        for pattern in _ALL_PATTERNS:
            match = pattern.search(document)
            if match:
                # Try to get version from either YAML or JSON group
                version = (
                    match.group("version_yaml")
                    if match.group("version_yaml")
                    else match.group("version_json")
                )
                return version
        return None
    elif isinstance(document, Mapping):
        # Return whatever version string is present, without validation
        # Validation can be done separately with is_openapi_*() predicates
        version = document.get("openapi") or document.get("swagger")
        if isinstance(version, str):
            return version
        return None
    return None


def is_openapi_20(document: str | Mapping[str, Any]) -> bool:
    """Check if document is OpenAPI 2.0 (Swagger 2.0) specification.

    Args:
        document: Either a text string (YAML/JSON) or a Mapping object

    Returns:
        True if document is OpenAPI 2.0, False otherwise

    Examples:
        >>> is_openapi_20("swagger: 2.0\\ninfo:\\n  title: API")
        True
        >>> is_openapi_20('{"swagger": "2.0"}')
        True
        >>> is_openapi_20({"swagger": "2.0"})
        True
        >>> is_openapi_20({"openapi": "3.0.4"})
        False
    """
    if isinstance(document, str):
        return bool(_OPENAPI_20_PATTERN.search(document))
    elif isinstance(document, Mapping):
        version = document.get("swagger")
        if isinstance(version, str):
            # Construct YAML-like string and reuse text pattern
            test_string = f"swagger: {version}"
            return bool(_OPENAPI_20_PATTERN.search(test_string))
    return False


def is_openapi_30(document: str | Mapping[str, Any]) -> bool:
    """Check if document is OpenAPI 3.0.x specification.

    Args:
        document: Either a text string (YAML/JSON) or a Mapping object

    Returns:
        True if document is OpenAPI 3.0.x, False otherwise

    Examples:
        >>> is_openapi_30("openapi: 3.0.4\\ninfo:\\n  title: API")
        True
        >>> is_openapi_30('{"openapi": "3.0.4"}')
        True
        >>> is_openapi_30({"openapi": "3.0.4"})
        True
        >>> is_openapi_30({"openapi": "3.1.0"})
        False
    """
    if isinstance(document, str):
        return bool(_OPENAPI_30_PATTERN.search(document))
    elif isinstance(document, Mapping):
        version = document.get("openapi")
        if isinstance(version, str):
            # Construct YAML-like string and reuse text pattern
            test_string = f"openapi: {version}"
            return bool(_OPENAPI_30_PATTERN.search(test_string))
    return False


def is_openapi_31(document: str | Mapping[str, Any]) -> bool:
    """Check if document is OpenAPI 3.1.x specification.

    Args:
        document: Either a text string (YAML/JSON) or a Mapping object

    Returns:
        True if document is OpenAPI 3.1.x, False otherwise

    Examples:
        >>> is_openapi_31("openapi: 3.1.2\\ninfo:\\n  title: API")
        True
        >>> is_openapi_31('{"openapi": "3.1.2"}')
        True
        >>> is_openapi_31({"openapi": "3.1.2"})
        True
        >>> is_openapi_31({"openapi": "3.0.4"})
        False
    """
    if isinstance(document, str):
        return bool(_OPENAPI_31_PATTERN.search(document))
    elif isinstance(document, Mapping):
        version = document.get("openapi")
        if isinstance(version, str):
            # Construct YAML-like string and reuse text pattern
            test_string = f"openapi: {version}"
            return bool(_OPENAPI_31_PATTERN.search(test_string))
    return False


def is_openapi_32(document: str | Mapping[str, Any]) -> bool:
    """Check if document is OpenAPI 3.2.x specification.

    Args:
        document: Either a text string (YAML/JSON) or a Mapping object

    Returns:
        True if document is OpenAPI 3.2.x, False otherwise

    Examples:
        >>> is_openapi_32("openapi: 3.2.0\\ninfo:\\n  title: API")
        True
        >>> is_openapi_32('{"openapi": "3.2.0"}')
        True
        >>> is_openapi_32({"openapi": "3.2.0"})
        True
        >>> is_openapi_32({"openapi": "3.1.0"})
        False
    """
    if isinstance(document, str):
        return bool(_OPENAPI_32_PATTERN.search(document))
    elif isinstance(document, Mapping):
        version = document.get("openapi")
        if isinstance(version, str):
            # Construct YAML-like string and reuse text pattern
            test_string = f"openapi: {version}"
            return bool(_OPENAPI_32_PATTERN.search(test_string))
    return False
