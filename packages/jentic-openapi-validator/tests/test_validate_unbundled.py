import tempfile
import threading
import time
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urljoin, urlparse
from urllib.request import url2pathname

import pytest

from jentic_openapi_parser import OpenAPIParser, load_uri
from jentic_openapi_validator import OpenAPIValidator

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

            def log_message(self, format, *args):
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

        # Give server time to start
        time.sleep(0.1)

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


class TestValidateUnbundled:
    def test_validate_unbundled_http_relative_existing(self, http_server):
        """Test validating unbundled document."""
        # validate passing Http URL

        spec_url = urljoin(http_server.base_url, "root-relative-refs-no-info-valid.json")
        spec_text = load_uri(spec_url, 300, 300)
        OpenAPIParser().parse(spec_text)

        # default
        validator = OpenAPIValidator(["default"])
        res = validator.validate(spec_url, base_url=spec_url)
        print(f"(default) valid: {res.valid}")
        for d in res.diagnostics:
            print(f"(default) {d.code}: {d.message}")
        assert not res.valid
        assert len(res.diagnostics) == 1

        # spectral
        validator = OpenAPIValidator(["spectral"])
        res = validator.validate(spec_url, base_url=spec_url)
        print(f"(spectral) valid: {res.valid}")
        for d in res.diagnostics:
            print(f"(spectral) {d.code}: {d.message}")
        assert not res.valid
        assert len(res.diagnostics) == 3

        # redocly
        validator = OpenAPIValidator(["redocly"])
        res = validator.validate(spec_url, base_url=spec_url)
        print(f"(redocly) valid: {res.valid}")
        for d in res.diagnostics:
            print(f"(redocly) {d.code}: {d.message}")
        assert not res.valid
        assert len(res.diagnostics) == 4

        # openapi-spec-validator
        # assert openapi-spec-validator not capable of validating relative URLs without base_uri
        validator = OpenAPIValidator(["openapi-spec-validator"])
        res = validator.validate(spec_url)
        print(f"(openapi-spec-validator) valid: {res.valid}")
        for d in res.diagnostics:
            print(f"(openapi-spec-validator) {d.code}: {d.message}")
        assert not res.valid
        assert len(res.diagnostics) == 1
        assert res.diagnostics[0].code == "openapi-spec-validator-error"

        # assert openapi-spec-validator capable of validating relative URLs with base_uri
        spec_url_invalid = urljoin(
            http_server.base_url, "root-relative-refs-no-info-valid-and-errors.json"
        )
        validator = OpenAPIValidator(["openapi-spec-validator"])
        res = validator.validate(spec_url_invalid, base_url=spec_url_invalid)
        print(f"(openapi-spec-validator base_url) valid: {res.valid}")
        for d in res.diagnostics:
            print(f"(openapi-spec-validator base_url) {d.code}: {d.message}")
        assert not res.valid
        assert len(res.diagnostics) == 1
        assert res.diagnostics[0].code == "type"

    def test_validate_unbundled_http_relative_non_existing(self, http_server):
        """Test validating unbundled document."""
        # validate passing Http URL
        spec_url = urljoin(http_server.base_url, "root-invalid-relative-refs-no-info-valid.json")
        spec_text = load_uri(spec_url, 300, 300)
        OpenAPIParser().parse(spec_text)

        # default
        validator = OpenAPIValidator(["default"])
        res = validator.validate(spec_url, base_url=spec_url)
        print(f"(default) valid: {res.valid}")
        for d in res.diagnostics:
            print(f"(default) {d.code}: {d.message}")
        assert not res.valid
        assert len(res.diagnostics) == 1

        # spectral
        validator = OpenAPIValidator(["spectral"])
        res = validator.validate(spec_url, base_url=spec_url)
        print(f"(spectral) valid: {res.valid}")
        for d in res.diagnostics:
            print(f"(spectral) {d.code}: {d.message}")
        assert not res.valid
        assert len(res.diagnostics) == 12

        # redocly
        validator = OpenAPIValidator(["redocly"])
        res = validator.validate(spec_url, base_url=spec_url)
        print(f"(redocly) valid: {res.valid}")
        for d in res.diagnostics:
            print(f"(redocly) {d.code}: {d.message}")
        assert not res.valid
        assert len(res.diagnostics) == 80

        # openapi-spec-validator
        # assert openapi-spec-validator not capable of validating relative URLs without base_uri
        validator = OpenAPIValidator(["openapi-spec-validator"])
        res = validator.validate(spec_url)
        print(f"(openapi-spec-validator) valid: {res.valid}")
        for d in res.diagnostics:
            print(f"(openapi-spec-validator) {d.code}: {d.message}")
        assert not res.valid
        assert len(res.diagnostics) == 1
        for d in res.diagnostics:
            print(f"{d.code}: {d.message}")
        assert res.diagnostics[0].code == "openapi-spec-validator-error"

        # assert openapi-spec-validator NOT capable of validating invalid relative URLs with base_uri
        validator = OpenAPIValidator(["openapi-spec-validator"])
        res = validator.validate(spec_url, base_url=spec_url)
        print(f"(openapi-spec-validator base_url) valid: {res.valid}")
        for d in res.diagnostics:
            print(f"(openapi-spec-validator base_url) {d.code}: {d.message}")
        assert not res.valid
        assert len(res.diagnostics) == 1
        for d in res.diagnostics:
            print(f"{d.code}: {d.message}")
        assert res.diagnostics[0].code == "openapi-spec-validator-error"

    def test_validate_unbundled_file_http_relative_existing_with_baseurl(self, http_server):
        """Test validating unbundled document."""
        # validate passing file URL
        spec_url = urljoin(http_server.base_url, "root-relative-refs-no-info-valid.json")
        spec_text = load_uri(spec_url, 300, 300)

        OpenAPIParser().parse(spec_text)

        spec_file_path = None
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".spec.json", delete=False, encoding="utf-8"
        ) as temp_file:
            temp_file.write(spec_text)
            parsed = urlparse(temp_file.name)
            spec_file_path = url2pathname(parsed.path)

        # default
        validator = OpenAPIValidator(["default"])
        res = validator.validate(spec_file_path, base_url=spec_url)
        print(f"(default) valid: {res.valid}")
        for d in res.diagnostics:
            print(f"(default) {d.code}: {d.message}")
        assert not res.valid
        assert len(res.diagnostics) == 1

        # spectral
        validator = OpenAPIValidator(["spectral"])
        res = validator.validate(spec_file_path, base_url=spec_url)
        print(f"(spectral) valid: {res.valid}")
        for d in res.diagnostics:
            print(f"(spectral) {d.code}: {d.message}")
        assert not res.valid
        assert len(res.diagnostics) == 12
        assert any(diag.code == "invalid-ref" for diag in res.diagnostics)

        # redocly
        validator = OpenAPIValidator(["redocly"])
        res = validator.validate(spec_file_path, base_url=spec_url)
        print(f"(redocly) valid: {res.valid}")
        for d in res.diagnostics:
            print(f"(redocly) {d.code}: {d.message}")
        assert not res.valid
        assert len(res.diagnostics) == 80
        assert any(diag.code == "no-unresolved-refs" for diag in res.diagnostics)

        # assert openapi-spec-validator capable of validating relative URLs with base_uri
        validator = OpenAPIValidator(["openapi-spec-validator"])
        res = validator.validate(spec_file_path, base_url=spec_url)
        print(f"(openapi-spec-validator base_url) valid: {res.valid}")
        for d in res.diagnostics:
            print(f"(openapi-spec-validator base_url) {d.code}: {d.message}")
        assert res.valid

    # validate passing text

    # validate passing dict
