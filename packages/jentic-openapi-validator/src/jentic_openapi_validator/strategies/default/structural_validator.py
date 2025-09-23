from typing import Dict, List
from lsprotocol import types as lsp


def validate(spec_data: Dict) -> List[lsp.Diagnostic]:
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
        diag = lsp.Diagnostic(
            range=lsp.Range(
                start=lsp.Position(line=0, character=0),
                end=lsp.Position(line=0, character=0),
            ),
            severity=lsp.DiagnosticSeverity.Error,
            code="OPENAPI_MISSING_INFO",
            source="default_validator",
            message="OpenAPI spec is missing the required 'info' section or it is not an object.",
        )
        diag.data = {"fixable": True, "path": ["info"]}
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

        diag = lsp.Diagnostic(
            range=lsp.Range(
                start=lsp.Position(line=0, character=0),
                end=lsp.Position(line=0, character=0),
            ),
            severity=lsp.DiagnosticSeverity.Error,
            code="OPENAPI_MISSING_INFO",
            source="default_validator",
            message=message,
        )
        diag.data = {"fixable": True, "path": ["info"]}
        issues.append(diag)

    if "paths" not in spec_data:
        diag = lsp.Diagnostic(
            range=lsp.Range(
                start=lsp.Position(line=0, character=0),
                end=lsp.Position(line=0, character=0),
            ),
            severity=lsp.DiagnosticSeverity.Error,
            code="OPENAPI_MISSING_PATHS",
            source="default_validator",
            message="OpenAPI spec is missing the required 'paths' section.",
        )
        diag.data = {"fixable": False, "path": []}
        issues.append(diag)
    return issues
