"""
OpenAPI Parser exceptions.

This module defines all custom exceptions used by the OpenAPI parser.
"""


class OpenAPIParserError(Exception):
    """Base exception for OpenAPI parser errors."""

    pass


class InvalidStrategyError(OpenAPIParserError):
    """Raised when an invalid strategy is provided."""

    pass


class StrategyNotFoundError(InvalidStrategyError):
    """Raised when a named strategy cannot be found."""

    pass


class ParsingError(OpenAPIParserError):
    """Raised when parsing fails."""

    def __init__(self, message: str, source_error: Exception | None = None):
        super().__init__(message)
        self.source_error = source_error


class DocumentLoadError(OpenAPIParserError):
    """Raised when document loading fails."""

    def __init__(self, message: str, source_error: Exception | None = None):
        super().__init__(message)
        self.source_error = source_error


class TypeConversionError(OpenAPIParserError):
    """Raised when type conversion fails in strict mode."""

    pass
