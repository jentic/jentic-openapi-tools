from abc import ABC, abstractmethod

from ..core.diagnostics import ValidationResult


class BaseValidatorStrategy(ABC):
    """Interface that all Validator plugins must implement."""

    @abstractmethod
    def validate(self, document: str | dict) -> ValidationResult:
        """Validate an OpenAPI document given by URI or file path or text.
        Returns a ValidationResult (could be a list of errors, or an object)."""
        pass

    @abstractmethod
    def accepts(self) -> list[str]:
        pass
