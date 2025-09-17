from pathlib import Path
from jentic_openapi_transformer import OpenAPIBundler

# Get the fixtures directory
FIXTURES_DIR = Path(__file__).parent / "fixtures" / "openapi"


def test_bundle_json_url_return_str():
    spec_file = FIXTURES_DIR / "simple_openapi.json"
    spec_uri = spec_file.as_uri()

    bundler = OpenAPIBundler()
    doc = bundler.bundle(spec_uri, return_type=str)
    assert isinstance(doc, str)


def test_bundle_json_url_return_dict():
    spec_file = FIXTURES_DIR / "simple_openapi.json"
    spec_uri = spec_file.as_uri()

    bundler = OpenAPIBundler()
    doc = bundler.bundle(spec_uri, return_type=dict)
    assert isinstance(doc, dict)
    assert doc["openapi"] == "3.1.0"
    assert doc["info"]["title"] == "Test API"


def test_parse_json_string():
    bundler = OpenAPIBundler()
    doc = bundler.bundle(
        '{"openapi":"3.1.0","info":{"title":"x","version":"1.0.0"}}', return_type=dict
    )
    assert doc["openapi"] == "3.1.0"
    assert doc["info"]["title"] == "x"


def test_parse_default_strategy():
    """Test that the strategy mechanism works."""
    bundler = OpenAPIBundler(["default"])
    assert len(bundler.strategies) == 1

    # Verify the strategy types
    strategy_names = [type(s).__name__ for s in bundler.strategies]
    assert "DefaultOpenAPIBundler" in strategy_names
    doc = bundler.bundle(
        '{"openapi":"3.1.0","info":{"title":"x","version":"1.0.0"}}', return_type=dict
    )
    assert doc["openapi"] == "3.1.0"
    assert doc["info"]["title"] == "x"
