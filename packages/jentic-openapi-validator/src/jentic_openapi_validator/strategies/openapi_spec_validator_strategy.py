from typing import Literal
import lsprotocol.types as lsp
from openapi_spec_validator import OpenAPIV30SpecValidator, OpenAPIV31SpecValidator
from .base import BaseValidatorStrategy
from ..diagnostics import ValidationResult, JenticDiagnostic


class OpenAPISpecValidator(BaseValidatorStrategy):
    def validate(
        self, document: str | dict, *, base_url: str | None = None, target: str | None = None
    ) -> ValidationResult:
        # Use openapi_spec_validator to check spec validity
        assert isinstance(document, dict)
        diagnostics: list[JenticDiagnostic] = []
        if self._is_openapi_v31(document):
            validator = OpenAPIV31SpecValidator(document, base_url or "")
        else:
            validator = OpenAPIV30SpecValidator(document, base_url or "")
        try:
            errors = list(validator.iter_errors())
            for err in errors:
                try:
                    # attrs:
                    #        "message", "path", "relative_path", "schema_path", "relative_schema_path",
                    #        "context", "cause", "validator", "validator_value",
                    #        "instance", "schema", "parent", "_type_checker"

                    diag = JenticDiagnostic(
                        range=lsp.Range(
                            start=lsp.Position(line=0, character=0),
                            end=lsp.Position(line=0, character=0),
                        ),
                        severity=lsp.DiagnosticSeverity.Error,
                        code=f"{err.validator or 'str(err.validator_value)'}",
                        source="openapi-spec-validator",
                        message=err.message,
                    )
                    diag.set_path(list(err.path))
                    diag.set_target(target)
                    diagnostics.append(diag)
                except Exception as e:
                    msg = f"Error validating spec for error {err.message} - {str(e)}"
                    print(msg)
                    diag = JenticDiagnostic(
                        range=lsp.Range(
                            start=lsp.Position(line=0, character=0),
                            end=lsp.Position(line=0, character=12),
                        ),
                        severity=lsp.DiagnosticSeverity.Error,
                        code="openapi-spec-validator-error",
                        source="openapi-spec-validator",
                        message=msg,
                    )
                    diag.set_target(target)
                    diagnostics.append(diag)
        except Exception as e:
            msg = f"Error validating spec - {str(e)}"
            print(msg)
            diag = JenticDiagnostic(
                range=lsp.Range(
                    start=lsp.Position(line=0, character=0),
                    end=lsp.Position(line=0, character=12),
                ),
                severity=lsp.DiagnosticSeverity.Error,
                code="openapi-spec-validator-error",
                source="openapi-spec-validator",
                message=msg,
            )
            diag.set_target(target)
            diagnostics.append(diag)

        return ValidationResult(diagnostics)

    @staticmethod
    def accepts() -> list[Literal["uri", "text", "dict"]]:
        return ["dict"]

    @staticmethod
    def _is_openapi_v31(document: dict) -> bool:
        return "openapi" in document and document["openapi"].startswith("3.1")
