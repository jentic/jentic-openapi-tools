from pathlib import Path

from jentic_openapi_parser import OpenAPIParser

# Get the fixtures directory
FIXTURES_DIR = Path(__file__).parent / "fixtures" / "openapi"


def test_parse_json_url():
    spec_file = FIXTURES_DIR / "simple_openapi.json"
    spec_uri = spec_file.as_uri()

    parser = OpenAPIParser()
    doc = parser.parse(spec_uri)
    assert doc["openapi"] == "3.1.0"
    assert doc["info"]["title"] == "Test API"


def test_parse_json_string():
    parser = OpenAPIParser()
    doc = parser.parse('{"openapi":"3.1.0","info":{"title":"x","version":"1.0.0"}}')
    assert doc["openapi"] == "3.1.0"
    assert doc["info"]["title"] == "x"
