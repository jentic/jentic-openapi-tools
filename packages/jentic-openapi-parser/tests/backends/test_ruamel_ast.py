"""Tests for RuamelASTParserBackend."""

import textwrap
from pathlib import Path

import pytest
from ruamel.yaml import MappingNode, ScalarNode

from jentic.apitools.openapi.parser.backends.ruamel_ast import RuamelASTParserBackend
from jentic.apitools.openapi.parser.core import OpenAPIParser


# Basic Functionality Tests


def test_parse_text():
    """Test RuamelASTParserBackend can parse text documents."""
    backend = RuamelASTParserBackend()
    yaml_text = textwrap.dedent("""
        openapi: 3.1.2
        info:
          title: Test API
          version: 1.0.0
        paths: {}
    """)
    result = backend.parse(yaml_text)

    # Should return MappingNode
    assert isinstance(result, MappingNode)
    assert result.tag == "tag:yaml.org,2002:map"

    # Should have proper node structure
    assert len(result.value) > 0
    assert isinstance(result.value, list)


def test_parse_json():
    """Test RuamelASTParserBackend can parse JSON documents."""
    backend = RuamelASTParserBackend()
    json_text = '{"openapi":"3.1.2","info":{"title":"Test API","version":"1.0.0"}}'

    result = backend.parse(json_text)

    assert isinstance(result, MappingNode)
    assert result.tag == "tag:yaml.org,2002:map"


def test_parse_uri(tmp_path: Path):
    """Test RuamelASTParserBackend can parse documents from URIs."""
    backend = RuamelASTParserBackend()

    # Create a test YAML file
    yaml_content = textwrap.dedent("""
        openapi: 3.1.2
        info:
          title: URI Test API
          version: 1.0.0
        paths: {}
    """)
    yaml_file = tmp_path / "test_api.yaml"
    yaml_file.write_text(yaml_content)

    result = backend.parse(yaml_file.as_uri())

    assert isinstance(result, MappingNode)
    assert result.tag == "tag:yaml.org,2002:map"


def test_accepts():
    """Test RuamelASTParserBackend reports correct accepted formats."""
    backend = RuamelASTParserBackend()
    accepts = backend.accepts()

    assert "text" in accepts
    assert "uri" in accepts


def test_invalid_type():
    """Test RuamelASTParserBackend raises error for invalid input types."""
    backend = RuamelASTParserBackend()

    # Invalid types cause errors in is_uri_like() before reaching _parse_text type check
    with pytest.raises((TypeError, AttributeError)):
        backend.parse(123)  # type: ignore

    with pytest.raises((TypeError, AttributeError)):
        backend.parse(None)  # type: ignore


def test_non_mapping_document():
    """Test RuamelASTParserBackend raises error for non-mapping documents."""
    backend = RuamelASTParserBackend()

    # YAML list instead of mapping
    with pytest.raises(TypeError, match="Parsed YAML document is not a mapping"):
        backend.parse("- item1\n- item2\n- item3")

    # YAML scalar instead of mapping
    with pytest.raises(TypeError, match="Parsed YAML document is not a mapping"):
        backend.parse("just a string")


def test_inheritance():
    """Test RuamelASTParserBackend inherits from BaseParserBackend."""
    backend = RuamelASTParserBackend()

    # Uses composition, not inheritance from RuamelRoundTripParserBackend
    from jentic.apitools.openapi.parser.backends.base import BaseParserBackend

    assert isinstance(backend, BaseParserBackend)

    # Should have yaml instance (via composition)
    assert hasattr(backend, "yaml")
    assert backend.yaml is not None


# Source Location Tests


def test_preserves_source_location():
    """Test RuamelASTParserBackend preserves source location information."""
    backend = RuamelASTParserBackend()
    yaml_text = textwrap.dedent("""
        openapi: 3.1.2
        info:
          title: Test API
          version: 1.0.0
    """)
    result = backend.parse(yaml_text)

    assert isinstance(result, MappingNode)

    # Check that nodes have start_mark and end_mark
    assert hasattr(result, "start_mark")
    assert hasattr(result, "end_mark")
    assert result.start_mark is not None
    assert result.end_mark is not None

    # Check nested nodes also have marks
    for key_node, value_node in result.value:
        assert hasattr(key_node, "start_mark")
        assert hasattr(key_node, "end_mark")
        assert hasattr(value_node, "start_mark")
        assert hasattr(value_node, "end_mark")


def test_line_column_info():
    """Test that AST backend provides accurate line/column information."""
    backend = RuamelASTParserBackend()
    yaml_text = textwrap.dedent("""\
        openapi: 3.1.2
        info:
          title: Test API
          version: 1.0.0
    """)
    result = backend.parse(yaml_text)

    # Get the first key-value pair (openapi)
    openapi_key_node, openapi_value_node = result.value[0]

    # Check line numbers are present
    assert openapi_key_node.start_mark.line >= 0
    assert openapi_value_node.start_mark.line >= 0

    # openapi key should be on line 0 (first line)
    assert openapi_key_node.start_mark.line == 0

    # info should be on line 1 (second line)
    info_key_node, info_value_node = result.value[1]
    assert info_key_node.start_mark.line == 1


