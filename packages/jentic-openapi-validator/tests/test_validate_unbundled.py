"""Tests for validating unbundled OpenAPI documents with external references."""

import tempfile
import threading
import time
from http.client import HTTPConnection
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urljoin, urlparse
from urllib.request import url2pathname

import pytest

from jentic.apitools.openapi.parser.core import OpenAPIParser, load_uri
from jentic.apitools.openapi.validator.core import OpenAPIValidator


FIXTURES_DIR = Path(__file__).parent / "fixtures" / "openapi" / "references"


class HTTPTestServer:
    """Simple HTTP server for testing HTTP URL loading."""

    def __init__(self, port: int = 0):
        self.port = port
        self.server = None
        self.thread = None
        self.base_url = None

    def start(self):
        """Start the HTTP server in a background thread."""
        # Change to fixtures directory to serve files
        fixtures_dir = FIXTURES_DIR
        fixtures_dir.mkdir(parents=True, exist_ok=True)

        class Handler(SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=str(fixtures_dir), **kwargs)

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
def http_server():
    """Fixture providing an HTTP server for testing."""
    server = HTTPTestServer()
    server.start()
    yield server
    server.stop()


def _print_diagnostics(backend_name: str, result):
    """Helper to print validation results for debugging."""
    print(f"({backend_name}) valid: {result.valid}")
    for d in result.diagnostics:
        print(f"({backend_name}) {d.code}: {d.message}")


class TestValidateUnbundledDefault:
    """Tests for default backend with unbundled documents."""

    def test_validate_unbundled_http_relative_existing_default(self, http_server):
        """Test default backend with HTTP URL and existing relative references."""
        spec_url = urljoin(http_server.base_url, "root-relative-refs-no-info-valid.json")
        spec_text = load_uri(spec_url, 300, 300)
        OpenAPIParser().parse(spec_text)

        # Default backend validates document structure but doesn't validate external references
        validator = OpenAPIValidator(backends=["default"])
        result = validator.validate(spec_url, base_url=spec_url)
        _print_diagnostics("default", result)
        assert result.valid  # Default backend only checks structure, not external refs

    def test_validate_unbundled_http_relative_non_existing_default(self, http_server):
        """Test default backend with HTTP URL and non-existing relative references."""
        spec_url = urljoin(http_server.base_url, "root-invalid-relative-refs-no-info-valid.json")
        spec_text = load_uri(spec_url, 300, 300)
        OpenAPIParser().parse(spec_text)

        # Default backend validates document structure but doesn't validate external references
        validator = OpenAPIValidator(backends=["default"])
        result = validator.validate(spec_url, base_url=spec_url)
        _print_diagnostics("default", result)
        assert result.valid  # Default backend only checks structure, not external refs

    def test_validate_unbundled_file_http_relative_existing_with_baseurl_default(self, http_server):
        """Test default backend with file and HTTP base URL."""
        spec_url = urljoin(http_server.base_url, "root-relative-refs-no-info-valid.json")
        spec_text = load_uri(spec_url, 300, 300)
        OpenAPIParser().parse(spec_text)

        # Write spec to temporary file
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".spec.json", delete=False, encoding="utf-8"
        ) as temp_file:
            temp_file.write(spec_text)
            parsed = urlparse(temp_file.name)
            spec_file_path = url2pathname(parsed.path)

        # Default backend validates document structure but doesn't validate external references
        validator = OpenAPIValidator(backends=["default"])
        result = validator.validate(spec_file_path, base_url=spec_url)
        _print_diagnostics("default", result)
        assert result.valid  # Default backend only checks structure, not external refs


