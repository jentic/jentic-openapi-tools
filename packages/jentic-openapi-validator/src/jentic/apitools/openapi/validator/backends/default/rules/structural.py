"""
Structural validation rules for OpenAPI specifications.

These rules validate the basic structure and required fields of an OpenAPI document.
"""

from typing import Any

from lsprotocol import types as lsp

from . import BaseRule, ValidationIssue


__all__ = ["InfoObjectRule", "PathsRule"]


class InfoObjectRule(BaseRule):
    """
    Validates the 'info' object in an OpenAPI specification.

    The 'info' object is required and must contain 'title' and 'version' fields.
    """

    @property
    def rule_id(self) -> str:
        return "info-object"

    @property
    def name(self) -> str:
        return "Info Object Validation"

    def validate(self, spec_data: dict[str, Any]) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []

        info_object = spec_data.get("info")

        # Check if info object exists and is a dict
        if not isinstance(info_object, dict):
            issues.append(
                ValidationIssue(
                    code="OPENAPI_MISSING_INFO",
                    message="OpenAPI spec is missing the required 'info' section or it is not an object.",
                    severity=lsp.DiagnosticSeverity.Error,
                    path=["info"],
                    fixable=False,
                )
            )
            return issues

        # Check for required fields: title and version
        missing_fields = []
        if not info_object.get("title"):
            missing_fields.append("'title'")
        if not info_object.get("version"):
            missing_fields.append("'version'")

        if missing_fields:
            # Special case: if only x-jentic-source-url is present
            if len(info_object.keys()) == 1 and "x-jentic-source-url" in info_object:
                message = "The 'info' object only contains 'x-jentic-source-url' and is missing required fields 'title' and 'version'."
            else:
                message = (
                    f"The 'info' object is missing required field(s): {', '.join(missing_fields)}."
                )

            issues.append(
                ValidationIssue(
                    code="OPENAPI_MISSING_INFO_FIELDS",
                    message=message,
                    severity=lsp.DiagnosticSeverity.Error,
                    path=["info"],
                    fixable=False,
                )
            )

        return issues


class PathsRule(BaseRule):
    """
    Validates that the OpenAPI specification contains a 'paths' section.

    The 'paths' section is required in OpenAPI 3.x specifications and should
    contain at least one path definition.
    """

    @property
    def rule_id(self) -> str:
        return "paths-section"

    @property
    def name(self) -> str:
        return "Paths Section Validation"

    def validate(self, spec_data: dict[str, Any]) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []

        if "paths" not in spec_data:
            issues.append(
                ValidationIssue(
                    code="OPENAPI_MISSING_PATHS",
                    message="OpenAPI spec is missing the required 'paths' section.",
                    severity=lsp.DiagnosticSeverity.Error,
                    path=["paths"],
                    fixable=False,
                )
            )

        return issues