# Node Structure Tests


def test_node_structure():
    """Test RuamelASTParserBackend returns proper node structure."""
    backend = RuamelASTParserBackend()
    yaml_text = textwrap.dedent("""
        openapi: 3.1.2
        info:
          title: Test API
          version: 1.0.0
        paths:
          /pets:
            get:
              summary: List pets
    """)
    result = backend.parse(yaml_text)

    assert isinstance(result, MappingNode)

    # Check we can access nested structure
    node_dict = {k.value: v for k, v in result.value}
    assert "openapi" in node_dict
    assert "info" in node_dict
    assert "paths" in node_dict

    # Check openapi version is a scalar node
    openapi_node = node_dict["openapi"]
    assert isinstance(openapi_node, ScalarNode)
    assert openapi_node.value == "3.1.2"

    # Check info is a mapping node
    info_node = node_dict["info"]
    assert isinstance(info_node, MappingNode)

    # Check paths is a mapping node
    paths_node = node_dict["paths"]
    assert isinstance(paths_node, MappingNode)


def test_complex_nested_structure():
    """Test RuamelASTParserBackend handles complex nested structures."""
    backend = RuamelASTParserBackend()
    yaml_text = textwrap.dedent("""
        openapi: 3.1.2
        info:
          title: Complex API
          version: 1.0.0
        paths:
          /pets:
            get:
              summary: List pets
              parameters:
                - name: limit
                  in: query
                  schema:
                    type: integer
              responses:
                '200':
                  description: Success
                  content:
                    application/json:
                      schema:
                        type: array
                        items:
                          type: object
                          properties:
                            id:
                              type: integer
                            name:
                              type: string
    """)
    result = backend.parse(yaml_text)

    assert isinstance(result, MappingNode)

    # Verify we can traverse deep nested structure
    node_dict = {k.value: v for k, v in result.value}
    paths_node = node_dict["paths"]
    assert isinstance(paths_node, MappingNode)

    # All nested nodes should be accessible
    paths_dict = {k.value: v for k, v in paths_node.value}
    assert "/pets" in paths_dict


# YAML Feature Tests


def test_with_comments():
    """Test RuamelASTParserBackend handles documents with comments."""
    backend = RuamelASTParserBackend()
    yaml_text = textwrap.dedent("""
        # OpenAPI document
        openapi: 3.1.2  # version
        info:
          title: Test API  # inline comment
          version: 1.0.0
        # End comment
    """)
    result = backend.parse(yaml_text)

    # Should successfully parse and return node structure
    assert isinstance(result, MappingNode)
    assert len(result.value) > 0


def test_yaml_anchors_and_aliases():
    """Test RuamelASTParserBackend handles YAML anchors and aliases."""
    backend = RuamelASTParserBackend()
    yaml_text = textwrap.dedent("""
        openapi: 3.1.2
        info:
          title: Test API
          version: 1.0.0
        components:
          schemas:
            BaseError: &base_error
              type: object
              properties:
                message:
                  type: string
            NotFound:
              allOf:
                - *base_error
                - type: object
                  properties:
                    code:
                      type: integer
    """)
    result = backend.parse(yaml_text)

    assert isinstance(result, MappingNode)
    # Should successfully parse with anchors and aliases


def test_multiline_strings():
    """Test RuamelASTParserBackend handles multiline strings."""
    backend = RuamelASTParserBackend()
    yaml_text = textwrap.dedent("""
        openapi: 3.1.2
        info:
          title: Test API
          description: |
            This is a multiline
            description that spans
            multiple lines.
          version: 1.0.0
    """)
    result = backend.parse(yaml_text)

    assert isinstance(result, MappingNode)

    # Find description node
    node_dict = {k.value: v for k, v in result.value}
    info_node = node_dict["info"]
    info_dict = {k.value: v for k, v in info_node.value}
    description_node = info_dict["description"]

    assert isinstance(description_node, ScalarNode)
    assert "multiline" in description_node.value
    assert "multiple lines" in description_node.value


def test_empty_values():
    """Test RuamelASTParserBackend handles empty/null values."""
    backend = RuamelASTParserBackend()
    yaml_text = textwrap.dedent("""
        openapi: 3.1.2
        info:
          title: Test API
          version: 1.0.0
          description:
          contact:
    """)
    result = backend.parse(yaml_text)

    assert isinstance(result, MappingNode)

    # Check empty values are handled
    node_dict = {k.value: v for k, v in result.value}
    info_node = node_dict["info"]
    info_dict = {k.value: v for k, v in info_node.value}

    # description should be None/null
    assert "description" in info_dict
    description_node = info_dict["description"]
    assert isinstance(description_node, ScalarNode)
    assert description_node.value is None or description_node.value == ""


