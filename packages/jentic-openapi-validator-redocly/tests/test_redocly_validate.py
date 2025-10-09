import subprocess

import pytest

from jentic.apitools.openapi.common.subproc import SubprocessExecutionError
from jentic.apitools.openapi.validator.backends.redocly import RedoclyValidatorBackend


pytestmark = pytest.mark.skipif(
    subprocess.run(
        ["npx", "--yes", "@redocly/cli@2.4.0", "--version"], capture_output=True
    ).returncode
    != 0,
    reason="Redocly CLI not available",
)


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


class TestRedoclyValidatorUnit:
    """Unit tests that don't require external dependencies."""

    def test_initialization_with_defaults(self):
        """Test RedoclyValidator initialization with default values."""
        validator = RedoclyValidatorBackend()
        assert validator.redocly_path == "npx --yes @redocly/cli@2.4.0"
        assert validator.ruleset_path is None
        assert validator.timeout == 30.0

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
        assert validator.redocly_path == "npx --yes @redocly/cli@2.4.0"  # default
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

        # Should fail during validation, not initialization
        with pytest.raises(FileNotFoundError, match="Custom ruleset not found"):
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
