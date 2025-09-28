from typing import Dict, List
from lsprotocol import types as lsp
from ...diagnostics import JenticDiagnostic


def validate(spec_data: Dict, target: str | None = None) -> List[JenticDiagnostic]:
    """
    Validates the basic structure and schema of an OpenAPI specification.

    Args:
        spec_data: The parsed OpenAPI specification as a dictionary.
        file_path: The path to the specification file (for context in messages).

    Returns:
        A list of issue dictionaries.
    """
    issues = []

    info_object = spec_data.get("info")
    if not isinstance(info_object, dict):
        diag = JenticDiagnostic(
            range=lsp.Range(
                start=lsp.Position(line=0, character=0),
                end=lsp.Position(line=0, character=0),
            ),
            severity=lsp.DiagnosticSeverity.Error,
            code="OPENAPI_MISSING_INFO",
            source="default-validator",
            message="OpenAPI spec is missing the required 'info' section or it is not an object.",
        )
        diag.set_target(target)
        diag.set_path(["info"])
        issues.append(diag)
    elif not info_object.get("title") or not info_object.get("version"):
        missing_fields = []
        if not info_object.get("title"):
            missing_fields.append("'title'")
        if not info_object.get("version"):
            missing_fields.append("'version'")

        message = f"The 'info' object is missing required field(s): {', '.join(missing_fields)}."
        if len(info_object.keys()) == 1 and "x-jentic-source-url" in info_object:
            message = "The 'info' object only contains 'x-jentic-source-url' and is missing required fields 'title' and 'version'."

        diag = JenticDiagnostic(
            range=lsp.Range(
                start=lsp.Position(line=0, character=0),
                end=lsp.Position(line=0, character=0),
            ),
            severity=lsp.DiagnosticSeverity.Error,
            code="OPENAPI_MISSING_INFO",
            source="default-validator",
            message=message,
        )
        diag.set_target(target)
        diag.set_path(["info"])
        issues.append(diag)

    if "paths" not in spec_data:
        diag = JenticDiagnostic(
            range=lsp.Range(
                start=lsp.Position(line=0, character=0),
                end=lsp.Position(line=0, character=0),
            ),
            severity=lsp.DiagnosticSeverity.Error,
            code="OPENAPI_MISSING_PATHS",
            source="default-validator",
            message="OpenAPI spec is missing the required 'paths' section.",
        )
        diag.set_target(target)
        diag.set_fixable(False)
        issues.append(diag)
    return issues
