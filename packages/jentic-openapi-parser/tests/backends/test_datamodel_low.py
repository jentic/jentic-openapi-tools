"""Tests for DataModelLowParserBackend."""

import textwrap
from pathlib import Path

import pytest

from jentic.apitools.openapi.datamodels.low.v30.openapi import OpenAPI30
from jentic.apitools.openapi.datamodels.low.v31.openapi import OpenAPI31
from jentic.apitools.openapi.datamodels.low.v31.response import Response
from jentic.apitools.openapi.datamodels.low.v31.schema import Schema
from jentic.apitools.openapi.parser.backends.datamodel_low import (
    DataModelLow,
    DataModelLowParserBackend,
)
from jentic.apitools.openapi.parser.core import OpenAPIParser
from jentic.apitools.openapi.parser.core.exceptions import TypeConversionError


# Basic Functionality Tests


def test_parse_v30_text():
    """Test DataModelLowParserBackend can parse OpenAPI 3.0 text documents."""
    backend = DataModelLowParserBackend()
    yaml_text = textwrap.dedent(
        """
        openapi: 3.0.4
        info:
          title: Test API
          version: 1.0.0
        paths: {}
    """
    )
    result = backend.parse(yaml_text)

    # Should return OpenAPI30 datamodel
    assert isinstance(result, OpenAPI30)
    assert result.openapi is not None
    assert result.openapi.value == "3.0.4"
    assert result.info is not None
    assert result.info.value.title is not None
    assert result.info.value.title.value == "Test API"
    assert result.info.value.version is not None
    assert result.info.value.version.value == "1.0.0"


def test_parse_v31_text():
    """Test DataModelLowParserBackend can parse OpenAPI 3.1 text documents."""
    backend = DataModelLowParserBackend()
    yaml_text = textwrap.dedent(
        """
        openapi: 3.1.2
        info:
          title: Test API
          version: 1.0.0
        paths: {}
    """
    )
    result = backend.parse(yaml_text)

    # Should return OpenAPI31 datamodel
    assert isinstance(result, OpenAPI31)
    assert result.openapi is not None
    assert result.openapi.value == "3.1.2"
    assert result.info is not None
    assert result.info.value.title is not None
    assert result.info.value.title.value == "Test API"
    assert result.info.value.version is not None
    assert result.info.value.version.value == "1.0.0"


def test_parse_json():
    """Test DataModelLowParserBackend can parse JSON documents."""
    backend = DataModelLowParserBackend()
    json_text = '{"openapi":"3.0.4","info":{"title":"Test API","version":"1.0.0"},"paths":{}}'

    result = backend.parse(json_text)

    assert isinstance(result, OpenAPI30)
    assert result.openapi is not None
    assert result.openapi.value == "3.0.4"


def test_parse_uri(tmp_path: Path):
    """Test DataModelLowParserBackend can parse documents from URIs."""
    backend = DataModelLowParserBackend()

    # Create a test YAML file
    yaml_content = textwrap.dedent(
        """
        openapi: 3.0.4
        info:
          title: URI Test API
          version: 1.0.0
        paths: {}
    """
    )
    yaml_file = tmp_path / "test_api.yaml"
    yaml_file.write_text(yaml_content)

    result = backend.parse(yaml_file.as_uri())

    assert isinstance(result, OpenAPI30)
    assert result.info is not None
    assert result.info.value.title is not None
    assert result.info.value.title.value == "URI Test API"


def test_accepts():
    """Test DataModelLowParserBackend reports correct accepted formats."""
    backend = DataModelLowParserBackend()
    accepts = backend.accepts()

    assert "text" in accepts
    assert "uri" in accepts


# Version Detection Tests


def test_parse_v30_with_patch():
    """Test parsing OpenAPI 3.0.x with various patch versions."""
    backend = DataModelLowParserBackend()

    for patch_version in ["3.0.0", "3.0.1", "3.0.2", "3.0.3", "3.0.4"]:
        yaml_text = f"""
openapi: {patch_version}
info:
  title: Test
  version: 1.0.0
paths: {{}}
"""
        result = backend.parse(yaml_text)
        assert isinstance(result, OpenAPI30)
        assert result.openapi is not None
        assert result.openapi.value == patch_version


