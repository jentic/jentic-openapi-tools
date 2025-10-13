"""
Security validation rules for OpenAPI specifications.

These rules validate security schemes and their usage throughout the specification.
"""

from typing import Any

from lsprotocol import types as lsp

from . import BaseRule, ValidationIssue


__all__ = ["SecuritySchemeReferenceRule", "UnusedSecuritySchemeRule"]


# HTTP methods defined in OpenAPI 3.x specification
_HTTP_METHODS = {"get", "put", "post", "delete", "options", "head", "patch", "trace"}


class SecuritySchemeReferenceRule(BaseRule):
    """
    Validates that all security scheme references point to defined schemes.

    Checks both global security requirements and operation-level security requirements
    to ensure they only reference schemes defined in components.securitySchemes.
    """

    @property
    def rule_id(self) -> str:
        return "security-scheme-reference"

    @property
    def name(self) -> str:
        return "Security Scheme Reference Validation"

    def validate(self, spec_data: dict[str, Any]) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []

        # Get defined security schemes
        components = spec_data.get("components", {})
        security_schemes = components.get("securitySchemes", {})
        defined_schemes: set[str] = (
            set(security_schemes.keys()) if isinstance(security_schemes, dict) else set()
        )

        # Check global security requirements
        issues.extend(self._check_global_security(spec_data, defined_schemes))

        # Check operation-level security requirements
        issues.extend(self._check_operation_security(spec_data, defined_schemes))

        return issues

    @staticmethod
    def _check_global_security(
        spec_data: dict[str, Any], defined_schemes: set[str]
    ) -> list[ValidationIssue]:
        """Check global security requirements."""
        issues: list[ValidationIssue] = []
        global_security = spec_data.get("security", [])

        if not isinstance(global_security, list):
            return issues

        for sec_req in global_security:
            if not isinstance(sec_req, dict):
                continue

            for scheme in sec_req.keys():
                if scheme not in defined_schemes:
                    issues.append(
                        ValidationIssue(
                            code="UNDEFINED_SECURITY_SCHEME_REFERENCE",
                            message=f"Global security requirement references undefined scheme '{scheme}'.",
                            severity=lsp.DiagnosticSeverity.Error,
                            path=["security"],
                            fixable=False,
                        )
                    )

        return issues

    @staticmethod
    def _check_operation_security(
        spec_data: dict[str, Any], defined_schemes: set[str]
    ) -> list[ValidationIssue]:
        """Check operation-level security requirements."""
        issues: list[ValidationIssue] = []
        paths = spec_data.get("paths", {})

        if not isinstance(paths, dict):
            return issues

        for path_str, path_item in paths.items():
            if not isinstance(path_item, dict):
                continue

            for method, operation in path_item.items():
                if method not in _HTTP_METHODS:
                    continue

                if not isinstance(operation, dict):
                    continue

                op_security = operation.get("security", [])
                if not isinstance(op_security, list):
                    continue

                for sec_req in op_security:
                    if not isinstance(sec_req, dict):
                        continue

                    for scheme in sec_req.keys():
                        if scheme not in defined_schemes:
                            issues.append(
                                ValidationIssue(
                                    code="UNDEFINED_SECURITY_SCHEME_REFERENCE",
                                    message=f"Operation '{method.upper()}' at path '{path_str}' references undefined scheme '{scheme}'.",
                                    severity=lsp.DiagnosticSeverity.Error,
                                    path=[
                                        "paths",
                                        path_str,
                                        method,
                                        "security",
                                    ],
                                    fixable=False,
                                )
                            )

        return issues


class UnusedSecuritySchemeRule(BaseRule):
    """
    Detects security schemes that are defined but never used.

    This is a warning-level rule that helps identify potentially dead code
    in the security scheme definitions.
    """

    @property
    def rule_id(self) -> str:
        return "unused-security-scheme"

    @property
    def name(self) -> str:
        return "Unused Security Scheme Detection"

    def validate(self, spec_data: dict[str, Any]) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []

        # Get defined security schemes
        components = spec_data.get("components", {})
        security_schemes = components.get("securitySchemes", {})
        defined_schemes: set[str] = (
            set(security_schemes.keys()) if isinstance(security_schemes, dict) else set()
        )

        # Collect all referenced schemes
        referenced_schemes: set[str] = set()

        # Check global security
        global_security = spec_data.get("security", [])
        if isinstance(global_security, list):
            for sec_req in global_security:
                if isinstance(sec_req, dict):
                    referenced_schemes.update(sec_req.keys())

        # Check operation-level security
        paths = spec_data.get("paths", {})
        if isinstance(paths, dict):
            for path_item in paths.values():
                if not isinstance(path_item, dict):
                    continue

                for method, operation in path_item.items():
                    if method not in _HTTP_METHODS or not isinstance(operation, dict):
                        continue

                    op_security = operation.get("security", [])
                    if isinstance(op_security, list):
                        for sec_req in op_security:
                            if isinstance(sec_req, dict):
                                referenced_schemes.update(sec_req.keys())

        # Find unused schemes
        unused = defined_schemes - referenced_schemes
        for scheme in unused:
            issues.append(
                ValidationIssue(
                    code="UNUSED_SECURITY_SCHEME_DEFINED",
                    message=f"Security scheme '{scheme}' is defined in components.securitySchemes but not used in any security requirement.",
                    severity=lsp.DiagnosticSeverity.Warning,
                    path=["components", "securitySchemes", scheme],
                    fixable=True,
                )
            )

        return issues