@pytest.mark.requires_spectral_cli
class TestValidateUnbundledSpectral:
    """Tests for spectral backend with unbundled documents."""

    def test_validate_unbundled_http_relative_existing_spectral(self, http_server):
        """Test spectral backend with HTTP URL and existing relative references."""
        spec_url = urljoin(http_server.base_url, "root-relative-refs-no-info-valid.json")
        spec_text = load_uri(spec_url, 300, 300)
        OpenAPIParser().parse(spec_text)

        validator = OpenAPIValidator(backends=["spectral"])
        result = validator.validate(spec_url, base_url=spec_url)
        _print_diagnostics("spectral", result)
        assert not result.valid
        assert len(result.diagnostics) == 3

    def test_validate_unbundled_http_relative_non_existing_spectral(self, http_server):
        """Test spectral backend with HTTP URL and non-existing relative references."""
        spec_url = urljoin(http_server.base_url, "root-invalid-relative-refs-no-info-valid.json")
        spec_text = load_uri(spec_url, 300, 300)
        OpenAPIParser().parse(spec_text)

        validator = OpenAPIValidator(backends=["spectral"])
        result = validator.validate(spec_url, base_url=spec_url)
        _print_diagnostics("spectral", result)
        assert not result.valid
        assert len(result.diagnostics) == 12

    def test_validate_unbundled_file_http_relative_existing_with_baseurl_spectral(
        self, http_server
    ):
        """Test spectral backend with file and HTTP base URL."""
        spec_url = urljoin(http_server.base_url, "root-relative-refs-no-info-valid.json")
        spec_text = load_uri(spec_url, 300, 300)
        OpenAPIParser().parse(spec_text)

        # Write spec to temporary file
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".spec.json", delete=False, encoding="utf-8"
        ) as temp_file:
            temp_file.write(spec_text)
            parsed = urlparse(temp_file.name)
            spec_file_path = url2pathname(parsed.path)

        validator = OpenAPIValidator(backends=["spectral"])
        result = validator.validate(spec_file_path, base_url=spec_url)
        _print_diagnostics("spectral", result)
        assert not result.valid
        assert len(result.diagnostics) == 12
        assert any(diag.code == "invalid-ref" for diag in result.diagnostics)


@pytest.mark.requires_redocly_cli
class TestValidateUnbundledRedocly:
    """Tests for redocly backend with unbundled documents."""

    def test_validate_unbundled_http_relative_existing_redocly(self, http_server):
        """Test redocly backend with HTTP URL and existing relative references."""
        spec_url = urljoin(http_server.base_url, "root-relative-refs-no-info-valid.json")
        spec_text = load_uri(spec_url, 300, 300)
        OpenAPIParser().parse(spec_text)

        validator = OpenAPIValidator(backends=["redocly"])
        result = validator.validate(spec_url, base_url=spec_url)
        _print_diagnostics("redocly", result)
        assert not result.valid
        assert len(result.diagnostics) == 4

    def test_validate_unbundled_http_relative_non_existing_redocly(self, http_server):
        """Test redocly backend with HTTP URL and non-existing relative references."""
        spec_url = urljoin(http_server.base_url, "root-invalid-relative-refs-no-info-valid.json")
        spec_text = load_uri(spec_url, 300, 300)
        OpenAPIParser().parse(spec_text)

        validator = OpenAPIValidator(backends=["redocly"])
        result = validator.validate(spec_url, base_url=spec_url)
        _print_diagnostics("redocly", result)
        assert not result.valid
        assert len(result.diagnostics) == 80

    def test_validate_unbundled_file_http_relative_existing_with_baseurl_redocly(self, http_server):
        """Test redocly backend with file and HTTP base URL."""
        spec_url = urljoin(http_server.base_url, "root-relative-refs-no-info-valid.json")
        spec_text = load_uri(spec_url, 300, 300)
        OpenAPIParser().parse(spec_text)

        # Write spec to temporary file
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".spec.json", delete=False, encoding="utf-8"
        ) as temp_file:
            temp_file.write(spec_text)
            parsed = urlparse(temp_file.name)
            spec_file_path = url2pathname(parsed.path)

        validator = OpenAPIValidator(backends=["redocly"])
        result = validator.validate(spec_file_path, base_url=spec_url)
        _print_diagnostics("redocly", result)
        assert not result.valid
        assert len(result.diagnostics) == 80
        assert any(diag.code == "no-unresolved-refs" for diag in result.diagnostics)