def test_parse_v31_with_patch():
    """Test parsing OpenAPI 3.1.x with various patch versions."""
    backend = DataModelLowParserBackend()

    for patch_version in ["3.1.0", "3.1.1", "3.1.2"]:
        yaml_text = f"""
openapi: {patch_version}
info:
  title: Test
  version: 1.0.0
paths: {{}}
"""
        result = backend.parse(yaml_text)
        assert isinstance(result, OpenAPI31)
        assert result.openapi is not None
        assert result.openapi.value == patch_version


def test_parse_version_with_suffix():
    """Test that versions with suffixes are rejected by version detection."""
    backend = DataModelLowParserBackend()

    # v3.0 with suffix should be rejected
    yaml_text = """
openapi: 3.0.4-rc1
info:
  title: Test
  version: 1.0.0
paths: {}
"""
    with pytest.raises(ValueError, match="Unsupported OpenAPI version"):
        backend.parse(yaml_text)

    # v3.1 with suffix should be rejected
    yaml_text = """
openapi: 3.1.2-beta
info:
  title: Test
  version: 1.0.0
paths: {}
"""
    with pytest.raises(ValueError, match="Unsupported OpenAPI version"):
        backend.parse(yaml_text)


# Source Tracking Tests


def test_preserves_source_location():
    """Test DataModelLowParserBackend preserves source location information."""
    backend = DataModelLowParserBackend()
    yaml_text = textwrap.dedent(
        """\
        openapi: 3.0.4
        info:
          title: Test API
          version: 1.0.0
        paths: {}
    """
    )
    result = backend.parse(yaml_text)

    assert isinstance(result, OpenAPI30)

    # Check that nodes have start_mark and end_mark
    assert hasattr(result.root_node, "start_mark")
    assert hasattr(result.root_node, "end_mark")
    assert result.root_node.start_mark is not None
    assert result.root_node.end_mark is not None

    # Check field source tracking
    assert result.openapi is not None
    assert result.openapi.key_node is not None
    assert result.openapi.value_node is not None
    assert hasattr(result.openapi.key_node, "start_mark")


def test_line_column_info():
    """Test that backend provides accurate line/column information."""
    backend = DataModelLowParserBackend()
    yaml_text = textwrap.dedent(
        """\
        openapi: 3.0.4
        info:
          title: Test API
          version: 1.0.0
    """
    )
    result = backend.parse(yaml_text)

    assert isinstance(result, OpenAPI30)
    # openapi should be on line 0 (first line)
    assert result.openapi is not None
    assert result.openapi.key_node.start_mark.line == 0

    # info should be on line 1 (second line)
    assert result.info is not None
    assert result.info.key_node.start_mark.line == 1


# Field Access Tests


def test_field_access_v30():
    """Test accessing fields in OpenAPI 3.0 datamodel."""
    backend = DataModelLowParserBackend()
    yaml_text = textwrap.dedent(
        """
        openapi: 3.0.4
        info:
          title: Pet Store API
          description: A sample Pet Store API
          version: 1.0.0
          contact:
            name: API Support
            email: support@example.com
        paths:
          /pets:
            get:
              summary: List all pets
              responses:
                '200':
                  description: A list of pets
    """
    )
    result = backend.parse(yaml_text)

    assert isinstance(result, OpenAPI30)

    # Access info fields
    assert result.info is not None
    assert result.info.value.title is not None
    assert result.info.value.title.value == "Pet Store API"
    assert result.info.value.description is not None
    assert result.info.value.description.value == "A sample Pet Store API"
    assert result.info.value.version is not None
    assert result.info.value.version.value == "1.0.0"
    assert result.info.value.contact is not None
    assert result.info.value.contact.value.name is not None
    assert result.info.value.contact.value.name.value == "API Support"
    assert result.info.value.contact.value.email is not None
    assert result.info.value.contact.value.email.value == "support@example.com"

    # Access paths
    assert result.paths is not None
    assert len(result.paths.value.paths) == 1
    pets_path_key = next(iter(result.paths.value.paths.keys()))
    assert pets_path_key.value == "/pets"


