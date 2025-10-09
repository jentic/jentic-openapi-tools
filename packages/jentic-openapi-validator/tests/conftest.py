"""Pytest configuration and fixtures for jentic-openapi-validator tests."""

import subprocess
from pathlib import Path

import pytest

from jentic.apitools.openapi.validator.core import OpenAPIValidator


@pytest.fixture
def fixtures_dir() -> Path:
    """Path to the test fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def openapi_fixtures_dir(fixtures_dir: Path) -> Path:
    """Path to the OpenAPI test fixtures directory."""
    return fixtures_dir / "openapi"


@pytest.fixture
def validator() -> OpenAPIValidator:
    """A default OpenAPIValidator instance."""
    return OpenAPIValidator()


@pytest.fixture
def validator_with_spectral() -> OpenAPIValidator:
    """An OpenAPIValidator instance with spectral backend."""
    return OpenAPIValidator(backends=["spectral"])


@pytest.fixture
def valid_openapi_path(openapi_fixtures_dir: Path) -> Path:
    """Path to a valid OpenAPI document fixture."""
    return openapi_fixtures_dir / "valid_openapi.json"


@pytest.fixture
def invalid_openapi_path(openapi_fixtures_dir: Path) -> Path:
    """Path to an invalid OpenAPI document fixture."""
    return openapi_fixtures_dir / "invalid_openapi.json"


@pytest.fixture
def valid_openapi_string() -> str:
    """A valid OpenAPI document as JSON string."""
    return '{"openapi":"3.1.0","info":{"title":"Test API","version":"1.0.0"},"paths":{}}'


@pytest.fixture
def invalid_openapi_string() -> str:
    """An invalid OpenAPI document as JSON string (missing paths)."""
    return '{"openapi":"3.1.0","info":{"title":"Test API","version":"1.0.0"}}'


@pytest.fixture
def valid_openapi_dict() -> dict:
    """A valid OpenAPI document as dictionary."""
    return {"openapi": "3.1.0", "info": {"title": "Test API", "version": "1.0.0"}, "paths": {}}


@pytest.fixture
def invalid_openapi_dict() -> dict:
    """An invalid OpenAPI document as dictionary (missing paths)."""
    return {"openapi": "3.1.0", "info": {"title": "Test API", "version": "1.0.0"}}


@pytest.fixture
def sample_openapi_yaml(tmp_path: Path) -> Path:
    """Create a temporary OpenAPI YAML file for testing."""
    openapi_content = """openapi: 3.1.0
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
                  type: object"""
    openapi_file = tmp_path / "test_api.yaml"
    openapi_file.write_text(openapi_content)
    return openapi_file


@pytest.fixture
def spectral_cli_available() -> bool:
    """Check if Spectral CLI is available on the system."""
    try:
        result = subprocess.run(
            ["npx", "--yes", "@stoplight/spectral-cli@^6.15.0", "--version"],
            capture_output=True,
            timeout=10,
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line(
        "markers", "requires_spectral_cli: mark test as requiring Spectral CLI to be available"
    )
    config.addinivalue_line(
        "markers", "requires_redocly_cli: mark test as requiring Redocly CLI to be available"
    )


def pytest_runtest_setup(item):
    """Skip tests that require Spectral or Redocly CLI when they're not available."""
    if item.get_closest_marker("requires_spectral_cli"):
        try:
            result = subprocess.run(
                ["npx", "--yes", "@stoplight/spectral-cli@^6.15.0", "--version"],
                capture_output=True,
                timeout=10,
            )
            if result.returncode != 0:
                pytest.skip("Spectral CLI not available")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pytest.skip("Spectral CLI not available")

    if item.get_closest_marker("requires_redocly_cli"):
        try:
            result = subprocess.run(
                ["npx", "--yes", "@redocly/cli@2.4.0", "--version"],
                capture_output=True,
                timeout=10,
            )
            if result.returncode != 0:
                pytest.skip("Redocly CLI not available")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pytest.skip("Redocly CLI not available")
