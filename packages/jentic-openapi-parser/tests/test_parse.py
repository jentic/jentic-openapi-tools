"""Tests for OpenAPI parser functionality."""

from pathlib import Path

import pytest
from jentic.apitools.openapi.parser.backends.pyyaml import PyYAMLParserBackend
from jentic.apitools.openapi.parser.core import OpenAPIParser
from jentic.apitools.openapi.parser.core.exceptions import (
    BackendNotFoundError,
    DocumentParseError,
    TypeConversionError,
)
from ruamel.yaml import CommentedMap


def test_parse_json_uri(parser: OpenAPIParser, simple_openapi_uri: str):
    """Test parsing an OpenAPI document from a file URI."""
    doc = parser.parse(simple_openapi_uri)
    assert doc["openapi"] == "3.1.0"
    assert doc["info"]["title"] == "Test API"


def test_parse_json_string(parser: OpenAPIParser, simple_openapi_string: str):
    """Test parsing an OpenAPI document from a JSON string."""
    doc = parser.parse(simple_openapi_string)
    assert doc["openapi"] == "3.1.0"
    assert doc["info"]["title"] == "x"


def test_parse_yaml_string(parser: OpenAPIParser):
    """Test parsing an OpenAPI document from a YAML string."""
    yaml_doc = """
openapi: 3.1.0
info:
  title: YAML API
  version: 1.0.0
"""
    doc = parser.parse(yaml_doc)
    assert doc["openapi"] == "3.1.0"
    assert doc["info"]["title"] == "YAML API"


def test_parse_default_backend(parser_default: OpenAPIParser, simple_openapi_string: str):
    """Test that the default backend (pyyaml) works correctly."""
    backend_name = type(parser_default.backend).__name__
    assert backend_name == "PyYAMLParserBackend"

    doc = parser_default.parse(simple_openapi_string)
    assert doc["openapi"] == "3.1.0"
    assert doc["info"]["title"] == "x"


def test_parse_pyyaml_backend(parser_pyyaml: OpenAPIParser, simple_openapi_string: str):
    """Test pyyaml parser backend."""
    backend_name = type(parser_pyyaml.backend).__name__
    assert backend_name == "PyYAMLParserBackend"

    doc = parser_pyyaml.parse(simple_openapi_string)
    assert doc["openapi"] == "3.1.0"
    assert doc["info"]["title"] == "x"


def test_parse_ruamel_backend(parser_ruamel: OpenAPIParser, simple_openapi_string: str):
    """Test ruamel parser backend."""
    backend_name = type(parser_ruamel.backend).__name__
    assert backend_name == "RuamelParserBackend"

    doc = parser_ruamel.parse(simple_openapi_string)
    assert doc["openapi"] == "3.1.0"
    assert doc["info"]["title"] == "x"
    assert not hasattr(doc, "lc")  # ruamel safe doesn't keep line/col info


def test_parse_ruamel_roundtrip_backend(
    parser_ruamel_roundtrip: OpenAPIParser, simple_openapi_string: str
):
    """Test ruamel-roundtrip parser backend."""
    backend_name = type(parser_ruamel_roundtrip.backend).__name__
    assert backend_name == "RuamelRoundTripParserBackend"

    doc = parser_ruamel_roundtrip.parse(simple_openapi_string, return_type=CommentedMap)
    assert doc["openapi"] == "3.1.0"
    assert doc["info"]["title"] == "x"
    assert hasattr(doc, "lc")  # ruamel roundtrip keeps line/col info


def test_backend_discovery():
    """Test that backends can be discovered via entry points."""
    parser = OpenAPIParser("pyyaml")
    assert len([parser.backend]) >= 1
    assert type(parser.backend).__name__ == "PyYAMLParserBackend"


def test_invalid_backend_name():
    """Test that invalid backend names raise appropriate errors."""
    with pytest.raises(BackendNotFoundError, match="No parser backend named 'nonexistent' found"):
        OpenAPIParser("nonexistent")


