import textwrap
from collections.abc import Sequence
from typing import Literal

from lsprotocol import types as lsp
from openapi_spec_validator import OpenAPIV30SpecValidator, OpenAPIV31SpecValidator

from jentic.apitools.openapi.validator.backends.base import BaseValidatorBackend
from jentic.apitools.openapi.validator.core.diagnostics import JenticDiagnostic, ValidationResult


__all__ = ["OpenAPISpecValidatorBackend"]


class OpenAPISpecValidatorBackend(BaseValidatorBackend):
    def validate(
        self, document: str | dict, *, base_url: str | None = None, target: str | None = None
    ) -> ValidationResult:
        if not isinstance(document, dict):
            diagnostic = JenticDiagnostic(
                range=lsp.Range(
                    start=lsp.Position(line=0, character=0),
                    end=lsp.Position(line=0, character=12),
                ),
                severity=lsp.DiagnosticSeverity.Error,
                code="OAS1002",
                source="openapi_spec_validator",
                message="OpenAPISpecValidatorBackend only accepts dict format",
            )
            diagnostic.set_target(target)
            return ValidationResult(diagnostics=[diagnostic])

        if self._is_openapi_v31(document):
            validator = OpenAPIV31SpecValidator(document, base_uri=base_url or "")
        elif self._is_openapi_v30(document):
            validator = OpenAPIV30SpecValidator(document, base_uri=base_url or "")
        else:
            diagnostic = JenticDiagnostic(
                range=lsp.Range(
                    start=lsp.Position(line=0, character=0),
                    end=lsp.Position(line=0, character=12),
                ),
                severity=lsp.DiagnosticSeverity.Error,
                code="OAS1000",
                # code_description=lsp.CodeDescription(href="https://example.com/rules/OAS1000"),
                source="openapi_spec_validator",
                message="Document does not appear to be a valid OpenAPI 3.0.x or 3.1.x specification",
            )
            diagnostic.set_target(target)
            return ValidationResult(diagnostics=[diagnostic])

        diagnostics: list[JenticDiagnostic] = []
        try:
            for error in validator.iter_errors():
                diagnostic = JenticDiagnostic(
                    range=lsp.Range(
                        start=lsp.Position(line=0, character=0),
                        end=lsp.Position(line=0, character=0),
                    ),
                    severity=lsp.DiagnosticSeverity.Error,
                    code=f"{error.validator or str(error.validator_value)}",
                    source="openapi-spec-validator",
                    message=error.message,
                )
                diagnostic.set_path(list(error.path))
                diagnostic.set_target(target)
                diagnostics.append(diagnostic)
        except Exception as e:
            error_msg = textwrap.shorten(str(e), width=500, placeholder="...")
            diagnostic = JenticDiagnostic(
                range=lsp.Range(
                    start=lsp.Position(line=0, character=0),
                    end=lsp.Position(line=0, character=12),
                ),
                severity=lsp.DiagnosticSeverity.Error,
                code="openapi-spec-validator-error",
                source="openapi-spec-validator",
                message=f"Error validating spec - {error_msg}",
            )
            diagnostic.set_target(target)
            diagnostics.append(diagnostic)

        return ValidationResult(diagnostics)

    @staticmethod
    def accepts() -> Sequence[Literal["dict"]]:
        """Return the document formats this validator can accept.

        Returns:
            Sequence of supported document format identifiers:
            - "dict": Python dictionary containing OpenAPI Document data
        """
        return ["dict"]

    @staticmethod
    def _is_openapi_v31(document: dict) -> bool:
        if not isinstance(document, dict):
            return False
        openapi_version = document.get("openapi", "")
        return isinstance(openapi_version, str) and openapi_version.startswith("3.1")

    @staticmethod
    def _is_openapi_v30(document: dict) -> bool:
        if not isinstance(document, dict):
            return False
        openapi_version = document.get("openapi", "")
        return isinstance(openapi_version, str) and openapi_version.startswith("3.0")
