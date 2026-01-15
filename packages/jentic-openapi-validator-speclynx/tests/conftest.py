"""Pytest configuration and fixtures for jentic-openapi-validator-speclynx tests."""

import subprocess
from pathlib import Path

import pytest

from jentic.apitools.openapi.validator.backends.speclynx import SpeclynxValidatorBackend


@pytest.fixture
def fixtures_dir() -> Path:
    """Path to the test fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def openapi_fixtures_dir(fixtures_dir: Path) -> Path:
    """Path to the OpenAPI test fixtures directory."""
    return fixtures_dir / "openapi"


@pytest.fixture
def valid_openapi_path(openapi_fixtures_dir: Path) -> Path:
    """Path to a valid OpenAPI document fixture."""
    return openapi_fixtures_dir / "simple_openapi.json"


@pytest.fixture
def invalid_openapi_path(openapi_fixtures_dir: Path) -> Path:
    """Path to an invalid OpenAPI document fixture."""
    return openapi_fixtures_dir / "simple_openapi_invalid.json"


@pytest.fixture
def swagger_2_0_path(openapi_fixtures_dir: Path) -> Path:
    """Path to a Swagger 2.0 document fixture."""
    return openapi_fixtures_dir / "swagger_2_0.json"


@pytest.fixture
def plugins_dir(fixtures_dir: Path) -> Path:
    """Path to the test plugins directory."""
    return fixtures_dir / "plugins"


@pytest.fixture
def speclynx_validator() -> SpeclynxValidatorBackend:
    """A default ApidomValidator instance."""
    return SpeclynxValidatorBackend()


@pytest.fixture
def speclynx_validator_with_short_timeout() -> SpeclynxValidatorBackend:
    """An ApidomValidator instance with a short timeout for testing."""
    return SpeclynxValidatorBackend(timeout=1.0)


@pytest.fixture
def speclynx_validator_with_long_timeout() -> SpeclynxValidatorBackend:
    """An ApidomValidator instance with a long timeout."""
    return SpeclynxValidatorBackend(timeout=120.0)


@pytest.fixture
def speclynx_validator_with_plugins(plugins_dir: Path) -> SpeclynxValidatorBackend:
    """A SpeclynxValidator instance with test plugins enabled."""
    return SpeclynxValidatorBackend(plugins_dir=plugins_dir)


def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line(
        "markers", "requires_speclynx_cli: mark test as requiring ApiDOM CLI to be available"
    )


def _is_node_available() -> bool:
    """Check if Node.js is available."""
    try:
        result = subprocess.run(
            ["node", "--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return result.returncode == 0
    except (subprocess.SubprocessError, FileNotFoundError):
        return False


def pytest_runtest_setup(item):
    """Skip tests that require ApiDOM CLI when it's not available."""
    if item.get_closest_marker("requires_speclynx_cli"):
        if not _is_node_available():
            pytest.skip("Node.js is not available")
