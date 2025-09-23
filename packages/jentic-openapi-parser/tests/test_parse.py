from pathlib import Path

from jentic.apitools.openapi.parser.core import OpenAPIParser
from ruamel.yaml import CommentedMap

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


def test_parse_default_strategy():
    """Test that the strategy mechanism works."""
    parser = OpenAPIParser("default")
    # Verify the strategy types
    strategy_name = type(parser.strategy).__name__
    assert strategy_name == "DefaultOpenAPIParser"
    doc = parser.parse('{"openapi":"3.1.0","info":{"title":"x","version":"1.0.0"}}')
    assert doc["openapi"] == "3.1.0"
    assert doc["info"]["title"] == "x"


def test_parse_ruamel_strategy():
    """Test ruamel parser."""
    parser = OpenAPIParser("ruamel")
    strategy_name = type(parser.strategy).__name__
    assert strategy_name == "RuamelOpenAPIParser"

    doc = parser.parse('{"openapi":"3.1.0","info":{"title":"x","version":"1.0.0"}}')
    assert doc["openapi"] == "3.1.0"
    assert doc["info"]["title"] == "x"
    assert not hasattr(doc, "lc")  # ruamel safe doesn't keep line/col info


def test_parse_ruamel_roundtrip_strategy():
    """Test ruamel-rt parser."""
    parser = OpenAPIParser("ruamel-rt")
    strategy_name = type(parser.strategy).__name__
    assert strategy_name == "RuamelRoundTripOpenAPIParser"

    doc = parser.parse(
        '{"openapi":"3.1.0","info":{"title":"x","version":"1.0.0"}}', return_type=CommentedMap
    )
    assert doc["openapi"] == "3.1.0"
    assert doc["info"]["title"] == "x"
    assert hasattr(doc, "lc")  # ruamel roundtrip keeps line/col info
