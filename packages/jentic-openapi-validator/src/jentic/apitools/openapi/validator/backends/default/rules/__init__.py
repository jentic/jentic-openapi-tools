"""
Validation rules system for the default OpenAPI validator backend.

This module provides the infrastructure for defining and executing validation rules
on OpenAPI specifications. Rules are modular, testable, and composable.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from lsprotocol import types as lsp

from ....core.diagnostics import JenticDiagnostic


__all__ = ["BaseRule", "RuleRegistry", "ValidationIssue"]


@dataclass
class ValidationIssue:
    """
    Represents a validation issue found by a rule.

    This is a lightweight data structure that captures the essential information
    about a validation problem. It will be converted to a JenticDiagnostic
    by the rule registry.

    Attributes:
        code: Error code (e.g., "MISSING_SERVER_URL")
        message: Human-readable error message
        severity: Diagnostic severity level
        path: JSON path to the problematic element (e.g., ["servers", 0, "url"])
        fixable: Whether this issue can be automatically fixed
    """

    code: str
    message: str
    severity: lsp.DiagnosticSeverity = lsp.DiagnosticSeverity.Error
    path: list[str | int] = field(default_factory=list)
    fixable: bool = True

    def to_diagnostic(self, source: str, target: str | None = None) -> JenticDiagnostic:
        """
        Convert this ValidationIssue to a JenticDiagnostic.

        Args:
            source: Source identifier for the diagnostic (e.g., "default-validator")
            target: Optional target identifier for validation context

        Returns:
            A JenticDiagnostic instance ready to be returned to the user
        """
        diagnostic = JenticDiagnostic(
            range=lsp.Range(
                start=lsp.Position(line=0, character=0),
                end=lsp.Position(line=0, character=0),
            ),
            severity=self.severity,
            code=self.code,
            source=source,
            message=self.message,
        )
        diagnostic.set_path(self.path)
        diagnostic.set_target(target)
        diagnostic.set_fixable(self.fixable)
        return diagnostic


class BaseRule(ABC):
    """
    Abstract base class for validation rules.

    Each rule should focus on validating a specific aspect of the OpenAPI specification.
    Rules are designed to be stateless and reusable.

    Subclasses must implement the `validate` method which examines the spec
    and returns a list of ValidationIssue objects for any problems found.
    """

    @property
    @abstractmethod
    def rule_id(self) -> str:
        """
        Return a machine-readable identifier for this rule.

        The rule ID should be in dash-case (kebab-case) format for consistency
        with other validation tools like Redocly.

        Returns:
            Rule identifier (e.g., "server-url-validation")
        """
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Return a human-readable name for this rule.

        Returns:
            Rule name (e.g., "Server URL Validation")
        """
        ...

    @abstractmethod
    def validate(self, spec_data: dict[str, Any]) -> list[ValidationIssue]:
        """
        Validate the OpenAPI specification.

        Args:
            spec_data: The parsed OpenAPI specification as a dictionary

        Returns:
            List of ValidationIssue objects for any problems found.
            Empty list if no issues.
        """
        ...


class RuleRegistry:
    """
    Registry for managing and executing validation rules.

    The registry maintains a collection of validation rules and provides
    methods to execute them against OpenAPI specifications.
    """

    def __init__(self, source: str = "default-validator"):
        """
        Initialize the rule registry.

        Args:
            source: Source identifier for diagnostics (default: "default-validator")
        """
        self.source = source
        self.rules: list[BaseRule] = []

    def register(self, rule: BaseRule) -> None:
        """
        Register a validation rule.

        Args:
            rule: The rule to register
        """
        self.rules.append(rule)

    def register_all(self, rules: list[BaseRule]) -> None:
        """
        Register multiple validation rules at once.

        Args:
            rules: List of rules to register
        """
        self.rules.extend(rules)

    def validate(
        self, spec_data: dict[str, Any], target: str | None = None
    ) -> list[JenticDiagnostic]:
        """
        Run all registered rules against the specification.

        Args:
            spec_data: The parsed OpenAPI specification as a dictionary
            target: Optional target identifier for validation context

        Returns:
            List of JenticDiagnostic objects for all issues found across all rules
        """
        diagnostics: list[JenticDiagnostic] = []

        for rule in self.rules:
            issues = rule.validate(spec_data)
            for issue in issues:
                diagnostic = issue.to_diagnostic(source=self.source, target=target)
                diagnostics.append(diagnostic)

        return diagnostics

    def clear(self) -> None:
        """Clear all registered rules."""
        self.rules.clear()
