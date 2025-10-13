"""
Server validation rules for OpenAPI specifications.

These rules validate the 'servers' section and individual server objects.
"""

from typing import Any

from lsprotocol import types as lsp

from . import BaseRule, ValidationIssue


__all__ = ["ServersArrayRule", "ServerUrlRule"]


class ServersArrayRule(BaseRule):
    """
    Validates that the OpenAPI specification contains at least one server.

    The 'servers' array is required and must contain at least one valid server object.
    """

    @property
    def rule_id(self) -> str:
        return "servers-array"

    @property
    def name(self) -> str:
        return "Servers Array Validation"

    def validate(self, spec_data: dict[str, Any]) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []
        servers = spec_data.get("servers")

        if not isinstance(servers, list) or not servers:
            issues.append(
                ValidationIssue(
                    code="MISSING_SERVER_URL",
                    message="OpenAPI spec must define at least one server in the 'servers' array.",
                    severity=lsp.DiagnosticSeverity.Error,
                    path=["servers"],
                    fixable=False,
                )
            )

        return issues


class ServerUrlRule(BaseRule):
    """
    Validates individual server objects and their URLs.

    Each server must:
    - Be a valid object (dict)
    - Have a non-empty 'url' field
    - Use an absolute URL (http://, https://, or template variable)
    """

    @property
    def rule_id(self) -> str:
        return "server-url"

    @property
    def name(self) -> str:
        return "Server URL Validation"

    def validate(self, spec_data: dict[str, Any]) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []
        servers = spec_data.get("servers")

        # Only validate if servers is a list
        if not isinstance(servers, list):
            return issues

        for index, server in enumerate(servers):
            issues.extend(self._validate_single_server(server, index))

        return issues

    @staticmethod
    def _validate_single_server(server: Any, index: int) -> list[ValidationIssue]:
        """
        Validates a single server object.

        Args:
            server: The server object to validate
            index: The index of the server in the servers array

        Returns:
            List of ValidationIssue objects for any problems found
        """
        issues: list[ValidationIssue] = []
        server_path = f"#/servers/{index}"

        # Check if server is a dict
        if not isinstance(server, dict):
            issues.append(
                ValidationIssue(
                    code="INVALID_SERVER_OBJECT_FORMAT",
                    message=f"Server entry at index {index} is not a valid object.",
                    severity=lsp.DiagnosticSeverity.Error,
                    path=["servers", index],
                    fixable=False,
                )
            )
            return issues

        # Check for URL field
        url = server.get("url")

        if not url or not isinstance(url, str):
            issues.append(
                ValidationIssue(
                    code="SERVER_URL_MISSING_OR_EMPTY",
                    message=f"Server entry at '{server_path}' must have a non-empty 'url' string.",
                    severity=lsp.DiagnosticSeverity.Error,
                    path=["servers", index, "url"],
                    fixable=False,
                )
            )
            return issues

        # Check if URL is absolute (or uses template variables)
        if not (url.startswith("http://") or url.startswith("https://") or url.startswith("{")):
            issues.append(
                ValidationIssue(
                    code="RELATIVE_SERVER_URL",
                    message=f"Server URL '{url}' at index {index} must be an absolute URL (e.g., start with http:// or https://).",
                    severity=lsp.DiagnosticSeverity.Warning,
                    path=["servers", index, "url"],
                    fixable=True,
                )
            )

        return issues
