"""Integration tests for Redocly backend discovery and usage."""

import pytest
from jentic.apitools.openapi.transformer.bundler.core import OpenAPIBundler


def test_redocly_backend_discovery():
    """Test that the redocly backend can be discovered via entry points."""
    try:
        bundler = OpenAPIBundler("redocly")
        backend_name = type(bundler.backend).__name__
        assert backend_name == "RedoclyBundlerBackend"
    except ValueError as e:
        if "No bundler backend named 'redocly' found" in str(e):
            pytest.skip(
                "jentic-openapi-transformer-redocly not installed - skipping integration test"
            )
        else:
            raise


@pytest.mark.requires_redocly_cli
def test_redocly_only_backend(sample_openapi_yaml):
    """Test using only the redocly backend."""
    try:
        bundler = OpenAPIBundler("redocly")
        result = bundler.bundle(str(sample_openapi_yaml), return_type=str)

        assert result is not None and isinstance(result, str) and len(result) > 0
        assert type(bundler.backend).__name__ == "RedoclyBundlerBackend"
    except ValueError as e:
        if "No bundler backend named 'redocly' found" in str(e):
            pytest.skip(
                "jentic-openapi-transformer-redocly not installed - skipping integration test"
            )
        else:
            raise


@pytest.mark.requires_redocly_cli
def test_invalid_backend_name():
    """Test that invalid backend names raise appropriate errors."""
    with pytest.raises(ValueError, match="No bundler backend named 'nonexistent' found"):
        OpenAPIBundler("nonexistent")


@pytest.mark.requires_redocly_cli
def test_redocly_with_real_cli(sample_openapi_yaml):
    """Test redocly integration when the actual redocly CLI is available."""
    try:
        bundler = OpenAPIBundler("redocly")
        result = bundler.bundle(str(sample_openapi_yaml), return_type=str)

        assert result is not None and isinstance(result, str) and len(result) > 0
    except ValueError as e:
        if "No bundler backend named 'redocly' found" in str(e):
            pytest.skip("jentic-openapi-transformer-redocly not installed")
        else:
            raise
