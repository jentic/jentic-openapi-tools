def test_bundle_json_url_return_str(openapi_bundler, simple_openapi_uri):
    """Test bundling a JSON OpenAPI document from URI and returning as string."""
    doc = openapi_bundler.bundle(simple_openapi_uri, return_type=str)
    assert isinstance(doc, str)


def test_bundle_json_url_return_dict(openapi_bundler, simple_openapi_uri):
    """Test bundling a JSON OpenAPI document from URI and returning as dict."""
    doc = openapi_bundler.bundle(simple_openapi_uri, return_type=dict)
    assert isinstance(doc, dict)
    assert doc["openapi"] == "3.1.0"
    assert doc["info"]["title"] == "Test API"


def test_parse_json_string(openapi_bundler):
    """Test parsing a JSON string directly."""
    doc = openapi_bundler.bundle(
        '{"openapi":"3.1.0","info":{"title":"x","version":"1.0.0"}}', return_type=dict
    )
    assert doc["openapi"] == "3.1.0"
    assert doc["info"]["title"] == "x"


def test_parse_default_backend(openapi_bundler_with_default_backend):
    """Test that the backend mechanism works with an explicit default backend."""
    # Verify the backend types
    backend_name = type(openapi_bundler_with_default_backend.backend).__name__
    assert backend_name == "DefaultBundlerBackend"
    doc = openapi_bundler_with_default_backend.bundle(
        '{"openapi":"3.1.0","info":{"title":"x","version":"1.0.0"}}', return_type=dict
    )
    assert doc["openapi"] == "3.1.0"
    assert doc["info"]["title"] == "x"


def test_list_backends():
    """Test that list_backends returns available bundler backends."""
    from jentic.apitools.openapi.transformer.bundler.core import OpenAPIBundler

    backends = OpenAPIBundler.list_backends()
    assert isinstance(backends, list)
    assert len(backends) > 0
    assert "default" in backends
