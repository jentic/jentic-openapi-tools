"""Integration tests for Spectral backend discovery and usage."""

import pytest

from jentic.apitools.openapi.validator.core import OpenAPIValidator


def test_spectral_backend_discovery():
    """Test that the spectral backend can be discovered via entry points."""
    try:
        validator = OpenAPIValidator(backends=["openapi-spec", "spectral"])
        assert len(validator.backends) == 2

        backend_names = [type(b).__name__ for b in validator.backends]
        assert "OpenAPISpecValidatorBackend" in backend_names
        assert "SpectralValidatorBackend" in backend_names
    except ValueError as e:
        if "No validator backend named 'spectral' found" in str(e):
            pytest.skip(
                "jentic-openapi-validator-spectral not installed - skipping integration test"
            )
        else:
            raise


@pytest.mark.requires_spectral_cli
def test_spectral_validation_integration(sample_openapi_yaml):
    """Test that spectral validation works end-to-end."""
    try:
        validator = OpenAPIValidator(backends=["openapi-spec", "spectral"])
        result = validator.validate(str(sample_openapi_yaml))

        assert result is not None
        assert hasattr(result, "diagnostics")
    except ValueError as e:
        if "No validator backend named 'spectral' found" in str(e):
            pytest.skip(
                "jentic-openapi-validator-spectral not installed - skipping integration test"
            )
        else:
            raise


@pytest.mark.requires_spectral_cli
def test_spectral_only_backend(sample_openapi_yaml):
    """Test using only the spectral backend."""
    try:
        validator = OpenAPIValidator(backends=["spectral"])
        result = validator.validate(str(sample_openapi_yaml))

        assert result is not None
        assert len(validator.backends) == 1
        assert type(validator.backends[0]).__name__ == "SpectralValidatorBackend"
    except ValueError as e:
        if "No validator backend named 'spectral' found" in str(e):
            pytest.skip(
                "jentic-openapi-validator-spectral not installed - skipping integration test"
            )
        else:
            raise


@pytest.mark.requires_spectral_cli
def test_invalid_backend_name():
    """Test that invalid backend names raise appropriate errors."""
    with pytest.raises(ValueError, match="No validator backend named 'nonexistent' found"):
        OpenAPIValidator(backends=["nonexistent"])


@pytest.mark.requires_spectral_cli
def test_spectral_with_real_cli(sample_openapi_yaml):
    """Test spectral integration when the actual spectral CLI is available."""
    try:
        validator = OpenAPIValidator(backends=["spectral"])
        result = validator.validate(str(sample_openapi_yaml))

        assert result is not None
        assert len(result) >= 0  # May have diagnostics or not
    except ValueError as e:
        if "No validator backend named 'spectral' found" in str(e):
            pytest.skip("jentic-openapi-validator-spectral not installed")
        else:
            raise
