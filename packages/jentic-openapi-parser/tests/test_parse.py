from pathlib import Path

import pytest

from jentic_openapi_parser import OpenAPIParser
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
    parser = OpenAPIParser(["default"])
    assert len(parser.strategies) == 1

    # Verify the strategy types
    strategy_names = [type(s).__name__ for s in parser.strategies]
    assert "DefaultOpenAPIParser" in strategy_names
    doc = parser.parse('{"openapi":"3.1.0","info":{"title":"x","version":"1.0.0"}}')
    assert doc["openapi"] == "3.1.0"
    assert doc["info"]["title"] == "x"


def test_parse_ruamel_strategy():
    """Test ruamel parser."""
    parser = OpenAPIParser(["ruamel"])
    assert len(parser.strategies) == 1
    strategy_names = [type(s).__name__ for s in parser.strategies]
    assert "RuamelOpenAPIParser" in strategy_names

    doc = parser.parse('{"openapi":"3.1.0","info":{"title":"x","version":"1.0.0"}}')
    assert doc["openapi"] == "3.1.0"
    assert doc["info"]["title"] == "x"
    assert not hasattr(doc, "lc")  # ruamel safe doesn't keep line/col info


def test_parse_ruamel_roundtrip_strategy():
    """Test ruamel-rt parser."""
    parser = OpenAPIParser(["ruamel-rt"])
    assert len(parser.strategies) == 1
    strategy_names = [type(s).__name__ for s in parser.strategies]
    assert "RuamelRoundTripOpenAPIParser" in strategy_names

    doc = parser.parse(
        '{"openapi":"3.1.0","info":{"title":"x","version":"1.0.0"}}', return_type=CommentedMap
    )
    assert doc["openapi"] == "3.1.0"
    assert doc["info"]["title"] == "x"
    assert hasattr(doc, "lc")  # ruamel roundtrip keeps line/col info


def test_parse_default_and_ruamel_roundtrip_strategy():
    """Test default and ruamel-rt parser."""
    parser = OpenAPIParser(["default", "ruamel-rt"])
    assert len(parser.strategies) == 2
    strategy_names = [type(s).__name__ for s in parser.strategies]
    assert "DefaultOpenAPIParser" in strategy_names
    assert "RuamelRoundTripOpenAPIParser" in strategy_names

    doc = parser.parse(
        '{"openapi":"3.1.0","info":{"title":"x","version":"1.0.0"}}', return_type=CommentedMap
    )
    assert doc["openapi"] == "3.1.0"
    assert doc["info"]["title"] == "x"
    assert hasattr(doc, "lc")  # ruamel roundtrip keeps line/col info


def test_parse_and_ruamel_roundtrip_and_default_strategy():
    """Test ruamel-rt and default parser."""
    parser = OpenAPIParser(["ruamel-rt", "default"])
    assert len(parser.strategies) == 2
    strategy_names = [type(s).__name__ for s in parser.strategies]
    assert "DefaultOpenAPIParser" in strategy_names
    assert "RuamelRoundTripOpenAPIParser" in strategy_names

    doc = parser.parse(
        '{"openapi":"3.1.0","info":{"title":"x","version":"1.0.0"}}', return_type=CommentedMap
    )
    assert doc["openapi"] == "3.1.0"
    assert doc["info"]["title"] == "x"
    assert not hasattr(doc, "lc")  # default strategy is last and returns a dict

    with pytest.raises(TypeError):
        doc = parser.parse(
            '{"openapi":"3.1.0","info":{"title":"x","version":"1.0.0"}}',
            return_type=CommentedMap,
            strict=True,
        )
