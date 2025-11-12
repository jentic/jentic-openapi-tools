import os

import pytest

from jentic.apitools.openapi.common.path_security import (
    InvalidExtensionError,
    PathSecurityError,
    PathTraversalError,
)
from jentic.apitools.openapi.common.subproc import SubprocessExecutionError
from jentic.apitools.openapi.validator.backends.redocly import RedoclyValidatorBackend


@pytest.mark.requires_redocly_cli
class TestRedoclyValidatorIntegration:
    """Integration tests that require Redocly CLI to be available."""

    def test_validate_valid_openapi_document(self, redocly_validator, valid_openapi_path):
        """Test validation of a valid OpenAPI document."""
        spec_uri = valid_openapi_path.as_uri()
        result = redocly_validator.validate(spec_uri)
        assert result.valid is True

    def test_validate_invalid_openapi_document(self, redocly_validator, invalid_openapi_path):
        """Test validation of an invalid OpenAPI document."""
        spec_uri = invalid_openapi_path.as_uri()
        result = redocly_validator.validate(spec_uri)
        assert result.valid is False

    def test_validate_with_custom_ruleset(
        self, redocly_validator_with_custom_ruleset, valid_openapi_path
    ):
        """Test validation using a custom ruleset."""
        spec_uri = valid_openapi_path.as_uri()
        result = redocly_validator_with_custom_ruleset.validate(spec_uri)
        assert result.valid is True

    def test_validate_with_long_timeout(
        self, redocly_validator_with_long_timeout, valid_openapi_path
    ):
        """Test validation with extended timeout still works."""
        spec_uri = valid_openapi_path.as_uri()
        result = redocly_validator_with_long_timeout.validate(spec_uri)
        assert result.valid is True

    def test_validate_catches_missing_operation_summary(
        self, redocly_validator, no_summary_openapi_path
    ):
        """Test that Redocly's recommended rules catch missing operation summaries."""
        spec_uri = no_summary_openapi_path.as_uri()
        result = redocly_validator.validate(spec_uri)
        assert result.valid is False
        assert result.diagnostics[0].code == "operation-summary"
        assert (
            result.diagnostics[0].message
            == "Operation object should contain `summary` field. [path: paths./test.get.summary]"
        )


class TestRedoclyValidatorUnit:
    """Unit tests that don't require external dependencies."""

    def test_initialization_with_defaults(self):
        """Test RedoclyValidator initialization with default values."""
        validator = RedoclyValidatorBackend()
        assert validator.redocly_path == "npx --yes @redocly/cli@2.11.1"
        assert validator.ruleset_path is None
        assert validator.timeout == 600.0

    def test_initialization_with_custom_redocly_path(self):
        """Test RedoclyValidator with a custom redocly path."""
        validator = RedoclyValidatorBackend(redocly_path="/custom/path/to/redocly")
        assert validator.redocly_path == "/custom/path/to/redocly"

    def test_initialization_with_custom_ruleset_path(self, custom_ruleset_path):
        """Test RedoclyValidator with a custom ruleset path."""
        validator = RedoclyValidatorBackend(ruleset_path=str(custom_ruleset_path))
        assert validator.ruleset_path == str(custom_ruleset_path)

    def test_initialization_with_custom_timeout(self):
        """Test RedoclyValidator with custom timeout."""
        validator = RedoclyValidatorBackend(timeout=60.0)
        assert validator.timeout == 60.0
        assert validator.redocly_path == "npx --yes @redocly/cli@2.11.1"  # default
        assert validator.ruleset_path is None  # default

    def test_initialization_with_all_custom_parameters(self, custom_ruleset_path):
        """Test RedoclyValidator with all custom parameters."""
        validator = RedoclyValidatorBackend(
            redocly_path="/custom/redocly", ruleset_path=str(custom_ruleset_path), timeout=45.0
        )
        assert validator.redocly_path == "/custom/redocly"
        assert validator.ruleset_path == str(custom_ruleset_path)
        assert validator.timeout == 45.0

    def test_initialization_with_invalid_ruleset_path(self, tmp_path):
        """Test RedoclyValidator with a non-existent custom ruleset path."""
        nonexistent_path = tmp_path / "nonexistent_ruleset.yaml"
        validator = RedoclyValidatorBackend(ruleset_path=str(nonexistent_path))

        # Should fail during validation when the ruleset path is validated
        # The error will come from validate_path (PathSecurityError) or Redocly (RuntimeError)
        with pytest.raises((PathSecurityError, RuntimeError)):
            validator.validate("file://some/test/file.yaml")

    def test_accepts_method(self):
        """Test the accepts method returns correct format identifiers."""
        validator = RedoclyValidatorBackend()
        accepted = validator.accepts()
        assert isinstance(accepted, list)
        assert "uri" in accepted
        assert "dict" in accepted

    def test_unsupported_document_type(self):
        """Test validation with an unsupported document type."""
        validator = RedoclyValidatorBackend()

        with pytest.raises(TypeError, match="Unsupported document type"):
            validator.validate(42)  # type: ignore


