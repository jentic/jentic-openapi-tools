from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from jentic.apitools.openapi.validator.core.diagnostics import ValidationResult


__all__ = ["BaseValidatorBackend"]


class BaseValidatorBackend(ABC):
    """Interface that all Validator backends must implement."""

    @abstractmethod
    def validate(
        self, document: str | dict, *, base_url: str | None = None, target: str | None = None
    ) -> ValidationResult:
        """Validate an OpenAPI document given by URI or file path or text.
        Returns a ValidationResult (could be a list of errors, or an object)."""
        ...

    @staticmethod
    @abstractmethod
    def accepts() -> Sequence[str]:
        """Return the document formats this backend can accept.

        Returns:
            Sequence of format identifiers (e.g., "uri", "text", "dict")
        """
        ...
