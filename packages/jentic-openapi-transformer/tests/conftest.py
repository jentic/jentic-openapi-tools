"""Pytest configuration and fixtures for jentic-openapi-transformer tests."""

import subprocess
from pathlib import Path
from typing import Any

import pytest

from jentic.apitools.openapi.parser.core import OpenAPIParser, load_uri
from jentic.apitools.openapi.transformer.bundler.core import OpenAPIBundler


@pytest.fixture
def fixtures_dir() -> Path:
    """Return the path to the test fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def openapi_fixtures_dir(fixtures_dir: Path) -> Path:
    """Return the path to the OpenAPI test fixtures directory."""
    return fixtures_dir / "openapi"


@pytest.fixture
def references_fixtures_dir(fixtures_dir: Path) -> Path:
    """Return the path to the references test fixtures directory."""
    return fixtures_dir / "references"


@pytest.fixture
def openapi_bundler() -> OpenAPIBundler:
    """Return a default OpenAPIBundler instance."""
    return OpenAPIBundler()


@pytest.fixture
def openapi_bundler_with_default_backend() -> OpenAPIBundler:
    """Return an OpenAPIBundler instance with explicit default backend."""
    return OpenAPIBundler("default")


@pytest.fixture
def simple_openapi_path(openapi_fixtures_dir: Path) -> Path:
    """Return path to a simple OpenAPI document."""
    return openapi_fixtures_dir / "simple_openapi.json"


@pytest.fixture
def simple_openapi_uri(simple_openapi_path: Path) -> str:
    """Return URI to a simple OpenAPI document."""
    return simple_openapi_path.as_uri()


@pytest.fixture
def root_relative_refs_path(references_fixtures_dir: Path) -> Path:
    """Return path to root-relative-refs.json fixture."""
    return references_fixtures_dir / "root-relative-refs.json"


@pytest.fixture
def root_relative_refs_uri(root_relative_refs_path: Path) -> str:
    """Return URI to root-relative-refs.json fixture."""
    return root_relative_refs_path.as_uri()


@pytest.fixture
def root_relative_refs_doc(root_relative_refs_uri: str) -> Any:
    """Load and parse the root-relative-refs.json document.

    This fixture is not cached (scope=function by default) so each test
    gets a fresh copy to modify without affecting other tests.
    """
    spec_text = load_uri(root_relative_refs_uri, 300, 300)
    return OpenAPIParser().parse(spec_text)


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
def redocly_cli_available() -> bool:
    """Check if Redocly CLI is available on the system."""
    try:
        result = subprocess.run(
            ["npx", "--yes", "@redocly/cli@^2.4.0", "--version"], capture_output=True, timeout=10
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
                ["npx", "--yes", "@redocly/cli@^2.4.0", "--version"],
                capture_output=True,
                timeout=10,
            )
            if result.returncode != 0:
                pytest.skip("Redocly CLI not available")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pytest.skip("Redocly CLI not available")
