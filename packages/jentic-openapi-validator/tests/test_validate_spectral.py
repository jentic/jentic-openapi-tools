import subprocess
import pytest
from jentic_openapi_validator import OpenAPIValidator


@pytest.fixture
def sample_openapi_file(tmp_path):
    """Create a temporary OpenAPI file for testing."""
    openapi_content = """
openapi: 3.1.0
info:
  title: Test API
  version: 1.0.0
paths:
  /users:
    get:
      summary: Get users
      responses:
        '200':
          description: Success
          content:
            application/json:
              schema:
                type: array
                items:
                  type: object
"""
    openapi_file = tmp_path / "test_api.yaml"
    openapi_file.write_text(openapi_content.strip())
    return str(openapi_file)


def test_spectral_plugin_discovery():
    """Test that the spectral plugin can be discovered via entry points."""
    try:
        # This should work if jentic-openapi-validator-spectral is installed
        validator = OpenAPIValidator(["default", "spectral"])
        assert len(validator.strategies) == 2

        # Verify the strategy types
        strategy_names = [type(s).__name__ for s in validator.strategies]
        assert "DefaultOpenAPIValidator" in strategy_names
        assert "SpectralValidator" in strategy_names

    except ValueError as e:
        if "No validator plugin named 'spectral' found" in str(e):
            pytest.skip(
                "jentic-openapi-validator-spectral not installed - skipping integration test"
            )
        else:
            raise


@pytest.mark.skipif(
    subprocess.run(["spectral", "--version"], capture_output=True).returncode != 0,
    reason="Spectral CLI not available",
)
def test_spectral_validation_integration(sample_openapi_file):
    """Test that spectral validation works end-to-end as a user would experience it."""
    try:
        # Test the exact usage pattern from your example
        validator = OpenAPIValidator(["default", "spectral"])
        result = validator.validate(sample_openapi_file)

        # The validation should complete without errors
        # (though it might have warnings/info from spectral)
        assert result is not None
        assert hasattr(result, "diagnostics")

        # If spectral CLI is not available, the spectral strategy should
        # return an appropriate error message
        spectral_diagnostics = [
            d
            for d in result.diagnostics
            if hasattr(d, "source") and "spectral" in str(d.source).lower()
        ]

        print(f"Total diagnostics: {len(spectral_diagnostics)}")
        for diag in result.diagnostics:
            print(
                f"  - {getattr(diag, 'severity', 'unknown')}: {getattr(diag, 'message', str(diag))}"
            )

    except ValueError as e:
        if "No validator plugin named 'spectral' found" in str(e):
            pytest.skip(
                "jentic-openapi-validator-spectral not installed - skipping integration test"
            )
        else:
            raise


@pytest.mark.skipif(
    subprocess.run(["spectral", "--version"], capture_output=True).returncode != 0,
    reason="Spectral CLI not available",
)
def test_spectral_only_strategy(sample_openapi_file):
    """Test using only the spectral strategy."""
    try:
        validator = OpenAPIValidator(["spectral"])
        result = validator.validate(sample_openapi_file)

        assert result is not None
        assert len(validator.strategies) == 1
        assert type(validator.strategies[0]).__name__ == "SpectralValidator"

    except ValueError as e:
        if "No validator plugin named 'spectral' found" in str(e):
            pytest.skip(
                "jentic-openapi-validator-spectral not installed - skipping integration test"
            )
        else:
            raise


@pytest.mark.skipif(
    subprocess.run(["spectral", "--version"], capture_output=True).returncode != 0,
    reason="Spectral CLI not available",
)
def test_invalid_strategy_name():
    """Test that invalid strategy names raise appropriate errors."""
    with pytest.raises(ValueError, match="No validator plugin named 'nonexistent' found"):
        OpenAPIValidator(["nonexistent"])


@pytest.mark.skipif(
    subprocess.run(["spectral", "--version"], capture_output=True).returncode != 0,
    reason="Spectral CLI not available",
)
def test_spectral_with_real_cli(sample_openapi_file):
    """Test spectral integration when the actual spectral CLI is available."""
    try:
        validator = OpenAPIValidator(["spectral"])
        result = validator.validate(sample_openapi_file)

        # With real spectral CLI, we should get actual validation results
        assert result is not None
        print(f"Spectral found {len(result.diagnostics)} issues")

    except ValueError as e:
        if "No validator plugin named 'spectral' found" in str(e):
            pytest.skip("jentic-openapi-validator-spectral not installed")
        else:
            raise
