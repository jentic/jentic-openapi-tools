import subprocess
import pytest

from jentic.apitools.openapi.common.subproc import SubprocessExecutionError
from jentic.apitools.openapi.validator.backends.spectral import SpectralValidatorBackend

pytestmark = pytest.mark.skipif(
    subprocess.run(
        ["npx", "@stoplight/spectral-cli@^6.15.0", "--version"], capture_output=True
    ).returncode
    != 0,
    reason="Spectral CLI not available",
)


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
        assert validator.spectral_path == "npx @stoplight/spectral-cli@^6.15.0"
        assert validator.ruleset_path is None
        assert validator.timeout == 30.0

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
        assert validator.spectral_path == "npx @stoplight/spectral-cli@^6.15.0"  # default
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

        # Should fail during validation, not initialization
        with pytest.raises(FileNotFoundError, match="Custom ruleset not found"):
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
