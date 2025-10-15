"""Pytest configuration and fixtures for jentic-openapi-transformer tests."""

import subprocess
import threading
import time
from http.client import HTTPConnection
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from typing import Any

import pytest

from jentic.apitools.openapi.parser.core import OpenAPIParser, load_uri
from jentic.apitools.openapi.transformer.bundler.core import OpenAPIBundler


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

        class Handler(SimpleHTTPRequestHandler):
            def __init__(handler_self, *args, **kwargs):
                super().__init__(*args, directory=str(self.fixtures_dir), **kwargs)

            def log_message(handler_self, format, *args):  # noqa: A002
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


@pytest.fixture
def openapi_fixtures_dir(fixtures_dir: Path) -> Path:
    """Return the path to the OpenAPI test fixtures directory."""
    return fixtures_dir / "openapi"


@pytest.fixture(scope="module")
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
def root_simple_doc(references_fixtures_dir: Path) -> Any:
    """Load and parse the root-simple.json document.

    This fixture is not cached (scope=function by default) so each test
    gets a fresh copy to modify without affecting other tests.
    """
    spec_file = references_fixtures_dir / "root-simple.json"
    spec_text = load_uri(spec_file.as_uri(), 300, 300)
    return OpenAPIParser().parse(spec_text)


@pytest.fixture
def root_complex_doc(references_fixtures_dir: Path) -> Any:
    """Load and parse the root-complex.json document.

    This fixture is not cached (scope=function by default) so each test
    gets a fresh copy to modify without affecting other tests.
    """
    spec_file = references_fixtures_dir / "root-complex.json"
    spec_text = load_uri(spec_file.as_uri(), 300, 300)
    return OpenAPIParser().parse(spec_text)


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
