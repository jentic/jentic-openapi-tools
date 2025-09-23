from typing import Dict, List
from lsprotocol import types as lsp


def validate(spec_data: Dict) -> List[lsp.Diagnostic]:
    """
    Validates the 'servers' section of an OpenAPI spec.
    """
    issues = []
    servers = spec_data.get("servers")

    if not isinstance(servers, list) or not servers:
        diag = lsp.Diagnostic(
            range=lsp.Range(
                start=lsp.Position(line=0, character=0),
                end=lsp.Position(line=0, character=0),
            ),
            severity=lsp.DiagnosticSeverity.Error,
            code="MISSING_SERVER_URL",
            source="default_validator",
            message="OpenAPI spec must define at least one server in the 'servers' array.",
        )
        diag.data = {"fixable": True, "path": ["servers"]}
        issues.append(diag)

        return issues

    for index, server in enumerate(servers):
        issues.extend(_validate_single_server(server, index))

    return issues


def _validate_single_server(server: object, index: int) -> List[lsp.Diagnostic]:
    """
    Validates a single server object.
    """
    issues = []
    server_path = f"#/servers/{index}"

    if not isinstance(server, dict):
        diag = lsp.Diagnostic(
            range=lsp.Range(
                start=lsp.Position(line=0, character=0),
                end=lsp.Position(line=0, character=0),
            ),
            severity=lsp.DiagnosticSeverity.Error,
            code="INVALID_SERVER_OBJECT_FORMAT",
            source="default_validator",
            message=f"Server entry at index {index} is not a valid object.",
        )
        diag.data = {"fixable": False, "path": ["servers", {index}]}
        issues.append(diag)
        return issues

    url = server.get("url")

    if not url or not isinstance(url, str):
        diag = lsp.Diagnostic(
            range=lsp.Range(
                start=lsp.Position(line=0, character=0),
                end=lsp.Position(line=0, character=0),
            ),
            severity=lsp.DiagnosticSeverity.Error,
            code="SERVER_URL_MISSING_OR_EMPTY",
            source="default_validator",
            message=f"Server entry at '{server_path}' must have a non-empty 'url' string.",
        )
        diag.data = {"fixable": True, "path": ["servers", {index}, "url"]}
        issues.append(diag)
        return issues

    if not (url.startswith("http://") or url.startswith("https://") or url.startswith("{")):
        diag = lsp.Diagnostic(
            range=lsp.Range(
                start=lsp.Position(line=0, character=0),
                end=lsp.Position(line=0, character=0),
            ),
            severity=lsp.DiagnosticSeverity.Warning,
            code="RELATIVE_SERVER_URL",
            source="default_validator",
            message=f"Server URL '{url}' at index {index} must be an absolute URL (e.g., start with http:// or https://).",
        )
        diag.data = {"fixable": True, "path": ["servers", {index}, "url"]}

    return issues