class TestValidateUnbundledOpenAPISpec:
    """Tests for openapi-spec backend with unbundled documents."""

    def test_validate_unbundled_http_without_base_url(self, http_server):
        """Test openapi-spec backend without base_url - should fail to validate relative URLs."""
        spec_url = urljoin(http_server.base_url, "root-relative-refs-no-info-valid.json")
        spec_text = load_uri(spec_url, 300, 300)
        OpenAPIParser().parse(spec_text)

        validator = OpenAPIValidator(backends=["openapi-spec"])
        result = validator.validate(spec_url)
        _print_diagnostics("openapi-spec (no base_url)", result)
        assert not result.valid
        assert len(result.diagnostics) == 1
        assert result.diagnostics[0].code == "openapi-spec-validator-error"

    def test_validate_unbundled_http_with_base_url_and_errors(self, http_server):
        """Test openapi-spec backend with base_url - should detect schema errors."""
        spec_url_with_errors = urljoin(
            http_server.base_url, "root-relative-refs-no-info-valid-and-errors.json"
        )
        validator = OpenAPIValidator(backends=["openapi-spec"])
        result = validator.validate(spec_url_with_errors, base_url=spec_url_with_errors)
        _print_diagnostics("openapi-spec (with base_url)", result)
        assert not result.valid
        assert len(result.diagnostics) == 1
        assert result.diagnostics[0].code == "type"

    def test_validate_unbundled_http_invalid_refs_without_base_url(self, http_server):
        """Test openapi-spec backend with invalid refs and no base_url."""
        spec_url = urljoin(http_server.base_url, "root-invalid-relative-refs-no-info-valid.json")
        spec_text = load_uri(spec_url, 300, 300)
        OpenAPIParser().parse(spec_text)

        validator = OpenAPIValidator(backends=["openapi-spec"])
        result = validator.validate(spec_url)
        _print_diagnostics("openapi-spec (no base_url)", result)
        assert not result.valid
        assert len(result.diagnostics) == 1
        assert result.diagnostics[0].code == "openapi-spec-validator-error"

    def test_validate_unbundled_http_invalid_refs_with_base_url(self, http_server):
        """Test openapi-spec backend with invalid refs and base_url - should still fail."""
        spec_url = urljoin(http_server.base_url, "root-invalid-relative-refs-no-info-valid.json")
        spec_text = load_uri(spec_url, 300, 300)
        OpenAPIParser().parse(spec_text)

        validator = OpenAPIValidator(backends=["openapi-spec"])
        result = validator.validate(spec_url, base_url=spec_url)
        _print_diagnostics("openapi-spec (with base_url)", result)
        assert not result.valid
        assert len(result.diagnostics) == 1
        assert result.diagnostics[0].code == "openapi-spec-validator-error"

    def test_validate_unbundled_file_with_base_url(self, http_server):
        """Test openapi-spec backend with file and HTTP base URL - should be valid."""
        spec_url = urljoin(http_server.base_url, "root-relative-refs-no-info-valid.json")
        spec_text = load_uri(spec_url, 300, 300)
        OpenAPIParser().parse(spec_text)

        # Write spec to temporary file
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".spec.json", delete=False, encoding="utf-8"
        ) as temp_file:
            temp_file.write(spec_text)
            parsed = urlparse(temp_file.name)
            spec_file_path = url2pathname(parsed.path)

        validator = OpenAPIValidator(backends=["openapi-spec"])
        result = validator.validate(spec_file_path, base_url=spec_url)
        _print_diagnostics("openapi-spec (with base_url)", result)
        assert result.valid
