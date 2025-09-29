"""
OpenAPI Parser exceptions.

This module defines all custom exceptions used by the OpenAPI parser.
"""


class OpenAPIParserError(Exception):
    """Base exception for OpenAPI parser errors."""


class InvalidStrategyError(OpenAPIParserError):
    """Raised when an invalid strategy is provided."""


class StrategyNotFoundError(InvalidStrategyError):
    """Raised when a named strategy cannot be found."""


class DocumentParseError(OpenAPIParserError):
    """Raised when parsing fails."""


class DocumentLoadError(OpenAPIParserError):
    """Raised when document loading fails."""


class TypeConversionError(OpenAPIParserError):
    """Raised when type conversion fails in strict mode."""
