import os

import pytest

from jentic.apitools.openapi.common.path_security import (
    InvalidExtensionError,
    PathSecurityError,
    PathTraversalError,
)
from jentic.apitools.openapi.common.subproc import SubprocessExecutionError
from jentic.apitools.openapi.validator.backends.spectral import SpectralValidatorBackend


@pytest.mark.requires_spectral_cli
class TestSpectralValidatorIntegration:
    """Integration tests that require Spectral CLI to be available."""

    def test_validate_valid_openapi_document(self, spectral_validator, valid_openapi_path):
        """Test validation of a valid OpenAPI document."""
        spec_uri = valid_openapi_path.as_uri()
        result = spectral_validator.validate(spec_uri)
        assert result.valid is True

    def test_validate_invalid_openapi_document(self, spectral_validator, invalid_openapi_path):
        """Test validation of an invalid OpenAPI document."""
        spec_uri = invalid_openapi_path.as_uri()
        result = spectral_validator.validate(spec_uri)
        assert result.valid is False

    def test_validate_with_custom_ruleset(
        self, spectral_validator_with_custom_ruleset, valid_openapi_path
    ):
        """Test validation using a custom ruleset."""
        spec_uri = valid_openapi_path.as_uri()
        result = spectral_validator_with_custom_ruleset.validate(spec_uri)
        assert result.valid is True

    def test_validate_with_long_timeout(
        self, spectral_validator_with_long_timeout, valid_openapi_path
    ):
        """Test validation with extended timeout still works."""
        spec_uri = valid_openapi_path.as_uri()
        result = spectral_validator_with_long_timeout.validate(spec_uri)
        assert result.valid is True


class TestSpectralValidatorUnit:
    """Unit tests that don't require external dependencies."""

    def test_initialization_with_defaults(self):
        """Test SpectralValidator initialization with default values."""
        validator = SpectralValidatorBackend()
        assert validator.spectral_path == "npx --yes @stoplight/spectral-cli@6.15.0"
        assert validator.ruleset_path is None
        assert validator.timeout == 600.0

    def test_initialization_with_custom_spectral_path(self):
        """Test SpectralValidator with a custom spectral path."""
        validator = SpectralValidatorBackend(spectral_path="/custom/path/to/spectral")
        assert validator.spectral_path == "/custom/path/to/spectral"

    def test_initialization_with_custom_ruleset_path(self, custom_ruleset_path):
        """Test SpectralValidator with a custom ruleset path."""
        validator = SpectralValidatorBackend(ruleset_path=str(custom_ruleset_path))
        assert validator.ruleset_path == str(custom_ruleset_path)

    def test_initialization_with_custom_timeout(self):
        """Test SpectralValidator with custom timeout."""
        validator = SpectralValidatorBackend(timeout=60.0)
        assert validator.timeout == 60.0
        assert validator.spectral_path == "npx --yes @stoplight/spectral-cli@6.15.0"  # default
        assert validator.ruleset_path is None  # default

    def test_initialization_with_all_custom_parameters(self, custom_ruleset_path):
        """Test SpectralValidator with all custom parameters."""
        validator = SpectralValidatorBackend(
            spectral_path="/custom/spectral", ruleset_path=str(custom_ruleset_path), timeout=45.0
        )
        assert validator.spectral_path == "/custom/spectral"
        assert validator.ruleset_path == str(custom_ruleset_path)
        assert validator.timeout == 45.0

    def test_initialization_with_invalid_ruleset_path(self, tmp_path):
        """Test SpectralValidator with a non-existent custom ruleset path."""
        nonexistent_path = tmp_path / "nonexistent_ruleset.yaml"
        validator = SpectralValidatorBackend(ruleset_path=str(nonexistent_path))

        # Should fail during validation when the ruleset path is validated
        with pytest.raises((PathSecurityError, RuntimeError)):
            validator.validate("file://some/test/file.yaml")

    def test_accepts_method(self):
        """Test the accepts method returns correct format identifiers."""
        validator = SpectralValidatorBackend()
        accepted = validator.accepts()
        assert isinstance(accepted, list)
        assert "uri" in accepted
        assert "dict" in accepted

    def test_unsupported_document_type(self):
        """Test validation with an unsupported document type."""
        validator = SpectralValidatorBackend()

        with pytest.raises(TypeError, match="Unsupported document type"):
            validator.validate(42)  # type: ignore


class TestSpectralValidatorErrorCases:
    """Test error cases and edge conditions."""

    def test_validator_without_cli(self):
        """Test SpectralValidator behavior when spectral CLI is not available."""
        validator = SpectralValidatorBackend(spectral_path="nonexistent_spectral")

        with pytest.raises(SubprocessExecutionError, match="'nonexistent_spectral"):
            validator.validate("/some/test/file.yaml")


