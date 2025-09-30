from dataclasses import dataclass, field
from lsprotocol.types import Diagnostic


@dataclass
class ValidationResult:
    """
    Represents the result of validating an OpenAPI document.

    This class encapsulates all diagnostics (errors, warnings, etc.) produced
    by validator backends and provides convenient methods to check validation
    status and filter diagnostics by severity.

    Attributes:
        diagnostics: List of all diagnostics from validation
        valid: True if no diagnostics were found, False otherwise (computed automatically)
    """

    diagnostics: list[Diagnostic] = field(default_factory=list)
    valid: bool = field(init=False)

    def __post_init__(self):
        """Compute the valid attribute after initialization."""
        self.valid = len(self.diagnostics) == 0

    def __bool__(self) -> bool:
        """
        Allow ValidationResult to be used in boolean context.

        Returns:
            True if validation passed (no diagnostics), False otherwise

        Example:
            >>> result = validator.validate(document)
            >>> if result:
            ...     print("Validation passed!")
        """
        return self.valid

    def __len__(self) -> int:
        """
        Return the number of diagnostics.

        Returns:
            Count of all diagnostics

        Example:
            >>> result = validator.validate(document)
            >>> print(f"Found {len(result)} issues")
        """
        return len(self.diagnostics)

    def __repr__(self) -> str:
        """Return a string representation of the validation result."""
        status = "valid" if self.valid else "invalid"
        return f"ValidationResult(status={status}, diagnostics={len(self.diagnostics)})"
