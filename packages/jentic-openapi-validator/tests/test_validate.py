"""Tests for the core OpenAPIValidator functionality."""

from lsprotocol.types import DiagnosticSeverity, Position, Range

from jentic.apitools.openapi.validator.core import JenticDiagnostic, ValidationResult


class TestValidationResultValid:
    """Tests for ValidationResult.valid severity-based logic."""

    def test_valid_is_true_when_diagnostics_empty(self):
        """Test that valid is True when no diagnostics are present."""
        result = ValidationResult(diagnostics=[])
        assert result.valid is True
        assert bool(result) is True

    def test_valid_is_false_when_error_diagnostic_present(self):
        """Test that valid is False when Error-severity diagnostics are present."""
        error_diagnostic = JenticDiagnostic(
            range=Range(start=Position(line=0, character=0), end=Position(line=0, character=1)),
            message="An error",
            severity=DiagnosticSeverity.Error,
        )
        result = ValidationResult(diagnostics=[error_diagnostic])
        assert result.valid is False
        assert bool(result) is False

    def test_valid_is_true_when_only_warning_diagnostics_present(self):
        """Test that valid is True when only Warning-severity diagnostics are present."""
        warning_diagnostic = JenticDiagnostic(
            range=Range(start=Position(line=0, character=0), end=Position(line=0, character=1)),
            message="A warning",
            severity=DiagnosticSeverity.Warning,
        )
        result = ValidationResult(diagnostics=[warning_diagnostic])
        assert result.valid is True
        assert bool(result) is True

    def test_valid_is_true_when_only_info_diagnostics_present(self):
        """Test that valid is True when only Information-severity diagnostics are present."""
        info_diagnostic = JenticDiagnostic(
            range=Range(start=Position(line=0, character=0), end=Position(line=0, character=1)),
            message="An info",
            severity=DiagnosticSeverity.Information,
        )
        result = ValidationResult(diagnostics=[info_diagnostic])
        assert result.valid is True
        assert bool(result) is True

    def test_valid_is_true_when_only_hint_diagnostics_present(self):
        """Test that valid is True when only Hint-severity diagnostics are present."""
        hint_diagnostic = JenticDiagnostic(
            range=Range(start=Position(line=0, character=0), end=Position(line=0, character=1)),
            message="A hint",
            severity=DiagnosticSeverity.Hint,
        )
        result = ValidationResult(diagnostics=[hint_diagnostic])
        assert result.valid is True
        assert bool(result) is True

    def test_valid_is_false_when_error_mixed_with_other_severities(self):
        """Test that valid is False when Error is present alongside other severities."""
        diagnostics = [
            JenticDiagnostic(
                range=Range(start=Position(line=0, character=0), end=Position(line=0, character=1)),
                message="A warning",
                severity=DiagnosticSeverity.Warning,
            ),
            JenticDiagnostic(
                range=Range(start=Position(line=1, character=0), end=Position(line=1, character=1)),
                message="An error",
                severity=DiagnosticSeverity.Error,
            ),
            JenticDiagnostic(
                range=Range(start=Position(line=2, character=0), end=Position(line=2, character=1)),
                message="An info",
                severity=DiagnosticSeverity.Information,
            ),
        ]
        result = ValidationResult(diagnostics=diagnostics)
        assert result.valid is False
        assert bool(result) is False


def test_validation_result_bool_context(validator, valid_openapi_string):
    """Test that ValidationResult works in boolean context."""
    result = validator.validate(valid_openapi_string)
    assert result  # Should be truthy when valid


def test_validation_result_len(validator, invalid_openapi_string):
    """Test that ValidationResult supports len()."""
    result = validator.validate(invalid_openapi_string)
    assert len(result) > 0


def test_list_backends():
    """Test that list_backends returns available validator backends."""
    from jentic.apitools.openapi.validator.core import OpenAPIValidator

    backends = OpenAPIValidator.list_backends()
    assert isinstance(backends, list)
    assert len(backends) > 0
    assert "openapi-spec" in backends
