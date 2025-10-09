from collections.abc import Sequence
from typing import Literal

from lsprotocol import types as lsp
from openapi_spec_validator import validate

from jentic.apitools.openapi.validator.backends.base import BaseValidatorBackend
from jentic.apitools.openapi.validator.core.diagnostics import JenticDiagnostic, ValidationResult


__all__ = ["DefaultValidatorBackend"]


class DefaultValidatorBackend(BaseValidatorBackend):
    def validate(
        self, source: str | dict, *, base_url: str | None = None, target: str | None = None
    ) -> ValidationResult:
        # Use openapi_spec_validator to check spec validity
        try:
            assert isinstance(source, dict)
            validate(source, base_uri=base_url or "")
        except Exception as e:
            msg = str(e)
            diagnostic = JenticDiagnostic(
                range=lsp.Range(
                    start=lsp.Position(line=0, character=0),
                    end=lsp.Position(line=0, character=12),
                ),
                severity=lsp.DiagnosticSeverity.Error,
                code="OAS1001",
                # code_description=lsp.CodeDescription(href="https://example.com/rules/OAS1001"),
                source="openapi_spec_validator",
                message=msg,
            )
            diagnostic.set_target(target)

            return ValidationResult(diagnostics=[diagnostic])
        # If no exception, it's valid
        return ValidationResult(diagnostics=[])

    @staticmethod
    def accepts() -> Sequence[Literal["dict"]]:
        """Return the document formats this validator can accept.

        Returns:
            Sequence of supported document format identifiers:
            - "dict": Python dictionary containing OpenAPI Document data
        """
        return ["dict"]
