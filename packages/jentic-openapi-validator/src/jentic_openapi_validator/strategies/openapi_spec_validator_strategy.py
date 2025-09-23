from lsprotocol.types import Diagnostic

from lsprotocol import types as lsp
from openapi_spec_validator import OpenAPIV30SpecValidator, OpenAPIV31SpecValidator
from jentic_openapi_validator.strategies.base import BaseValidatorStrategy
from jentic_openapi_validator.diagnostics import ValidationResult


class OpenAPISpecValidator(BaseValidatorStrategy):
    def validate(self, document: str | dict) -> ValidationResult:
        # Use openapi_spec_validator to check spec validity
        assert isinstance(document, dict)
        diagnostics: list[Diagnostic] = []
        if self._is_openapi_v31(document):
            validator = OpenAPIV31SpecValidator(document)
        else:
            validator = OpenAPIV30SpecValidator(document)
        errors = list(validator.iter_errors())
        for err in errors:
            try:
                # attrs:
                #        "message", "path", "relative_path", "schema_path", "relative_schema_path",
                #        "context", "cause", "validator", "validator_value",
                #        "instance", "schema", "parent", "_type_checker"

                diag = lsp.Diagnostic(
                    range=lsp.Range(
                        start=lsp.Position(line=0, character=0),
                        end=lsp.Position(line=0, character=0),
                    ),
                    severity=lsp.DiagnosticSeverity.Error,
                    code=str(err.validator_value),
                    source="openapi-spec-validator",
                    message=err.message,
                )
                diag.data = {"fixable": True, "path": list(err.path)}
                diagnostics.append(diag)
            except Exception as e:
                print("Error validating spec:", e)
                msg = str(e)
                diag = lsp.Diagnostic(
                    range=lsp.Range(
                        start=lsp.Position(line=0, character=0),
                        end=lsp.Position(line=0, character=12),
                    ),
                    severity=lsp.DiagnosticSeverity.Error,
                    code="openapi-spec-validator-error",
                    source="openapi-spec-validator",
                    message=msg,
                )
                diagnostics.append(diag)

        return ValidationResult(diagnostics)

    def accepts(self) -> list[str]:
        return ["dict"]

    @staticmethod
    def _is_openapi_v31(document: dict) -> bool:
        return "openapi" in document and document["openapi"].startswith("3.1")