def test_field_access_v31():
    """Test accessing fields in OpenAPI 3.1 datamodel with JSON Schema 2020-12."""
    backend = DataModelLowParserBackend()
    yaml_text = textwrap.dedent(
        """
        openapi: 3.1.2
        info:
          title: Pet Store API
          version: 1.0.0
        paths:
          /pets:
            get:
              responses:
                '200':
                  description: Pet list
                  content:
                    application/json:
                      schema:
                        type: array
                        prefixItems:
                          - type: string
                          - type: integer
                        items: false
    """
    )
    result = backend.parse(yaml_text)

    assert isinstance(result, OpenAPI31)

    # Access JSON Schema 2020-12 features
    # Find /pets path (keys are KeySource objects)
    assert result.paths is not None
    path_item = None
    for key_source, item in result.paths.value.paths.items():
        if key_source.value == "/pets":
            path_item = item
            break
    assert path_item is not None

    # Find 200 response (keys are KeySource objects)
    assert path_item.get is not None
    assert path_item.get.value.responses is not None
    response = None
    for key_source, resp in path_item.get.value.responses.value.responses.items():
        if key_source.value == "200":
            response = resp
            break
    assert response is not None

    # Find application/json media type (keys are KeySource objects)
    assert isinstance(response, Response)
    assert response.content is not None
    media_type = None
    for key_source, mt in response.content.value.items():
        if key_source.value == "application/json":
            media_type = mt
            break
    assert media_type is not None

    assert media_type.schema is not None
    schema = media_type.schema.value

    # Check prefixItems - narrow schema type from union
    assert isinstance(schema, Schema)
    assert schema.prefix_items is not None
    assert len(schema.prefix_items.value) == 2
    # Narrow type of prefix items
    item_0 = schema.prefix_items.value[0]
    assert isinstance(item_0, Schema)
    assert item_0.type is not None
    assert item_0.type.value == "string"
    item_1 = schema.prefix_items.value[1]
    assert isinstance(item_1, Schema)
    assert item_1.type is not None
    assert item_1.type.value == "integer"

    # Check boolean schema (items: false)
    assert schema.items is not None
    assert schema.items.value is False


# Integration Tests


def test_with_parser():
    """Test DataModelLowParserBackend integration with OpenAPIParser."""
    parser = OpenAPIParser("datamodel-low")
    backend_name = type(parser.backend).__name__
    assert backend_name == "DataModelLowParserBackend"

    yaml_text = textwrap.dedent(
        """
        openapi: 3.0.4
        info:
          title: Test
          version: 1.0.0
        paths: {}
    """
    )

    result = parser.parse(yaml_text)
    assert isinstance(result, OpenAPI30)


def test_parser_v30():
    """Test parsing v3.0 document via OpenAPIParser."""
    parser = OpenAPIParser("datamodel-low")

    yaml_text = '{"openapi":"3.0.4","info":{"title":"Test","version":"1.0.0"},"paths":{}}'

    result = parser.parse(yaml_text)
    assert isinstance(result, OpenAPI30)
    assert result.openapi is not None
    assert result.openapi.value == "3.0.4"


def test_parser_v31():
    """Test parsing v3.1 document via OpenAPIParser."""
    parser = OpenAPIParser("datamodel-low")

    yaml_text = '{"openapi":"3.1.2","info":{"title":"Test","version":"1.0.0"}}'

    result = parser.parse(yaml_text)
    assert isinstance(result, OpenAPI31)
    assert result.openapi is not None
    assert result.openapi.value == "3.1.2"


# Union Type Tests


def test_parser_with_union_type_v30():
    """Test parsing with DataModelLow union type returns OpenAPI30."""
    parser = OpenAPIParser("datamodel-low")

    yaml_text = textwrap.dedent(
        """
        openapi: 3.0.4
        info:
          title: Test API
          version: 1.0.0
        paths: {}
    """
    )

    # Use union type - type checker sees 'Any', runtime gets OpenAPI30
    result = parser.parse(yaml_text, return_type=DataModelLow)
    assert isinstance(result, OpenAPI30)
    assert result.openapi is not None
    assert result.openapi.value == "3.0.4"