def test_backend_instance_passing():
    """Test passing a backend instance directly."""
    backend_instance = PyYAMLParserBackend()
    parser = OpenAPIParser(backend_instance)
    assert parser.backend is backend_instance

    doc = parser.parse('{"openapi":"3.1.0","info":{"title":"x","version":"1.0.0"}}')
    assert doc["openapi"] == "3.1.0"


def test_backend_class_passing():
    """Test passing a backend class directly."""
    parser = OpenAPIParser(PyYAMLParserBackend)
    assert isinstance(parser.backend, PyYAMLParserBackend)

    doc = parser.parse('{"openapi":"3.1.0","info":{"title":"x","version":"1.0.0"}}')
    assert doc["openapi"] == "3.1.0"


def test_parse_invalid_json():
    """Test parsing invalid JSON raises appropriate error."""
    parser = OpenAPIParser("pyyaml")
    with pytest.raises(DocumentParseError):
        parser.parse('{"invalid json')


def test_parse_invalid_yaml():
    """Test parsing invalid YAML raises appropriate error."""
    parser = OpenAPIParser("pyyaml")
    with pytest.raises(DocumentParseError):
        parser.parse("invalid: yaml: content: [")


def test_parse_non_dict_document():
    """Test parsing non-dict document raises appropriate error."""
    parser = OpenAPIParser("pyyaml")
    with pytest.raises(DocumentParseError):
        parser.parse('["array", "not", "dict"]')


def test_return_type_with_strict_mode():
    """Test return_type parameter with strict mode enabled."""
    parser = OpenAPIParser("ruamel-roundtrip")

    # Should succeed with correct type
    doc = parser.parse(
        '{"openapi":"3.1.0","info":{"title":"x","version":"1.0.0"}}',
        return_type=CommentedMap,
        strict=True,
    )
    assert isinstance(doc, CommentedMap)

    # Should fail with incorrect type in strict mode
    with pytest.raises(TypeConversionError):
        parser.parse(
            '{"openapi":"3.1.0","info":{"title":"x","version":"1.0.0"}}',
            return_type=list,
            strict=True,
        )


def test_return_type_without_strict_mode():
    """Test return_type parameter without strict mode (should cast anyway)."""
    parser = OpenAPIParser("pyyaml")

    # Without strict mode, it casts even if type doesn't match
    doc = parser.parse(
        '{"openapi":"3.1.0","info":{"title":"x","version":"1.0.0"}}', return_type=dict, strict=False
    )
    assert isinstance(doc, dict)


def test_backend_accepts_method():
    """Test that each backend reports correct accepted formats."""
    parser_pyyaml = OpenAPIParser("pyyaml")
    assert "text" in parser_pyyaml.backend.accepts()

    parser_ruamel = OpenAPIParser("ruamel")
    assert "text" in parser_ruamel.backend.accepts()

    parser_roundtrip = OpenAPIParser("ruamel-roundtrip")
    assert "text" in parser_roundtrip.backend.accepts()


def test_parse_yaml_file_uri(tmp_path: Path):
    """Test parsing a YAML file via URI."""
    yaml_content = """openapi: 3.1.0
info:
  title: YAML File API
  version: 1.0.0
paths: {}
"""
    yaml_file = tmp_path / "test.yaml"
    yaml_file.write_text(yaml_content)

    parser = OpenAPIParser("pyyaml")
    doc = parser.parse(yaml_file.as_uri())
    assert doc["openapi"] == "3.1.0"
    assert doc["info"]["title"] == "YAML File API"


def test_to_plain_conversion(parser: OpenAPIParser, simple_openapi_string: str):
    """Test that _to_plain properly converts nested structures."""
    doc = parser.parse(simple_openapi_string)

    # Should be plain dict
    assert isinstance(doc, dict)
    assert isinstance(doc["info"], dict)

    # Test with nested lists
    complex_doc = '{"openapi":"3.1.0","info":{"title":"x","version":"1.0.0"},"tags":["a","b"]}'
    result = parser.parse(complex_doc)
    assert isinstance(result["tags"], list)
    assert result["tags"] == ["a", "b"]
