"""
Default OpenAPI validator backend with rule-based validation system.

This backend provides a collection of validation rules for common OpenAPI
specification issues including structural validation, server validation,
and security validation.
"""

from typing import Literal

from lsprotocol import types as lsp

from jentic.apitools.openapi.parser.core import OpenAPIParser
from jentic.apitools.openapi.parser.core.exceptions import DocumentLoadError, DocumentParseError

from ...core.diagnostics import JenticDiagnostic, ValidationResult
from ..base import BaseValidatorBackend
from .rules import RuleRegistry
from .rules.security import SecuritySchemeReferenceRule, UnusedSecuritySchemeRule
from .rules.server import ServerUrlRule
from .rules.structural import InfoObjectRule, PathsRule


__all__ = ["DefaultOpenAPIValidatorBackend"]


class DefaultOpenAPIValidatorBackend(BaseValidatorBackend):
    """
    Default OpenAPI validator backend using a rule-based validation system.

    This validator applies a set of predefined rules to check for common
    issues in OpenAPI specifications. Rules cover:
    - Structural validation (info, paths)
    - Server validation (servers array, URLs)
    - Security validation (scheme references, unused schemes)

    The validator can be customized by providing a custom RuleRegistry
    with different rules.
    """

    def __init__(
        self, rule_registry: RuleRegistry | None = None, parser: OpenAPIParser | None = None
    ):
        """
        Initialize the default OpenAPI validator.

        Args:
            rule_registry: Optional custom rule registry. If None, uses default rules.
            parser: Optional OpenAPIParser instance. If None, creates a default parser.
        """
        if rule_registry is None:
            rule_registry = self._create_default_registry()
        self.registry = rule_registry
        self.parser = parser if parser else OpenAPIParser()

    def validate(
        self, document: str | dict, *, base_url: str | None = None, target: str | None = None
    ) -> ValidationResult:
        """
        Validate an OpenAPI document using the registered rules.

        Args:
            document: Path to the OpenAPI document file to validate, or dict containing the document
            base_url: Optional base URL for resolving references
            target: Optional target identifier for validation context

        Returns:
            ValidationResult containing diagnostics for all rule violations

        Raises:
            TypeError: If document type is not supported
        """
        if isinstance(document, str):
            return self._validate_uri(document, base_url=base_url, target=target)
        elif isinstance(document, dict):
            return self._validate_dict(document, base_url=base_url, target=target)
        else:
            raise TypeError(f"Unsupported document type: {type(document)!r}")

    @staticmethod
    def accepts() -> list[Literal["uri", "dict"]]:
        """
        Return the document formats this validator accepts.

        Returns:
            Sequence of supported document format identifiers:
            - "uri": File path or URI pointing to OpenAPI Document
            - "dict": Python dictionary containing OpenAPI Document data
        """
        return ["uri", "dict"]

    def _validate_uri(
        self, document: str, *, base_url: str | None = None, target: str | None = None
    ) -> ValidationResult:
        """
        Validate an OpenAPI document from a URI or file path.

        Args:
            document: Path to the OpenAPI document file or URI
            base_url: Optional base URL for resolving references
            target: Optional target identifier for validation context

        Returns:
            ValidationResult containing diagnostics for all rule violations
        """
        try:
            # Check if parser backend supports URI directly
            if "uri" in self.parser.backend.accepts():
                # Let parser handle URI loading
                document_dict = self.parser.parse(document)
            else:
                # Manually load URI and parse the text
                document_text = self.parser.load_uri(document)
                document_dict = self.parser.parse(document_text)

            # Validate the parsed document
            return self._validate_dict(document_dict, base_url=base_url, target=target)

        except (DocumentParseError, DocumentLoadError) as e:
            # Handle document parsing/loading errors
            diagnostic = JenticDiagnostic(
                range=lsp.Range(
                    start=lsp.Position(line=0, character=0),
                    end=lsp.Position(line=0, character=12),
                ),
                severity=lsp.DiagnosticSeverity.Error,
                code="document-parse-error",
                source="default-validator",
                message=f"Failed to parse document: {str(e)}",
            )
            diagnostic.set_target(target)
            return ValidationResult(diagnostics=[diagnostic])
        except Exception as e:
            # Handle any other unexpected errors
            diagnostic = JenticDiagnostic(
                range=lsp.Range(
                    start=lsp.Position(line=0, character=0),
                    end=lsp.Position(line=0, character=12),
                ),
                severity=lsp.DiagnosticSeverity.Error,
                code="default-validator-error",
                source="default-validator",
                message=f"Unexpected error: {str(e)}",
            )
            diagnostic.set_target(target)
            return ValidationResult(diagnostics=[diagnostic])

    def _validate_dict(
        self, document: dict, *, base_url: str | None = None, target: str | None = None
    ) -> ValidationResult:
        """
        Validate an OpenAPI document from a dictionary.

        Args:
            document: The OpenAPI document as a dictionary
            base_url: Optional base URL for resolving references (not used)
            target: Optional target identifier for validation context

        Returns:
            ValidationResult containing diagnostics for all rule violations
        """
        try:
            # Run all rules through the registry
            diagnostics = self.registry.validate(document, target=target)
            return ValidationResult(diagnostics=diagnostics)

        except Exception as e:
            # Catch any unexpected errors during validation
            msg = str(e)
            diagnostic = JenticDiagnostic(
                range=lsp.Range(
                    start=lsp.Position(line=0, character=0),
                    end=lsp.Position(line=0, character=12),
                ),
                severity=lsp.DiagnosticSeverity.Error,
                code="default-validator-error",
                source="default-validator",
                message=msg,
            )
            diagnostic.set_target(target)
            return ValidationResult(diagnostics=[diagnostic])

    @staticmethod
    def _create_default_registry() -> RuleRegistry:
        """
        Create the default rule registry with all standard rules.

        Returns:
            A RuleRegistry with all default validation rules registered
        """
        registry = RuleRegistry(source="default-validator")

        # Register structural rules
        registry.register(InfoObjectRule())
        registry.register(PathsRule())

        # Register server rules (only validate format if servers exist)
        registry.register(ServerUrlRule())

        # Register security rules
        registry.register(SecuritySchemeReferenceRule())
        registry.register(UnusedSecuritySchemeRule())

        return registry
