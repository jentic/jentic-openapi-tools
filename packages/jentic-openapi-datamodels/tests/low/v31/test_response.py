"""Tests for Response low-level datamodel."""

import textwrap

from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap

from jentic.apitools.openapi.datamodels.low.context import Context
from jentic.apitools.openapi.datamodels.low.sources import FieldSource, KeySource, ValueSource
from jentic.apitools.openapi.datamodels.low.v31 import response
from jentic.apitools.openapi.datamodels.low.v31.header import Header
from jentic.apitools.openapi.datamodels.low.v31.link import Link
from jentic.apitools.openapi.datamodels.low.v31.media_type import MediaType
from jentic.apitools.openapi.datamodels.low.v31.reference import Reference
from jentic.apitools.openapi.datamodels.low.v31.schema import Schema


def test_build_with_description_only():
    """Test building Response with only description field."""
    yaml_content = textwrap.dedent(
        """
        description: successful operation
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = response.build(root)
    assert isinstance(result, response.Response)

    assert result.root_node == root
    assert isinstance(result.description, FieldSource)
    assert result.description.value == "successful operation"

    # Optional fields should be None
    assert result.headers is None
    assert result.content is None
    assert result.links is None
    assert result.extensions == {}


def test_build_with_headers():
    """Test building Response with headers field."""
    yaml_content = textwrap.dedent(
        """
        description: successful operation
        headers:
          X-Rate-Limit:
            description: Rate limit header
            schema:
              type: integer
          X-Expires-After:
            description: Expiration header
            schema:
              type: string
              format: date-time
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = response.build(root)
    assert isinstance(result, response.Response)

    assert result.description is not None
    assert result.description.value == "successful operation"

    assert result.headers is not None
    assert isinstance(result.headers, FieldSource)
    assert isinstance(result.headers.value, dict)
    assert len(result.headers.value) == 2

    # Check header keys
    header_keys = {k.value for k in result.headers.value.keys()}
    assert header_keys == {"X-Rate-Limit", "X-Expires-After"}

    # Check X-Rate-Limit header
    rate_limit_key = next(k for k in result.headers.value.keys() if k.value == "X-Rate-Limit")
    rate_limit_header = result.headers.value[rate_limit_key]
    assert isinstance(rate_limit_header, Header)
    assert rate_limit_header.description is not None
    assert rate_limit_header.description.value == "Rate limit header"


def test_build_with_headers_reference():
    """Test building Response with headers containing $ref."""
    yaml_content = textwrap.dedent(
        """
        description: successful operation
        headers:
          X-Custom-Header:
            $ref: '#/components/headers/CustomHeader'
          X-Another-Header:
            description: Direct header definition
            schema:
              type: string
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = response.build(root)
    assert isinstance(result, response.Response)

    assert result.headers is not None
    assert len(result.headers.value) == 2

    # Check that X-Custom-Header is a Reference
    custom_key = next(k for k in result.headers.value.keys() if k.value == "X-Custom-Header")
    custom_header = result.headers.value[custom_key]
    assert isinstance(custom_header, Reference)
    assert custom_header.ref is not None
    assert custom_header.ref.value == "#/components/headers/CustomHeader"

    # Check that X-Another-Header is a Header
    another_key = next(k for k in result.headers.value.keys() if k.value == "X-Another-Header")
    another_header = result.headers.value[another_key]
    assert isinstance(another_header, Header)


def test_build_with_content():
    """Test building Response with content field."""
    yaml_content = textwrap.dedent(
        """
        description: successful operation
        content:
          application/json:
            schema:
              type: object
              properties:
                id:
                  type: integer
                name:
                  type: string
          application/xml:
            schema:
              type: string
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = response.build(root)
    assert isinstance(result, response.Response)

    assert result.content is not None
    assert isinstance(result.content.value, dict)
    assert len(result.content.value) == 2

    # Check content keys
    content_keys = {k.value for k in result.content.value.keys()}
    assert content_keys == {"application/json", "application/xml"}

    # Check application/json media type
    json_key = next(k for k in result.content.value.keys() if k.value == "application/json")
    json_media_type = result.content.value[json_key]
    assert isinstance(json_media_type, MediaType)
    assert json_media_type.schema is not None
    assert isinstance(json_media_type.schema.value, Schema)


def test_build_with_links():
    """Test building Response with links field."""
    yaml_content = textwrap.dedent(
        """
        description: successful operation
        links:
          GetUserByUserId:
            operationId: getUser
            parameters:
              userId: '$response.body#/id'
            description: Get user by ID
          GetAddressByUserId:
            operationRef: '#/paths/~1users~1{userId}~1address/get'
            parameters:
              userId: '$response.body#/id'
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = response.build(root)
    assert isinstance(result, response.Response)

    assert result.links is not None
    assert isinstance(result.links.value, dict)
    assert len(result.links.value) == 2

    # Check link keys
    link_keys = {k.value for k in result.links.value.keys()}
    assert link_keys == {"GetUserByUserId", "GetAddressByUserId"}

    # Check GetUserByUserId link
    user_link_key = next(k for k in result.links.value.keys() if k.value == "GetUserByUserId")
    user_link = result.links.value[user_link_key]
    assert isinstance(user_link, Link)
    assert user_link.operation_id is not None
    assert user_link.operation_id.value == "getUser"


def test_build_with_links_reference():
    """Test building Response with links containing $ref."""
    yaml_content = textwrap.dedent(
        """
        description: successful operation
        links:
          UserLink:
            $ref: '#/components/links/UserLink'
          AddressLink:
            operationId: getAddress
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = response.build(root)
    assert isinstance(result, response.Response)

    assert result.links is not None
    assert len(result.links.value) == 2

    # Check that UserLink is a Reference
    user_link_key = next(k for k in result.links.value.keys() if k.value == "UserLink")
    user_link = result.links.value[user_link_key]
    assert isinstance(user_link, Reference)
    assert user_link.ref is not None
    assert user_link.ref.value == "#/components/links/UserLink"

    # Check that AddressLink is a Link
    address_link_key = next(k for k in result.links.value.keys() if k.value == "AddressLink")
    address_link = result.links.value[address_link_key]
    assert isinstance(address_link, Link)


def test_build_with_all_fields():
    """Test building Response with all fields."""
    yaml_content = textwrap.dedent(
        """
        description: successful operation
        headers:
          X-Rate-Limit:
            description: Rate limit
            schema:
              type: integer
        content:
          application/json:
            schema:
              type: object
        links:
          GetUser:
            operationId: getUser
        x-custom: value
        x-internal: true
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = response.build(root)
    assert isinstance(result, response.Response)

    assert result.description is not None
    assert result.description.value == "successful operation"
    assert result.headers is not None
    assert len(result.headers.value) == 1
    assert result.content is not None
    assert len(result.content.value) == 1
    assert result.links is not None
    assert len(result.links.value) == 1

    # Check extensions
    assert len(result.extensions) == 2
    ext_dict = {k.value: v.value for k, v in result.extensions.items()}
    assert ext_dict["x-custom"] == "value"
    assert ext_dict["x-internal"] is True


def test_build_with_empty_object():
    """Test building Response from empty YAML object."""
    yaml_content = "{}"
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = response.build(root)
    assert isinstance(result, response.Response)

    assert result.root_node == root
    assert result.description is None
    assert result.headers is None
    assert result.content is None
    assert result.links is None
    assert result.extensions == {}


def test_build_with_invalid_node_returns_value_source():
    """Test that build returns ValueSource for non-mapping nodes."""
    yaml_parser = YAML()

    # Scalar node
    scalar_root = yaml_parser.compose("not-a-response-object")
    result = response.build(scalar_root)
    assert isinstance(result, ValueSource)
    assert result.value == "not-a-response-object"
    assert result.value_node == scalar_root

    # Sequence node
    sequence_root = yaml_parser.compose("['item1', 'item2']")
    result = response.build(sequence_root)
    assert isinstance(result, ValueSource)
    assert result.value == ["item1", "item2"]
    assert result.value_node == sequence_root


def test_build_preserves_invalid_types():
    """Test that build preserves values even with 'wrong' types."""
    yaml_content = textwrap.dedent(
        """
        description: 12345
        headers: not-a-mapping
        content: invalid-value
        links: 999
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = response.build(root)
    assert isinstance(result, response.Response)

    # Should preserve the actual values, not convert them
    assert result.description is not None
    assert result.description.value == 12345

    assert result.headers is not None
    assert result.headers.value == "not-a-mapping"

    assert result.content is not None
    assert result.content.value == "invalid-value"

    assert result.links is not None
    assert result.links.value == 999


def test_build_with_invalid_headers_data():
    """Test that invalid headers data is preserved."""
    yaml_content = textwrap.dedent(
        """
        description: Test response
        headers:
          broken: invalid-string-not-object
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = response.build(root)
    assert isinstance(result, response.Response)

    assert result.headers is not None
    assert len(result.headers.value) == 1

    header_keys = list(result.headers.value.keys())
    assert header_keys[0].value == "broken"
    # The invalid data should be preserved - child builder returns ValueSource
    header_value = result.headers.value[header_keys[0]]
    assert isinstance(header_value, ValueSource)
    assert header_value.value == "invalid-string-not-object"


def test_build_with_custom_context():
    """Test building Response with a custom context."""
    yaml_content = textwrap.dedent(
        """
        description: successful operation
        content:
          application/json:
            schema:
              type: string
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    custom_context = Context()
    result = response.build(root, context=custom_context)
    assert isinstance(result, response.Response)

    assert isinstance(result.description, FieldSource)
    assert result.description.value == "successful operation"


def test_source_tracking():
    """Test that source location information is preserved."""
    yaml_content = textwrap.dedent(
        """
        description: successful operation
        content:
          application/json:
            schema:
              type: string
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = response.build(root)
    assert isinstance(result, response.Response)

    # Check description source tracking
    assert isinstance(result.description, FieldSource)
    assert result.description.key_node is not None
    assert result.description.value_node is not None
    assert result.description.key_node.value == "description"
    assert result.description.value_node.value == "successful operation"

    # Check content source tracking
    assert isinstance(result.content, FieldSource)
    assert result.content.key_node is not None
    assert result.content.value_node is not None
    assert result.content.key_node.value == "content"

    # Check line numbers are available
    assert hasattr(result.description.key_node.start_mark, "line")
    assert hasattr(result.description.value_node.start_mark, "line")


def test_build_with_null_values():
    """Test that build preserves null values."""
    yaml_content = textwrap.dedent(
        """
        description:
        headers:
        content:
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = response.build(root)
    assert isinstance(result, response.Response)

    assert result.description is not None
    assert result.description.value is None

    assert result.headers is not None
    assert result.headers.value is None

    assert result.content is not None
    assert result.content.value is None


def test_build_with_complex_extensions():
    """Test building Response with complex extension objects."""
    yaml_content = textwrap.dedent(
        """
        description: successful operation
        x-response-config:
          cache: enabled
          ttl: 3600
        x-format: custom
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = response.build(root)
    assert isinstance(result, response.Response)

    assert len(result.extensions) == 2
    ext_dict = {k.value: v.value for k, v in result.extensions.items()}

    # Check x-response-config extension
    response_config = ext_dict["x-response-config"]
    assert isinstance(response_config, CommentedMap)
    assert response_config["cache"] == "enabled"
    assert response_config["ttl"] == 3600

    # Check x-format extension
    assert ext_dict["x-format"] == "custom"


def test_build_real_world_success_response():
    """Test a complete real-world 200 success Response."""
    yaml_content = textwrap.dedent(
        """
        description: successful operation
        headers:
          X-Rate-Limit:
            description: calls per hour allowed by the user
            schema:
              type: integer
              format: int32
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
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = response.build(root)
    assert isinstance(result, response.Response)

    assert result.description is not None
    assert result.description.value == "successful operation"
    assert result.headers is not None
    assert len(result.headers.value) == 1
    assert result.content is not None
    assert len(result.content.value) == 1

    # Check content structure
    json_key = next(k for k in result.content.value.keys() if k.value == "application/json")
    json_media_type = result.content.value[json_key]
    assert isinstance(json_media_type, MediaType)
    assert json_media_type.schema is not None


def test_build_real_world_error_response():
    """Test a complete real-world 4xx error Response."""
    yaml_content = textwrap.dedent(
        """
        description: Invalid request
        content:
          application/json:
            schema:
              type: object
              properties:
                code:
                  type: integer
                message:
                  type: string
            example:
              code: 400
              message: Bad Request
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = response.build(root)
    assert isinstance(result, response.Response)

    assert result.description is not None
    assert result.description.value == "Invalid request"
    assert result.content is not None

    json_key = next(k for k in result.content.value.keys())
    json_media_type = result.content.value[json_key]
    assert isinstance(json_media_type, MediaType)
    assert json_media_type.schema is not None
    assert json_media_type.example is not None


def test_headers_source_tracking():
    """Test that headers maintain proper source tracking."""
    yaml_content = textwrap.dedent(
        """
        description: successful operation
        headers:
          X-First:
            description: First header
            schema:
              type: string
          X-Second:
            description: Second header
            schema:
              type: integer
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = response.build(root)
    assert isinstance(result, response.Response)

    assert result.headers is not None

    # Check that each header key has source tracking
    for header_key, header_value in result.headers.value.items():
        assert isinstance(header_key, KeySource)
        assert header_key.key_node is not None

        # Check that the Header has proper root_node
        if isinstance(header_value, Header):
            assert header_value.root_node is not None


def test_content_source_tracking():
    """Test that content maintains proper source tracking."""
    yaml_content = textwrap.dedent(
        """
        description: successful operation
        content:
          application/json:
            schema:
              type: string
          text/plain:
            schema:
              type: string
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = response.build(root)
    assert isinstance(result, response.Response)

    assert result.content is not None

    # Check that each content key has source tracking
    for content_key, content_value in result.content.value.items():
        assert isinstance(content_key, KeySource)
        assert content_key.key_node is not None

        # Check that the MediaType has proper root_node
        assert isinstance(content_value, MediaType)
        assert content_value.root_node is not None


def test_links_source_tracking():
    """Test that links maintain proper source tracking."""
    yaml_content = textwrap.dedent(
        """
        description: successful operation
        links:
          GetUser:
            operationId: getUser
          GetAddress:
            operationId: getAddress
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = response.build(root)
    assert isinstance(result, response.Response)

    assert result.links is not None

    # Check that each link key has source tracking
    for link_key, link_value in result.links.value.items():
        assert isinstance(link_key, KeySource)
        assert link_key.key_node is not None

        # Check that the Link has proper root_node
        if isinstance(link_value, Link):
            assert link_value.root_node is not None


def test_build_response_or_reference_with_response():
    """Test build_response_or_reference with a Response object."""
    yaml_content = textwrap.dedent(
        """
        description: successful operation
        content:
          application/json:
            schema:
              type: string
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    context = Context()
    result = response.build_response_or_reference(root, context)
    assert isinstance(result, response.Response)
    assert result.description is not None
    assert result.description.value == "successful operation"


def test_build_response_or_reference_with_reference():
    """Test build_response_or_reference with a $ref."""
    yaml_content = textwrap.dedent(
        """
        $ref: '#/components/responses/NotFound'
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    context = Context()
    result = response.build_response_or_reference(root, context)
    assert isinstance(result, Reference)
    assert result.ref is not None
    assert result.ref.value == "#/components/responses/NotFound"


def test_build_response_or_reference_with_invalid_node():
    """Test build_response_or_reference with invalid node."""
    yaml_parser = YAML()
    root = yaml_parser.compose("invalid-scalar")

    context = Context()
    result = response.build_response_or_reference(root, context)
    assert isinstance(result, ValueSource)
    assert result.value == "invalid-scalar"


def test_build_with_commonmark_description():
    """Test building Response with CommonMark description."""
    yaml_content = textwrap.dedent(
        """
        description: |
          # Successful Operation

          This response indicates that the **request** was successful.

          - Item 1
          - Item 2
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = response.build(root)
    assert isinstance(result, response.Response)

    assert result.description is not None
    assert "# Successful Operation" in result.description.value
    assert "**request**" in result.description.value


def test_build_with_multiple_content_types():
    """Test building Response with multiple content types."""
    yaml_content = textwrap.dedent(
        """
        description: successful operation
        content:
          application/json:
            schema:
              type: object
          application/xml:
            schema:
              type: object
          text/plain:
            schema:
              type: string
          '*/*':
            schema:
              type: string
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = response.build(root)
    assert isinstance(result, response.Response)

    assert result.content is not None
    assert len(result.content.value) == 4

    content_keys = {k.value for k in result.content.value.keys()}
    assert content_keys == {"application/json", "application/xml", "text/plain", "*/*"}
