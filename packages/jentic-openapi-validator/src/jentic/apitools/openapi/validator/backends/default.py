from lsprotocol import types as lsp
from openapi_spec_validator import validate
from jentic.apitools.openapi.validator.backends.base import BaseValidatorBackend
from jentic.apitools.openapi.validator.core.diagnostics import ValidationResult


__all__ = ["DefaultValidatorBackend"]


class DefaultValidatorBackend(BaseValidatorBackend):
    def validate(self, document: str | dict) -> ValidationResult:
        # Use openapi_spec_validator to check spec validity
        try:
            assert isinstance(document, dict)
            validate(document)  # TODO use base url..
        except Exception as e:
            msg = str(e)
            diag = lsp.Diagnostic(
                range=lsp.Range(
                    start=lsp.Position(line=0, character=0),
                    end=lsp.Position(line=0, character=12),
                ),
                severity=lsp.DiagnosticSeverity.Error,
                code="OAS1001",
                # code_description=lsp.CodeDescription(href="https://example.com/rules/OAS1001"),
                source="openapi_spec_validator",
                message=msg,
            )  # ,tags=[lsp.DiagnosticTag.Unnecessary])

            return ValidationResult([diag])
        # If no exception, it's valid
        return ValidationResult([])

    def accepts(self) -> list[str]:
        return ["dict"]
