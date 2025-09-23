from lsprotocol import types as lsp

from ..base import BaseValidatorStrategy
from ...diagnostics import ValidationResult
from .structural_validator import validate as validate_structural
from .server_validator import validate as validate_servers
from .security_usage_validator import validate as validate_security_usage


class DefaultOpenAPIValidator(BaseValidatorStrategy):
    def validate(self, document: str | dict) -> ValidationResult:
        diagnostics: list[lsp.Diagnostic] = []
        try:
            assert isinstance(document, dict)

            diagnostics.extend(validate_structural(document))
            diagnostics.extend(validate_servers(document))
            diagnostics.extend(validate_security_usage(document))
        except Exception as e:
            msg = str(e)
            diag = lsp.Diagnostic(
                range=lsp.Range(
                    start=lsp.Position(line=0, character=0),
                    end=lsp.Position(line=0, character=12),
                ),
                severity=lsp.DiagnosticSeverity.Error,
                code="default-validator-error",
                source="default-validator",
                message=msg,
            )

            return ValidationResult([diag])
        # If no exception, it's valid
        return ValidationResult(diagnostics)

    def accepts(self) -> list[str]:
        return ["dict"]
