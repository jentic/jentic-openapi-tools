from abc import ABC, abstractmethod
from typing import Literal

from ..diagnostics import ValidationResult


class BaseValidatorStrategy(ABC):
    """Interface that all Validator plugins must implement."""

    @abstractmethod
    def validate(
        self, document: str | dict, *, base_url: str | None = None, target: str | None = None
    ) -> ValidationResult:
        """Validate an OpenAPI document given by URI or file path or text.
        Returns a ValidationResult (could be a list of errors, or an object)."""
        pass

    @staticmethod
    def accepts() -> list[Literal["uri", "text", "dict"]]:
        return []