class TestRedoclyValidatorErrorCases:
    """Test error cases and edge conditions."""

    def test_validator_without_cli(self):
        """Test RedoclyValidator behavior when redocly CLI is not available."""
        validator = RedoclyValidatorBackend(redocly_path="nonexistent_redocly")

        with pytest.raises(SubprocessExecutionError, match="'nonexistent_redocly"):
            validator.validate("/some/test/file.yaml")


class TestRedoclyValidatorPathSecurity:
    """Test path security validation features."""

    def test_initialization_with_allowed_base_dir(self, tmp_path):
        """Test that allowed_base_dir can be set during initialization."""
        validator = RedoclyValidatorBackend(allowed_base_dir=str(tmp_path))
        assert validator.allowed_base_dir == str(tmp_path)

    def test_initialization_without_allowed_base_dir(self):
        """Test backward compatibility when allowed_base_dir is not set."""
        validator = RedoclyValidatorBackend()
        assert validator.allowed_base_dir is None

    def test_path_validation_disabled_when_allowed_base_dir_is_none(self, tmp_path):
        """Test that path validation is skipped when allowed_base_dir is None."""
        # Create a test file outside any restricted directory
        test_file = tmp_path / "test.yaml"
        test_file.write_text("openapi: 3.0.0\ninfo:\n  title: Test\n  version: 1.0.0\npaths: {}")

        # Should not raise PathTraversalError since no allowed_base_dir is set
        validator = RedoclyValidatorBackend()
        # Will either succeed or fail for other reasons, but NOT path validation
        try:
            validator.validate(str(test_file))
        except (SubprocessExecutionError, RuntimeError):
            # Redocly CLI may or may not be available, or file may be invalid
            # We're just checking that PathTraversalError wasn't raised
            pass

    def test_valid_path_within_allowed_base_dir(self, tmp_path):
        """Test that valid paths within allowed_base_dir are accepted."""
        test_file = tmp_path / "spec.yaml"
        test_file.write_text("openapi: 3.0.0\ninfo:\n  title: Test\n  version: 1.0.0\npaths: {}")

        validator = RedoclyValidatorBackend(allowed_base_dir=str(tmp_path))

        # Path validation should pass (no PathTraversalError or InvalidExtensionError)
        try:
            validator.validate(str(test_file))
        except (SubprocessExecutionError, RuntimeError):
            # May fail for Redocly CLI reasons, but path validation passed
            pass

    def test_path_traversal_attempt_blocked(self, tmp_path):
        """Test that path traversal attempts are blocked."""
        # Create directory structure
        base_dir = tmp_path / "allowed"
        base_dir.mkdir()

        # Try to access path outside allowed directory
        validator = RedoclyValidatorBackend(allowed_base_dir=str(base_dir))

        with pytest.raises(PathTraversalError, match="outside allowed base"):
            validator.validate(str(tmp_path / ".." / "etc" / "passwd"))

    def test_invalid_file_extension_rejected(self, tmp_path):
        """Test that files with invalid extensions are rejected."""
        test_file = tmp_path / "malicious.exe"
        test_file.write_text("fake executable")

        validator = RedoclyValidatorBackend(allowed_base_dir=str(tmp_path))

        with pytest.raises(InvalidExtensionError, match="disallowed extension"):
            validator.validate(str(test_file))

    def test_http_url_bypasses_path_validation(self):
        """Test that HTTP(S) URLs bypass path validation."""
        validator = RedoclyValidatorBackend(allowed_base_dir="/restricted/dir")

        # HTTP URLs should bypass path validation entirely (no PathTraversalError)
        try:
            validator.validate("https://example.com/openapi.yaml")
        except (SubprocessExecutionError, RuntimeError):
            # May fail at network/Redocly level, but path validation was bypassed
            pass

    def test_file_uri_with_path_validation(self, tmp_path):
        """Test that file:// URIs are validated when allowed_base_dir is set."""
        test_file = tmp_path / "spec.yaml"
        test_file.write_text("openapi: 3.0.0\ninfo:\n  title: Test\n  version: 1.0.0\npaths: {}")

        validator = RedoclyValidatorBackend(allowed_base_dir=str(tmp_path))

        # file:// URI should be validated (no PathTraversalError)
        file_uri = test_file.as_uri()
        try:
            validator.validate(file_uri)
        except (SubprocessExecutionError, RuntimeError):
            # May fail for Redocly reasons, but path validation passed
            pass

    def test_ruleset_path_validated_during_validation(self, tmp_path):
        """Test that ruleset_path is validated during validation when allowed_base_dir is set."""
        # Create a ruleset inside allowed directory
        ruleset = tmp_path / "rules.yaml"
        ruleset.write_text("extends: [recommended]")

        # Create a valid document inside allowed directory
        test_file = tmp_path / "spec.yaml"
        test_file.write_text("openapi: 3.0.0\ninfo:\n  title: Test\n  version: 1.0.0\npaths: {}")

        # Validator initialization should succeed
        validator = RedoclyValidatorBackend(
            allowed_base_dir=str(tmp_path),
            ruleset_path=str(ruleset),
        )

        # Validation should succeed (no PathTraversalError or InvalidExtensionError)
        try:
            validator.validate(str(test_file))
        except (SubprocessExecutionError, RuntimeError):
            # May fail for Redocly reasons, but path validation passed
            pass

    def test_ruleset_path_outside_allowed_dir_blocked(self, tmp_path):
        """Test that ruleset_path outside allowed_base_dir is blocked during validation."""
        base_dir = tmp_path / "allowed"
        base_dir.mkdir()

        # Create ruleset outside allowed directory
        outside_ruleset = tmp_path / "outside_rules.yaml"
        outside_ruleset.write_text("extends: [recommended]")

        # Create a valid document inside allowed directory
        test_file = base_dir / "spec.yaml"
        test_file.write_text("openapi: 3.0.0\ninfo:\n  title: Test\n  version: 1.0.0\npaths: {}")

        # Should raise during validation, not initialization
        validator = RedoclyValidatorBackend(
            allowed_base_dir=str(base_dir),
            ruleset_path=str(outside_ruleset),
        )

        with pytest.raises(PathTraversalError, match="outside allowed base"):
            validator.validate(str(test_file))

    def test_valid_yaml_extensions_accepted(self, tmp_path):
        """Test that .yaml, .yml, and .json extensions are accepted."""
        validator = RedoclyValidatorBackend(allowed_base_dir=str(tmp_path))

        for ext in [".yaml", ".yml", ".json"]:
            test_file = tmp_path / f"spec{ext}"
            test_file.write_text(
                "openapi: 3.0.0\ninfo:\n  title: Test\n  version: 1.0.0\npaths: {}"
            )

            # Should pass path validation (no InvalidExtensionError)
            try:
                validator.validate(str(test_file))
            except (SubprocessExecutionError, RuntimeError):
                # May fail for Redocly reasons, but path validation passed
                pass

    def test_relative_path_resolved_and_validated(self, tmp_path):
        """Test that relative paths are resolved before validation."""
        # Create a test file
        test_file = tmp_path / "spec.yaml"
        test_file.write_text("openapi: 3.0.0\ninfo:\n  title: Test\n  version: 1.0.0\npaths: {}")

        validator = RedoclyValidatorBackend(allowed_base_dir=str(tmp_path))

        # Use relative path - should be resolved and validated (no PathTraversalError)
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            try:
                validator.validate("./spec.yaml")
            except (SubprocessExecutionError, RuntimeError):
                # May fail for Redocly reasons, but path validation passed
                pass
        finally:
            os.chdir(original_cwd)
