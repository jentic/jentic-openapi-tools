from typing import Literal

from lsprotocol import types as lsp

from ..base import BaseValidatorStrategy
from ...diagnostics import ValidationResult, JenticDiagnostic
from .structural_validator import validate as validate_structural
from .server_validator import validate as validate_servers
from .security_usage_validator import validate as validate_security_usage


class DefaultOpenAPIValidator(BaseValidatorStrategy):
    def validate(
        self, document: str | dict, *, base_url: str | None = None, target: str | None = None
    ) -> ValidationResult:
        diagnostics: list[JenticDiagnostic] = []
        try:
            assert isinstance(document, dict)

            diagnostics.extend(validate_structural(document, target))
            diagnostics.extend(validate_servers(document, target))
            diagnostics.extend(validate_security_usage(document, target))
        except Exception as e:
            msg = str(e)
            diag = JenticDiagnostic(
                range=lsp.Range(
                    start=lsp.Position(line=0, character=0),
                    end=lsp.Position(line=0, character=12),
                ),
                severity=lsp.DiagnosticSeverity.Error,
                code="default-validator-error",
                source="default-validator",
                message=msg,
            )
            diag.set_target(target)

            return ValidationResult([diag])
        # If no exception, it's valid
        return ValidationResult(diagnostics)

    @staticmethod
    def accepts() -> list[Literal["uri", "text", "dict"]]:
        return ["dict"]