def test_parser_with_union_type_v31():
    """Test parsing with DataModelLow union type returns OpenAPI31."""
    parser = OpenAPIParser("datamodel-low")

    yaml_text = textwrap.dedent(
        """
        openapi: 3.1.2
        info:
          title: Test API
          version: 1.0.0
        paths: {}
    """
    )

    # Use union type - type checker sees 'Any', runtime gets OpenAPI31
    result = parser.parse(yaml_text, return_type=DataModelLow)
    assert isinstance(result, OpenAPI31)
    assert result.openapi is not None
    assert result.openapi.value == "3.1.2"


def test_parser_with_union_type_strict_valid():
    """Test parsing with DataModelLow and strict=True passes for valid type."""
    parser = OpenAPIParser("datamodel-low")

    yaml_text = textwrap.dedent(
        """
        openapi: 3.0.4
        info:
          title: Test API
          version: 1.0.0
        paths: {}
    """
    )

    # Should not raise - result is OpenAPI30 which is in the union
    result = parser.parse(yaml_text, return_type=DataModelLow, strict=True)
    assert isinstance(result, OpenAPI30)


def test_parser_with_concrete_type_strict_invalid():
    """Test parsing with concrete type and strict=True raises for type mismatch."""
    parser = OpenAPIParser("datamodel-low")

    # This is a v3.0 document
    yaml_text = textwrap.dedent(
        """
        openapi: 3.0.4
        info:
          title: Test API
          version: 1.0.0
        paths: {}
    """
    )

    # Expect OpenAPI31 but get OpenAPI30 - should raise with strict=True
    with pytest.raises(TypeConversionError, match="Expected OpenAPI31, got OpenAPI30"):
        parser.parse(yaml_text, return_type=OpenAPI31, strict=True)


# Error Handling Tests


def test_unsupported_version_swagger_20():
    """Test that Swagger 2.0 raises ValueError."""
    backend = DataModelLowParserBackend()
    yaml_text = """
swagger: '2.0'
info:
  title: Test
  version: 1.0.0
paths: {}
"""
    # swagger: '2.0' documents don't match OpenAPI 3.x patterns
    with pytest.raises(ValueError, match="Unsupported OpenAPI version"):
        backend.parse(yaml_text)


def test_unsupported_version_32():
    """Test that OpenAPI 3.2 raises ValueError."""
    backend = DataModelLowParserBackend()
    yaml_text = """
openapi: 3.2.0
info:
  title: Test
  version: 1.0.0
paths: {}
"""
    with pytest.raises(ValueError, match="Unsupported OpenAPI version"):
        backend.parse(yaml_text)


def test_missing_openapi_field():
    """Test that documents without openapi field raise ValueError."""
    backend = DataModelLowParserBackend()
    yaml_text = """
info:
  title: Test
  version: 1.0.0
paths: {}
"""
    with pytest.raises(ValueError, match="Unsupported OpenAPI version"):
        backend.parse(yaml_text)


def test_invalid_openapi_field_type():
    """Test that non-string openapi field raises ValueError."""
    backend = DataModelLowParserBackend()
    yaml_text = """
openapi: 123
info:
  title: Test
  version: 1.0.0
paths: {}
"""
    # 123 is parsed as int, reported as unsupported version
    with pytest.raises(ValueError, match="Unsupported OpenAPI version"):
        backend.parse(yaml_text)


def test_invalid_version_format():
    """Test that invalid version format raises ValueError."""
    backend = DataModelLowParserBackend()
    yaml_text = """
openapi: "3"
info:
  title: Test
  version: 1.0.0
paths: {}
"""
    # "3" doesn't match any version pattern
    with pytest.raises(ValueError, match="Unsupported OpenAPI version"):
        backend.parse(yaml_text)


def test_non_mapping_document():
    """Test that non-mapping documents raise ValueError."""
    backend = DataModelLowParserBackend()

    # YAML list instead of mapping - doesn't match version patterns
    with pytest.raises(ValueError, match="Unsupported OpenAPI version"):
        backend.parse("- item1\n- item2\n- item3")

    # YAML scalar instead of mapping - doesn't match version patterns
    with pytest.raises(ValueError, match="Unsupported OpenAPI version"):
        backend.parse("just a string")


# Real World Tests


