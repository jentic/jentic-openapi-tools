import subprocess
import pytest
from jentic_openapi_transformer import OpenAPIBundler


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


def test_redocly_plugin_discovery():
    """Test that the redocly plugin can be discovered via entry points."""
    try:
        # This should work if jentic-openapi-bundler-redocly is installed
        bundler = OpenAPIBundler("redocly")
        # Verify the strategy types
        strategy_name = type(bundler.strategy).__name__
        assert strategy_name == "RedoclyBundler"

    except ValueError as e:
        if "No bundler plugin named 'redocly' found" in str(e):
            pytest.skip("jentic-openapi-bundler-redocly not installed - skipping integration test")
        else:
            raise


@pytest.mark.skipif(
    subprocess.run(["npx", "@redocly/cli@^2.1.5", "--version"], capture_output=True).returncode
    != 0,
    reason="Redocly CLI not available",
)
def test_redocly_only_strategy(sample_openapi_file):
    """Test using only the redocly strategy."""
    try:
        bundler = OpenAPIBundler("redocly")
        result = bundler.bundle(sample_openapi_file, return_type=str)

        # With real redocly CLI, we should get actual validation results
        assert result is not None and isinstance(result, str) and len(result) > 0

        assert type(bundler.strategy).__name__ == "RedoclyBundler"

    except ValueError as e:
        if "No bundler plugin named 'redocly' found" in str(e):
            pytest.skip("jentic-openapi-bundler-redocly not installed - skipping integration test")
        else:
            raise


@pytest.mark.skipif(
    subprocess.run(["npx", "@redocly/cli@^2.1.5", "--version"], capture_output=True).returncode
    != 0,
    reason="Redocly CLI not available",
)
def test_invalid_strategy_name():
    """Test that invalid strategy names raise appropriate errors."""
    with pytest.raises(ValueError, match="No bundler plugin named 'nonexistent' found"):
        OpenAPIBundler("nonexistent")


@pytest.mark.skipif(
    subprocess.run(["npx", "@redocly/cli@^2.1.5", "--version"], capture_output=True).returncode
    != 0,
    reason="Redocly CLI not available",
)
def test_redocly_with_real_cli(sample_openapi_file):
    """Test redocly integration when the actual redocly CLI is available."""
    try:
        bundler = OpenAPIBundler("redocly")
        result = bundler.bundle(sample_openapi_file, return_type=str)

        # With real redocly CLI, we should get actual validation results
        assert result is not None and isinstance(result, str) and len(result) > 0

    except ValueError as e:
        if "No bundler plugin named 'redocly' found" in str(e):
            pytest.skip("jentic-openapi-bundler-redocly not installed")
        else:
            raise
