"""
OpenAPI Parser exceptions.

This module defines all custom exceptions used by the OpenAPI parser.
"""


class OpenAPIParserError(Exception):
    """Base exception for OpenAPI parser errors."""


class InvalidBackendError(OpenAPIParserError):
    """Raised when an invalid backend is provided."""


class BackendNotFoundError(InvalidBackendError):
    """Raised when a named backend cannot be found."""


class DocumentParseError(OpenAPIParserError):
    """Raised when parsing fails."""


class DocumentLoadError(OpenAPIParserError):
    """Raised when document loading fails."""


class TypeConversionError(OpenAPIParserError):
    """Raised when type conversion fails in strict mode."""