def test_real_world_v30_document():
    """Test parsing a realistic OpenAPI 3.0 document."""
    backend = DataModelLowParserBackend()
    yaml_text = textwrap.dedent(
        """
        openapi: 3.0.4
        info:
          title: Pet Store API
          description: A sample Pet Store API
          version: 1.0.0
          contact:
            name: API Support
            email: support@example.com
          license:
            name: Apache 2.0
            url: https://www.apache.org/licenses/LICENSE-2.0.html
        servers:
          - url: https://api.example.com/v1
            description: Production server
        paths:
          /pets:
            get:
              summary: List all pets
              operationId: listPets
              tags:
                - pets
              parameters:
                - name: limit
                  in: query
                  schema:
                    type: integer
              responses:
                '200':
                  description: A list of pets
                  content:
                    application/json:
                      schema:
                        type: array
                        items:
                          $ref: '#/components/schemas/Pet'
        components:
          schemas:
            Pet:
              type: object
              required:
                - id
                - name
              properties:
                id:
                  type: integer
                name:
                  type: string
                tag:
                  type: string
    """
    )
    result = backend.parse(yaml_text)

    assert isinstance(result, OpenAPI30)
    assert result.info is not None
    assert result.info.value.title is not None
    assert result.info.value.title.value == "Pet Store API"
    assert result.info.value.license is not None
    assert result.info.value.license.value.name is not None
    assert result.info.value.license.value.name.value == "Apache 2.0"
    assert result.servers is not None
    assert len(result.servers.value) == 1
    assert result.paths is not None
    assert len(result.paths.value.paths) == 1
    assert result.components is not None
    assert result.components.value.schemas is not None


def test_real_world_v31_document():
    """Test parsing a realistic OpenAPI 3.1 document."""
    backend = DataModelLowParserBackend()
    yaml_text = textwrap.dedent(
        """
        openapi: 3.1.2
        info:
          title: Pet Store API
          version: 1.0.0
        paths:
          /pets:
            get:
              responses:
                '200':
                  description: Pet list
                  content:
                    application/json:
                      schema:
                        type: array
                        prefixItems:
                          - type: string
                          - type: integer
                        items: false
                        contains:
                          type: object
                          required: [id]
        components:
          schemas:
            Pet:
              type: object
              properties:
                id:
                  type: integer
                tags:
                  type: array
                  prefixItems:
                    - type: string
                    - type: string
                  items: false
              patternProperties:
                "^x-":
                  type: string
              unevaluatedProperties: false
    """
    )
    result = backend.parse(yaml_text)

    assert isinstance(result, OpenAPI31)
    assert result.info is not None
    assert result.info.value.title is not None
    assert result.info.value.title.value == "Pet Store API"

    # Check JSON Schema 2020-12 features in response
    # Find /pets path (keys are KeySource objects)
    assert result.paths is not None
    path_item = None
    for key_source, item in result.paths.value.paths.items():
        if key_source.value == "/pets":
            path_item = item
            break
    assert path_item is not None

    # Find 200 response (keys are KeySource objects)
    assert path_item.get is not None
    assert path_item.get.value.responses is not None
    response = None
    for key_source, resp in path_item.get.value.responses.value.responses.items():
        if key_source.value == "200":
            response = resp
            break
    assert response is not None

    # Find application/json media type (keys are KeySource objects)
    assert isinstance(response, Response)
    assert response.content is not None
    media_type = None
    for key_source, mt in response.content.value.items():
        if key_source.value == "application/json":
            media_type = mt
            break
    assert media_type is not None

    assert media_type.schema is not None
    response_schema = media_type.schema.value

    assert isinstance(response_schema, Schema)
    assert response_schema.prefix_items is not None
    assert response_schema.items is not None
    assert response_schema.items.value is False
    assert response_schema.contains is not None

    # Check JSON Schema 2020-12 features in components
    # Find Pet schema (keys are KeySource objects)
    assert result.components is not None
    assert result.components.value.schemas is not None
    pet_schema = None
    for key_source, schema in result.components.value.schemas.value.items():
        if key_source.value == "Pet":
            pet_schema = schema
            break
    assert pet_schema is not None
    assert isinstance(pet_schema, Schema)
    assert pet_schema.pattern_properties is not None
    assert pet_schema.unevaluated_properties is not None
    assert pet_schema.unevaluated_properties.value is False