# OpenAPI Specific Tests


def test_with_references():
    """Test RuamelASTParserBackend handles $ref correctly."""
    backend = RuamelASTParserBackend()
    yaml_text = textwrap.dedent("""
        openapi: 3.1.2
        info:
          title: Ref Test
          version: 1.0.0
        components:
          schemas:
            Pet:
              type: object
              properties:
                name:
                  type: string
        paths:
          /pets:
            get:
              responses:
                '200':
                  content:
                    application/json:
                      schema:
                        $ref: '#/components/schemas/Pet'
    """)
    result = backend.parse(yaml_text)

    assert isinstance(result, MappingNode)

    # Find the $ref
    node_dict = {k.value: v for k, v in result.value}
    paths_node = node_dict["paths"]
    paths_dict = {k.value: v for k, v in paths_node.value}
    pets_node = paths_dict["/pets"]
    pets_dict = {k.value: v for k, v in pets_node.value}
    get_node = pets_dict["get"]
    get_dict = {k.value: v for k, v in get_node.value}
    responses_node = get_dict["responses"]
    responses_dict = {k.value: v for k, v in responses_node.value}
    response_200 = responses_dict["200"]
    response_dict = {k.value: v for k, v in response_200.value}
    content_node = response_dict["content"]
    content_dict = {k.value: v for k, v in content_node.value}
    json_node = content_dict["application/json"]
    json_dict = {k.value: v for k, v in json_node.value}

    # Check $ref is preserved as a node
    assert "schema" in json_dict
    schema_node = json_dict["schema"]
    schema_dict = {k.value: v for k, v in schema_node.value}
    assert "$ref" in schema_dict
    ref_node = schema_dict["$ref"]
    assert isinstance(ref_node, ScalarNode)
    assert ref_node.value == "#/components/schemas/Pet"


def test_json_schema_keywords():
    """Test RuamelASTParserBackend handles JSON Schema 2020-12 keywords."""
    backend = RuamelASTParserBackend()
    yaml_text = textwrap.dedent("""
        openapi: 3.1.2
        info:
          title: Test API
          version: 1.0.0
        components:
          schemas:
            Product:
              type: object
              properties:
                id:
                  type: integer
              prefixItems:
                - type: string
                - type: integer
              if:
                properties:
                  premium:
                    const: true
              then:
                required: [support]
              $defs:
                address:
                  type: object
    """)
    result = backend.parse(yaml_text)

    assert isinstance(result, MappingNode)

    # Verify JSON Schema 2020-12 keywords are preserved
    node_dict = {k.value: v for k, v in result.value}
    components = node_dict["components"]
    components_dict = {k.value: v for k, v in components.value}
    schemas = components_dict["schemas"]
    schemas_dict = {k.value: v for k, v in schemas.value}
    product = schemas_dict["Product"]
    product_dict = {k.value: v for k, v in product.value}

    # Check for JSON Schema 2020-12 keywords
    assert "prefixItems" in product_dict
    assert "if" in product_dict
    assert "then" in product_dict
    assert "$defs" in product_dict


# Integration Tests with OpenAPIParser


def test_with_parser():
    """Test RuamelASTParserBackend integration with OpenAPIParser."""
    parser = OpenAPIParser("ruamel-ast")
    backend_name = type(parser.backend).__name__
    assert backend_name == "RuamelASTParserBackend"

    yaml_text = '{"openapi":"3.1.2","info":{"title":"Test","version":"1.0.0"}}'

    # Parse with return_type=MappingNode
    result = parser.parse(yaml_text, return_type=MappingNode)
    assert isinstance(result, MappingNode)


def test_parser_return_type_yaml_node():
    """Test that OpenAPIParser returns MappingNode when requested."""
    parser = OpenAPIParser("ruamel-ast")

    yaml_text = '{"openapi":"3.1.2","info":{"title":"Test","version":"1.0.0"}}'

    # Parse with return_type=MappingNode
    result = parser.parse(yaml_text, return_type=MappingNode)
    assert isinstance(result, MappingNode)

    # Can access node values
    node_dict = {k.value: v for k, v in result.value}
    openapi_node = node_dict["openapi"]
    assert isinstance(openapi_node, ScalarNode)
    assert openapi_node.value == "3.1.2"


def test_parser_default_return():
    """Test RuamelASTParserBackend default return without type conversion."""
    parser = OpenAPIParser("ruamel-ast")

    yaml_text = '{"openapi":"3.1.2","info":{"title":"Test","version":"1.0.0"}}'

    # Parse without return_type
    # The parser's _to_plain method doesn't convert MappingNode (it's not a Mapping)
    # so it returns the node as-is
    result = parser.parse(yaml_text)
    assert isinstance(result, MappingNode)

    # Verify we can still access the data through node structure
    node_dict = {k.value: v for k, v in result.value}
    assert "openapi" in node_dict
    assert node_dict["openapi"].value == "3.1.2"
