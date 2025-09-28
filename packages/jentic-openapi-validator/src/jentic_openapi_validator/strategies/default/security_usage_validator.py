from typing import Dict, List, Set
from lsprotocol import types as lsp

from ...paths import escape_token
from ...diagnostics import JenticDiagnostic


def validate(spec_data: Dict, target: str | None = None) -> List[JenticDiagnostic]:
    issues: List[JenticDiagnostic] = []
    components = spec_data.get("components", {})
    security_schemes = components.get("securitySchemes", {})
    defined_schemes: Set[str] = (
        set(security_schemes.keys()) if isinstance(security_schemes, dict) else set()
    )
    # --- Collect all referenced schemes ---
    referenced_schemes: Set[str] = set()
    # Check global security
    global_security = spec_data.get("security_validators", [])
    if isinstance(global_security, list):
        for sec_req in global_security:
            if isinstance(sec_req, dict):
                referenced_schemes.update(sec_req.keys())
                for scheme in sec_req.keys():
                    if scheme not in defined_schemes:
                        diag = JenticDiagnostic(
                            range=lsp.Range(
                                start=lsp.Position(line=0, character=0),
                                end=lsp.Position(line=0, character=0),
                            ),
                            severity=lsp.DiagnosticSeverity.Error,
                            code="UNDEFINED_SECURITY_SCHEME_REFERENCE",
                            source="default-validator",
                            message=f"Global security requirement references undefined scheme '{scheme}'.",
                        )
                        diag.set_target(target)
                        diag.set_path(["security"])
                        issues.append(diag)

    # Check operation-level security
    paths = spec_data.get("paths", {})
    if isinstance(paths, dict):
        for path_str, path_item in paths.items():
            if not isinstance(path_item, dict):
                continue
            for method, op in path_item.items():
                if method not in {
                    "get",
                    "put",
                    "post",
                    "delete",
                    "options",
                    "head",
                    "patch",
                    "trace",
                }:
                    continue
                op_security = op.get("security", [])
                if isinstance(op_security, list):
                    for sec_req in op_security:
                        if isinstance(sec_req, dict):
                            referenced_schemes.update(sec_req.keys())
                            for scheme in sec_req.keys():
                                if scheme not in defined_schemes:
                                    diag = JenticDiagnostic(
                                        range=lsp.Range(
                                            start=lsp.Position(line=0, character=0),
                                            end=lsp.Position(line=0, character=0),
                                        ),
                                        severity=lsp.DiagnosticSeverity.Error,
                                        code="UNDEFINED_SECURITY_SCHEME_REFERENCE",
                                        source="default-validator",
                                        message=f"Operation '{method.upper()}' at path '{path_str}' references undefined scheme '{scheme}'.",
                                    )
                                    diag.set_target(target)
                                    diag.set_path(
                                        [
                                            "paths",
                                            escape_token(path_str),
                                            escape_token(method),
                                            "security",
                                        ]
                                    )
                                    issues.append(diag)
    # Unused scheme detection
    unused = defined_schemes - referenced_schemes
    for scheme in unused:
        diag = JenticDiagnostic(
            range=lsp.Range(
                start=lsp.Position(line=0, character=0),
                end=lsp.Position(line=0, character=0),
            ),
            severity=lsp.DiagnosticSeverity.Warning,
            code="UNUSED_SECURITY_SCHEME_DEFINED",
            source="default-validator",
            message=f"Security scheme '{scheme}' is defined in components.securitySchemes but not used in any security requirement.",
        )
        diag.set_target(target)
        diag.set_path(["components", "securitySchemes"])
        issues.append(diag)
    return issues
