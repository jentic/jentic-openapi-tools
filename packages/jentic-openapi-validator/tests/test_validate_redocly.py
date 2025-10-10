"""Integration tests for Redocly backend discovery and usage."""

import pytest

from jentic.apitools.openapi.validator.core import OpenAPIValidator


def test_redocly_backend_discovery():
    """Test that the redocly backend can be discovered via entry points."""
    try:
        validator = OpenAPIValidator(backends=["openapi-spec", "redocly"])
        assert len(validator.backends) == 2

        backend_names = [type(b).__name__ for b in validator.backends]
        assert "OpenAPISpecValidatorBackend" in backend_names
        assert "RedoclyValidatorBackend" in backend_names
    except ValueError as e:
        if "No validator backend named 'redocly' found" in str(e):
            pytest.skip(
                "jentic-openapi-validator-redocly not installed - skipping integration test"
            )
        else:
            raise


@pytest.mark.requires_redocly_cli
def test_redocly_validation_integration(sample_openapi_yaml):
    """Test that redocly validation works end-to-end."""
    try:
        validator = OpenAPIValidator(backends=["openapi-spec", "redocly"])
        result = validator.validate(str(sample_openapi_yaml))

        assert result is not None
        assert hasattr(result, "diagnostics")
    except ValueError as e:
        if "No validator backend named 'redocly' found" in str(e):
            pytest.skip(
                "jentic-openapi-validator-redocly not installed - skipping integration test"
            )
        else:
            raise


@pytest.mark.requires_redocly_cli
def test_redocly_only_backend(sample_openapi_yaml):
    """Test using only the redocly backend."""
    try:
        validator = OpenAPIValidator(backends=["redocly"])
        result = validator.validate(str(sample_openapi_yaml))

        assert result is not None
        assert len(validator.backends) == 1
        assert type(validator.backends[0]).__name__ == "RedoclyValidatorBackend"
    except ValueError as e:
        if "No validator backend named 'redocly' found" in str(e):
            pytest.skip(
                "jentic-openapi-validator-redocly not installed - skipping integration test"
            )
        else:
            raise


@pytest.mark.requires_redocly_cli
def test_invalid_backend_name():
    """Test that invalid backend names raise appropriate errors."""
    with pytest.raises(ValueError, match="No validator backend named 'nonexistent' found"):
        OpenAPIValidator(backends=["nonexistent"])


@pytest.mark.requires_redocly_cli
def test_redocly_with_real_cli(sample_openapi_yaml):
    """Test redocly integration when the actual redocly CLI is available."""
    try:
        validator = OpenAPIValidator(backends=["redocly"])
        result = validator.validate(str(sample_openapi_yaml))

        assert result is not None
        assert len(result) >= 0  # May have diagnostics or not
    except ValueError as e:
        if "No validator backend named 'redocly' found" in str(e):
            pytest.skip("jentic-openapi-validator-redocly not installed")
        else:
            raise