class TestSpectralValidatorErrorHandling:
    """Test _handle_error extension point."""

    def test_base_class_raises_runtime_error_on_execution_failure(self):
        """Test that base class raises RuntimeError for execution errors by default."""
        validator = SpectralValidatorBackend(spectral_path="nonexistent_spectral_cli")

        # Base class should raise SubprocessExecutionError (command not found)
        with pytest.raises(SubprocessExecutionError):
            validator.validate("/some/test/file.yaml")

    def test_custom_error_handler_can_intercept_errors(self):
        """Test that subclasses can override _handle_error to handle errors gracefully."""
        from lsprotocol.types import DiagnosticSeverity, Position, Range

        from jentic.apitools.openapi.common.subproc import SubprocessExecutionResult
        from jentic.apitools.openapi.validator.core import JenticDiagnostic, ValidationResult

        class CustomSpectralValidator(SpectralValidatorBackend):
            """Custom validator that handles fetch errors gracefully."""

            def _handle_error(
                self,
                stderr_msg: str,
                result: SubprocessExecutionResult,
                document_path: str,
                target: str | None = None,
            ) -> ValidationResult | None:
                """Override to handle fetch errors."""
                # Handle "Could not parse" errors (fetch failures)
                if "Could not parse" in stderr_msg and "://" in document_path:
                    diagnostic = JenticDiagnostic(
                        range=Range(
                            start=Position(line=0, character=0),
                            end=Position(line=0, character=0),
                        ),
                        message=f"Could not fetch document: {document_path}",
                        severity=DiagnosticSeverity.Error,
                        code="document-fetch-error",
                        source="spectral-validator",
                    )
                    diagnostic.set_target(target)
                    return ValidationResult(diagnostics=[diagnostic])

                # Fall back to default behavior
                return super()._handle_error(stderr_msg, result, document_path, target)

        # This test verifies the structure works
        validator = CustomSpectralValidator()
        assert hasattr(validator, "_handle_error")
        assert callable(validator._handle_error)

    def test_custom_error_handler_accesses_instance_state(self):
        """Test that custom error handler can access instance attributes via self."""
        from jentic.apitools.openapi.common.subproc import SubprocessExecutionResult
        from jentic.apitools.openapi.validator.core import ValidationResult

        class StateAccessValidator(SpectralValidatorBackend):
            """Validator that accesses instance state in error handler."""

            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.error_count = 0

            def _handle_error(
                self,
                stderr_msg: str,
                result: SubprocessExecutionResult,
                document_path: str,
                target: str | None = None,
            ) -> ValidationResult | None:
                """Track errors using instance state."""
                self.error_count += 1
                # Fall back to default behavior
                return super()._handle_error(stderr_msg, result, document_path, target)

        validator = StateAccessValidator(spectral_path="nonexistent_cli")

        # Verify instance attributes are accessible
        assert validator.error_count == 0
        assert validator.timeout == 600.0  # default

        # Try to validate (will fail, but that's expected)
        with pytest.raises(SubprocessExecutionError):
            validator.validate("/test/file.yaml")

    def test_handle_error_returns_none_by_default(self):
        """Test that base implementation returns None (allowing default error handling)."""
        from jentic.apitools.openapi.common.subproc import SubprocessExecutionResult

        validator = SpectralValidatorBackend()

        # Call _handle_error directly
        result = SubprocessExecutionResult(returncode=2, stdout="", stderr="some error")
        handled = validator._handle_error("some error", result, "/test/doc.yaml", target=None)

        # Should return None to proceed with default error handling
        assert handled is None


