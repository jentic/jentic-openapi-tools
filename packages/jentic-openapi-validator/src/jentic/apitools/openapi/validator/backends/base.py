from abc import ABC, abstractmethod
from jentic.apitools.openapi.validator.core import ValidationResult


class BaseValidatorBackend(ABC):
    """Interface that all Validator backends must implement."""

    @abstractmethod
    def validate(self, document: str | dict) -> ValidationResult:
        """Validate an OpenAPI document given by URI or file path or text.
        Returns a ValidationResult (could be a list of errors, or an object)."""
        pass

    @abstractmethod
    def accepts(self) -> list[str]:
        pass
