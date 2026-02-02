"""Pytest configuration and fixtures for jentic-openapi-validator tests."""

import subprocess
import threading
import time
from http.client import HTTPConnection
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

import pytest

from jentic.apitools.openapi.validator.core import OpenAPIValidator


class HTTPTestServer:
    """Simple HTTP server for testing HTTP URL loading."""

    def __init__(self, fixtures_dir: Path, port: int = 0):
        self.fixtures_dir = fixtures_dir
        self.port = port
        self.server = None
        self.thread = None
        self.base_url = None

    def start(self):
        """Start the HTTP server in a background thread."""
        # Change to fixtures directory to serve files
        self.fixtures_dir.mkdir(parents=True, exist_ok=True)
        # Capture directory path as string for closure in Handler class
        directory = str(self.fixtures_dir)

        class Handler(SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=directory, **kwargs)

            def log_message(self, format, *args):  # noqa: A002
                # Suppress log messages
                pass

        self.server = HTTPServer(("localhost", self.port), Handler)
        self.port = self.server.server_port
        self.base_url = f"http://localhost:{self.port}"

        def run_server():
            assert self.server
            self.server.serve_forever()

        self.thread = threading.Thread(target=run_server, daemon=True)
        self.thread.start()

        # Poll server until it's ready (max 5 retries with 0.1s intervals)
        retries = 5
        while retries > 0:
            try:
                conn = HTTPConnection(f"localhost:{self.port}")
                conn.request("HEAD", "/")
                response = conn.getresponse()
                if response is not None:
                    conn.close()
                    return  # Server is ready
            except (ConnectionRefusedError, OSError):
                time.sleep(0.1)
                retries -= 1

        # If we get here, server failed to start
        raise RuntimeError(f"HTTP server failed to start on port {self.port}")

    def stop(self):
        """Stop the HTTP server."""
        if self.server:
            self.server.shutdown()
            self.server.server_close()
        if self.thread:
            self.thread.join(timeout=1)


@pytest.fixture(scope="module")
def fixtures_dir() -> Path:
    """Return the path to the test fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture(scope="module")
def references_fixtures_dir(fixtures_dir: Path) -> Path:
    """Return the path to the OpenAPI references test fixtures directory."""
    return fixtures_dir / "openapi" / "references"


@pytest.fixture(scope="module")
def http_server(references_fixtures_dir: Path):
    """Fixture providing an HTTP server for testing.

    The server serves files from the references fixtures directory.
    Uses module scope for performance - server is shared across all tests in a module.
    """
    server = HTTPTestServer(fixtures_dir=references_fixtures_dir)
    server.start()
    yield server
    server.stop()


@pytest.fixture
def validator() -> OpenAPIValidator:
    """A default OpenAPIValidator instance."""
    return OpenAPIValidator()


@pytest.fixture
def valid_openapi_string() -> str:
    """A valid OpenAPI document as JSON string."""
    return '{"openapi":"3.1.0","info":{"title":"Test API","version":"1.0.0"},"paths":{},"servers":[{"url":"https://api.example.com"}]}'


@pytest.fixture
def invalid_openapi_string() -> str:
    """An invalid OpenAPI document as JSON string (missing paths)."""
    return '{"openapi":"3.1.0","info":{"title":"Test API","version":"1.0.0"}}'


@pytest.fixture
def valid_openapi_dict() -> dict:
    """A valid OpenAPI document as dictionary."""
    return {
        "openapi": "3.1.0",
        "info": {"title": "Test API", "version": "1.0.0"},
        "paths": {},
        "servers": [{"url": "https://api.example.com"}],
    }


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
            ["npx", "--yes", "@stoplight/spectral-cli@6.15.0", "--version"],
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
                ["npx", "--yes", "@stoplight/spectral-cli@6.15.0", "--version"],
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
                ["npx", "--yes", "@redocly/cli@2.15.1", "--version"],
                capture_output=True,
                timeout=10,
            )
            if result.returncode != 0:
                pytest.skip("Redocly CLI not available")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pytest.skip("Redocly CLI not available")