class TestSpectralValidatorPathSecurity:
    """Test path security features."""

    def test_initialization_with_allowed_base_dir(self, tmp_path):
        """Test SpectralValidator initialization with allowed_base_dir."""
        validator = SpectralValidatorBackend(allowed_base_dir=str(tmp_path))
        assert validator.allowed_base_dir == str(tmp_path)

    def test_initialization_without_allowed_base_dir(self):
        """Test SpectralValidator initialization without allowed_base_dir (default None)."""
        validator = SpectralValidatorBackend()
        assert validator.allowed_base_dir is None

    def test_path_validation_disabled_when_allowed_base_dir_is_none(self, tmp_path):
        """Test that path traversal is NOT blocked when allowed_base_dir is None."""
        validator = SpectralValidatorBackend(allowed_base_dir=None)

        # Create a test file outside any restricted directory
        test_file = tmp_path / "spec.yaml"
        test_file.write_text("openapi: 3.0.0\ninfo:\n  title: Test\n  version: 1.0.0\npaths: {}")

        # This should not raise PathTraversalError (but may fail for other reasons like missing Spectral)
        try:
            validator.validate(str(test_file))
        except PathTraversalError:
            pytest.fail("PathTraversalError should not be raised when allowed_base_dir=None")
        except (SubprocessExecutionError, RuntimeError):
            # Expected if Spectral is not available
            pass

    def test_valid_path_within_allowed_base_dir(self, tmp_path):
        """Test that paths within allowed_base_dir are accepted."""
        test_file = tmp_path / "spec.yaml"
        test_file.write_text("openapi: 3.0.0\ninfo:\n  title: Test\n  version: 1.0.0\npaths: {}")

        validator = SpectralValidatorBackend(allowed_base_dir=str(tmp_path))

        # Should not raise PathTraversalError
        try:
            validator.validate(str(test_file))
        except PathTraversalError:
            pytest.fail("Valid path should not raise PathTraversalError")
        except (SubprocessExecutionError, RuntimeError):
            # May fail for Spectral-related reasons
            pass

    def test_path_traversal_attempt_blocked(self, tmp_path):
        """Test that path traversal attempts are blocked."""
        # Create a restricted directory
        restricted_dir = tmp_path / "restricted"
        restricted_dir.mkdir()

        # Create a file outside the restricted directory
        outside_file = tmp_path / "outside.yaml"
        outside_file.write_text("openapi: 3.0.0")

        validator = SpectralValidatorBackend(allowed_base_dir=str(restricted_dir))

        # Attempt to access file outside allowed directory
        with pytest.raises(PathTraversalError):
            validator.validate(str(outside_file))

    def test_invalid_file_extension_rejected(self, tmp_path):
        """Test that files with invalid extensions are rejected."""
        test_file = tmp_path / "malicious.exe"
        test_file.write_text("fake executable")

        validator = SpectralValidatorBackend(allowed_base_dir=str(tmp_path))

        with pytest.raises(InvalidExtensionError):
            validator.validate(str(test_file))

    def test_http_url_bypasses_path_validation(self):
        """Test that HTTP(S) URLs bypass path validation."""
        validator = SpectralValidatorBackend(allowed_base_dir="/restricted/path")

        # HTTP URLs should bypass path validation (though they may fail for other reasons)
        try:
            validator.validate("https://example.com/openapi.yaml")
        except PathTraversalError:
            pytest.fail("HTTP URLs should bypass path validation")
        except (SubprocessExecutionError, RuntimeError):
            # Expected - Spectral may fail to fetch the URL
            pass

    def test_file_uri_with_path_validation(self, tmp_path):
        """Test that file:// URIs are validated correctly."""
        test_file = tmp_path / "spec.yaml"
        test_file.write_text("openapi: 3.0.0\ninfo:\n  title: Test\n  version: 1.0.0\npaths: {}")

        validator = SpectralValidatorBackend(allowed_base_dir=str(tmp_path))

        # file:// URI should be validated
        try:
            validator.validate(test_file.as_uri())
        except PathTraversalError:
            pytest.fail("Valid file URI should not raise PathTraversalError")
        except (SubprocessExecutionError, RuntimeError):
            pass

    def test_ruleset_path_validated_during_validation(self, tmp_path):
        """Test that ruleset_path is validated during validation."""
        test_file = tmp_path / "spec.yaml"
        test_file.write_text("openapi: 3.0.0\ninfo:\n  title: Test\n  version: 1.0.0\npaths: {}")

        ruleset_file = tmp_path / "ruleset.yaml"
        ruleset_file.write_text("extends: ['spectral:oas']")

        validator = SpectralValidatorBackend(
            allowed_base_dir=str(tmp_path), ruleset_path=str(ruleset_file)
        )

        # Should not raise PathTraversalError for ruleset
        try:
            validator.validate(str(test_file))
        except PathTraversalError:
            pytest.fail("Valid ruleset path should not raise PathTraversalError")
        except (SubprocessExecutionError, RuntimeError):
            pass

    def test_ruleset_path_outside_allowed_dir_blocked(self, tmp_path):
        """Test that ruleset paths outside allowed_base_dir are blocked."""
        restricted_dir = tmp_path / "restricted"
        restricted_dir.mkdir()

        test_file = restricted_dir / "spec.yaml"
        test_file.write_text("openapi: 3.0.0")

        # Ruleset outside the restricted directory
        outside_ruleset = tmp_path / "ruleset.yaml"
        outside_ruleset.write_text("extends: ['spectral:oas']")

        validator = SpectralValidatorBackend(
            allowed_base_dir=str(restricted_dir), ruleset_path=str(outside_ruleset)
        )

        with pytest.raises(PathTraversalError):
            validator.validate(str(test_file))

    def test_valid_yaml_extensions_accepted(self, tmp_path):
        """Test that .yaml, .yml, and .json extensions are all accepted."""
        validator = SpectralValidatorBackend(allowed_base_dir=str(tmp_path))

        for ext in [".yaml", ".yml", ".json"]:
            test_file = tmp_path / f"spec{ext}"
            test_file.write_text("openapi: 3.0.0")

            try:
                validator.validate(str(test_file))
            except InvalidExtensionError:
                pytest.fail(f"Extension {ext} should be accepted")
            except (SubprocessExecutionError, RuntimeError):
                pass

    def test_relative_path_resolved_and_validated(self, tmp_path):
        """Test that relative paths are resolved before validation."""
        # Create a test file
        test_file = tmp_path / "spec.yaml"
        test_file.write_text("openapi: 3.0.0\ninfo:\n  title: Test\n  version: 1.0.0\npaths: {}")

        validator = SpectralValidatorBackend(allowed_base_dir=str(tmp_path))

        # Use relative path - should be resolved and validated (no PathTraversalError)
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            try:
                validator.validate("./spec.yaml")
            except (SubprocessExecutionError, RuntimeError):
                # May fail for Spectral reasons, but path validation passed
                pass
        finally:
            os.chdir(original_cwd)
