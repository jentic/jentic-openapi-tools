"""Pytest configuration and fixtures for jentic-openapi-transformer-redocly tests."""

import subprocess
from pathlib import Path

import pytest

from jentic.apitools.openapi.transformer.bundler.backends.redocly import RedoclyBundlerBackend


@pytest.fixture
def fixtures_dir() -> Path:
    """Return the path to the test fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def openapi_fixtures_dir(fixtures_dir: Path) -> Path:
    """Return the path to the OpenAPI test fixtures directory."""
    return fixtures_dir / "openapi"


@pytest.fixture
def snapshots_dir(fixtures_dir: Path) -> Path:
    """Return the path to the snapshots directory."""
    return fixtures_dir / "snapshots"


@pytest.fixture
def redocly_bundler() -> RedoclyBundlerBackend:
    """Return a default RedoclyBundler instance."""
    return RedoclyBundlerBackend()


@pytest.fixture
def redocly_bundler_with_custom_timeout() -> RedoclyBundlerBackend:
    """Return a RedoclyBundler instance with custom timeout."""
    return RedoclyBundlerBackend(timeout=60.0)


@pytest.fixture
def redocly_bundler_with_custom_path() -> RedoclyBundlerBackend:
    """Return a RedoclyBundler instance with custom redocly path."""
    return RedoclyBundlerBackend(redocly_path="/custom/path/to/redocly")


@pytest.fixture
def valid_openapi_path(openapi_fixtures_dir: Path) -> Path:
    """Return path to a valid OpenAPI document."""
    return openapi_fixtures_dir / "openapi.yaml"


@pytest.fixture
def valid_openapi_uri(valid_openapi_path: Path) -> str:
    """Return URI to a valid OpenAPI document."""
    return valid_openapi_path.as_uri()


@pytest.fixture
def malformed_openapi_path(openapi_fixtures_dir: Path) -> Path:
    """Return path to a malformed OpenAPI document."""
    return openapi_fixtures_dir / "simple_openapi_not_well_formed.json"


@pytest.fixture
def malformed_openapi_uri(malformed_openapi_path: Path) -> str:
    """Return URI to a malformed OpenAPI document."""
    return malformed_openapi_path.as_uri()


@pytest.fixture
def expected_bundled_content(snapshots_dir: Path) -> str:
    """Return the expected bundled OpenAPI content."""
    return (snapshots_dir / "openapi-bundled.json").read_text(encoding="utf-8")


@pytest.fixture
def redocly_cli_available() -> bool:
    """Check if Redocly CLI is available on the system."""
    try:
        result = subprocess.run(
            ["npx", "@redocly/cli@^2.1.5", "--version"], capture_output=True, timeout=10
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line(
        "markers", "requires_redocly_cli: mark test as requiring Redocly CLI to be available"
    )


def pytest_runtest_setup(item):
    """Skip tests that require Redocly CLI when it's not available."""
    if item.get_closest_marker("requires_redocly_cli"):
        try:
            result = subprocess.run(
                ["npx", "@redocly/cli@^2.1.5", "--version"], capture_output=True, timeout=10
            )
            if result.returncode != 0:
                pytest.skip("Redocly CLI not available")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pytest.skip("Redocly CLI not available")
