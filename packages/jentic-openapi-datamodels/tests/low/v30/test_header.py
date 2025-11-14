"""Tests for Header low-level datamodel."""

import textwrap

from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap

from jentic.apitools.openapi.datamodels.low.context import Context
from jentic.apitools.openapi.datamodels.low.sources import FieldSource, KeySource, ValueSource
from jentic.apitools.openapi.datamodels.low.v30 import header
from jentic.apitools.openapi.datamodels.low.v30.example import Example
from jentic.apitools.openapi.datamodels.low.v30.reference import Reference
from jentic.apitools.openapi.datamodels.low.v30.schema import Schema


def test_build_with_description_only():
    """Test building Header with only description field."""
    yaml_content = textwrap.dedent(
        """
        description: The number of allowed requests in the current period
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = header.build(root)
    assert isinstance(result, header.Header)

    assert result.root_node == root
    assert isinstance(result.description, FieldSource)
    assert result.description.value == "The number of allowed requests in the current period"

    # Optional fields should be None
    assert result.required is None
    assert result.deprecated is None
    assert result.style is None
    assert result.explode is None
    assert result.schema is None
    assert result.example is None
    assert result.examples is None
    assert result.content is None
    assert result.extensions == {}


def test_build_with_schema():
    """Test building Header with schema field."""
    yaml_content = textwrap.dedent(
        """
        description: Request rate limit
        schema:
          type: integer
          minimum: 0
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = header.build(root)
    assert isinstance(result, header.Header)

    assert result.description is not None
    assert result.description.value == "Request rate limit"

    assert result.schema is not None
    assert isinstance(result.schema, FieldSource)
    assert isinstance(result.schema.value, Schema)
    assert result.schema.value.type is not None
    assert result.schema.value.type.value == "integer"


def test_build_with_schema_reference():
    """Test building Header with schema as $ref."""
    yaml_content = textwrap.dedent(
        """
        description: API version header
        schema:
          $ref: '#/components/schemas/Version'
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = header.build(root)
    assert isinstance(result, header.Header)

    assert result.schema is not None
    assert isinstance(result.schema.value, Reference)
    assert result.schema.value.ref is not None
    assert result.schema.value.ref.value == "#/components/schemas/Version"


def test_build_with_required_and_deprecated():
    """Test building Header with required and deprecated flags."""
    yaml_content = textwrap.dedent(
        """
        description: Authorization header
        required: true
        deprecated: false
        schema:
          type: string
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = header.build(root)
    assert isinstance(result, header.Header)

    assert result.required is not None
    assert result.required.value is True
    assert result.deprecated is not None
    assert result.deprecated.value is False


def test_build_with_style_and_explode():
    """Test building Header with style and explode."""
    yaml_content = textwrap.dedent(
        """
        description: Array header
        style: simple
        explode: true
        schema:
          type: array
          items:
            type: string
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = header.build(root)
    assert isinstance(result, header.Header)

    assert result.style is not None
    assert result.style.value == "simple"
    assert result.explode is not None
    assert result.explode.value is True


def test_build_with_example():
    """Test building Header with example field."""
    yaml_content = textwrap.dedent(
        """
        description: Rate limit
        schema:
          type: integer
        example: 100
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = header.build(root)
    assert isinstance(result, header.Header)

    assert result.example is not None
    assert result.example.value == 100


def test_build_with_examples():
    """Test building Header with examples field."""
    yaml_content = textwrap.dedent(
        """
        description: API token
        schema:
          type: string
        examples:
          production:
            value: prod-token-123
            summary: Production token
          staging:
            value: stg-token-456
            summary: Staging token
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = header.build(root)
    assert isinstance(result, header.Header)

    assert result.examples is not None
    assert isinstance(result.examples.value, dict)
    assert len(result.examples.value) == 2

    # Check example keys
    example_keys = {k.value for k in result.examples.value.keys()}
    assert example_keys == {"production", "staging"}

    # Check production example
    prod_key = next(k for k in result.examples.value.keys() if k.value == "production")
    prod_example = result.examples.value[prod_key]
    assert isinstance(prod_example, Example)
    assert prod_example.value is not None
    assert prod_example.value.value == "prod-token-123"


def test_build_with_examples_reference():
    """Test building Header with examples containing $ref."""
    yaml_content = textwrap.dedent(
        """
        description: Token header
        schema:
          type: string
        examples:
          default:
            $ref: '#/components/examples/DefaultToken'
          custom:
            value: custom-token
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = header.build(root)
    assert isinstance(result, header.Header)

    assert result.examples is not None
    assert len(result.examples.value) == 2

    # Check that default is a Reference
    default_key = next(k for k in result.examples.value.keys() if k.value == "default")
    default_example = result.examples.value[default_key]
    assert isinstance(default_example, Reference)
    assert default_example.ref is not None
    assert default_example.ref.value == "#/components/examples/DefaultToken"

    # Check that custom is an Example
    custom_key = next(k for k in result.examples.value.keys() if k.value == "custom")
    custom_example = result.examples.value[custom_key]
    assert isinstance(custom_example, Example)


def test_build_with_content():
    """Test building Header with content field."""
    yaml_content = textwrap.dedent(
        """
        description: Complex header
        content:
          application/json:
            schema:
              type: object
              properties:
                version:
                  type: string
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = header.build(root)
    assert isinstance(result, header.Header)

    assert result.content is not None
    assert isinstance(result.content.value, dict)
    assert len(result.content.value) == 1

    # Check content keys
    content_keys = list(result.content.value.keys())
    assert len(content_keys) == 1
    assert content_keys[0].value == "application/json"

    # Content values are now MediaType objects
    from jentic.apitools.openapi.datamodels.low.v30.media_type import MediaType
    from jentic.apitools.openapi.datamodels.low.v30.schema import Schema

    media_type_value = result.content.value[content_keys[0]]
    assert isinstance(media_type_value, MediaType)
    assert media_type_value.schema is not None
    assert isinstance(media_type_value.schema.value, Schema)
    assert media_type_value.schema.value.type is not None
    assert media_type_value.schema.value.type.value == "object"


def test_build_with_all_fields():
    """Test building Header with all fields."""
    yaml_content = textwrap.dedent(
        """
        description: Complete header example
        required: true
        deprecated: false
        style: simple
        explode: false
        schema:
          type: string
          pattern: "^[A-Z]+$"
        example: ABC
        x-custom: value
        x-internal: true
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = header.build(root)
    assert isinstance(result, header.Header)

    assert result.description is not None
    assert result.description.value == "Complete header example"
    assert result.required is not None
    assert result.required.value is True
    assert result.deprecated is not None
    assert result.deprecated.value is False
    assert result.style is not None
    assert result.style.value == "simple"
    assert result.explode is not None
    assert result.explode.value is False
    assert result.schema is not None
    assert isinstance(result.schema.value, Schema)
    assert result.example is not None
    assert result.example.value == "ABC"

    # Check extensions
    assert len(result.extensions) == 2
    ext_dict = {k.value: v.value for k, v in result.extensions.items()}
    assert ext_dict["x-custom"] == "value"
    assert ext_dict["x-internal"] is True


def test_build_with_commonmark_description():
    """Test that Header description can contain CommonMark formatted text."""
    yaml_content = textwrap.dedent(
        """
        description: |
          # Rate Limit Header

          This header indicates the **current rate limit** for the API.

          - Resets hourly
          - Maximum: 1000 requests
        schema:
          type: integer
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = header.build(root)
    assert isinstance(result, header.Header)

    assert result.description is not None
    assert "# Rate Limit Header" in result.description.value
    assert "**current rate limit**" in result.description.value
    assert "- Resets hourly" in result.description.value


def test_build_with_empty_object():
    """Test building Header from empty YAML object."""
    yaml_content = "{}"
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = header.build(root)
    assert isinstance(result, header.Header)

    assert result.root_node == root
    assert result.description is None
    assert result.required is None
    assert result.deprecated is None
    assert result.style is None
    assert result.explode is None
    assert result.schema is None
    assert result.example is None
    assert result.examples is None
    assert result.content is None
    assert result.extensions == {}


def test_build_with_invalid_node_returns_value_source():
    """Test that build returns ValueSource for non-mapping nodes."""
    yaml_parser = YAML()

    # Scalar node
    scalar_root = yaml_parser.compose("not-a-header-object")
    result = header.build(scalar_root)
    assert isinstance(result, ValueSource)
    assert result.value == "not-a-header-object"
    assert result.value_node == scalar_root

    # Sequence node
    sequence_root = yaml_parser.compose("['item1', 'item2']")
    result = header.build(sequence_root)
    assert isinstance(result, ValueSource)
    assert result.value == ["item1", "item2"]
    assert result.value_node == sequence_root


def test_build_preserves_invalid_types():
    """Test that build preserves values even with 'wrong' types."""
    yaml_content = textwrap.dedent(
        """
        description: 12345
        required: not-a-boolean
        schema: invalid-string
        examples: not-a-mapping
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = header.build(root)
    assert isinstance(result, header.Header)

    # Should preserve the actual values, not convert them
    assert result.description is not None
    assert result.description.value == 12345

    assert result.required is not None
    assert result.required.value == "not-a-boolean"

    assert result.schema is not None
    # Schema builder returns ValueSource for invalid root, but FieldSource auto-unwraps it
    assert result.schema.value == "invalid-string"

    assert result.examples is not None
    assert result.examples.value == "not-a-mapping"


def test_build_with_invalid_examples_data():
    """Test that invalid examples data is preserved."""
    yaml_content = textwrap.dedent(
        """
        description: Test header
        schema:
          type: string
        examples:
          broken: invalid-string-not-object
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = header.build(root)
    assert isinstance(result, header.Header)

    assert result.examples is not None
    assert len(result.examples.value) == 1

    example_keys = list(result.examples.value.keys())
    assert example_keys[0].value == "broken"
    # The invalid data should be preserved - child builder returns ValueSource
    example_value = result.examples.value[example_keys[0]]
    assert isinstance(example_value, ValueSource)
    assert example_value.value == "invalid-string-not-object"


def test_build_with_custom_context():
    """Test building Header with a custom context."""
    yaml_content = textwrap.dedent(
        """
        description: Custom context header
        schema:
          type: string
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    custom_context = Context()
    result = header.build(root, context=custom_context)
    assert isinstance(result, header.Header)

    assert isinstance(result.description, FieldSource)
    assert result.description.value == "Custom context header"


def test_source_tracking():
    """Test that source location information is preserved."""
    yaml_content = textwrap.dedent(
        """
        description: Tracked header
        required: true
        schema:
          type: integer
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = header.build(root)
    assert isinstance(result, header.Header)

    # Check description source tracking
    assert isinstance(result.description, FieldSource)
    assert result.description.key_node is not None
    assert result.description.value_node is not None
    assert result.description.key_node.value == "description"
    assert result.description.value_node.value == "Tracked header"

    # Check required source tracking
    assert isinstance(result.required, FieldSource)
    assert result.required.key_node is not None
    assert result.required.value_node is not None
    assert result.required.key_node.value == "required"

    # Check schema source tracking
    assert isinstance(result.schema, FieldSource)
    assert result.schema.key_node is not None
    assert result.schema.value_node is not None
    assert result.schema.key_node.value == "schema"

    # Check line numbers are available
    assert hasattr(result.description.key_node.start_mark, "line")
    assert hasattr(result.description.value_node.start_mark, "line")


def test_build_with_null_values():
    """Test that build preserves null values."""
    yaml_content = textwrap.dedent(
        """
        description:
        schema:
        examples:
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = header.build(root)
    assert isinstance(result, header.Header)

    assert result.description is not None
    assert result.description.value is None

    assert result.schema is not None
    # Schema builder returns ValueSource for null, but FieldSource auto-unwraps it
    assert result.schema.value is None

    assert result.examples is not None
    assert result.examples.value is None


def test_build_with_complex_extensions():
    """Test building Header with complex extension objects."""
    yaml_content = textwrap.dedent(
        """
        description: Header with extensions
        schema:
          type: string
        x-rate-limit:
          requests: 1000
          window: 60
        x-auth-type: bearer
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = header.build(root)
    assert isinstance(result, header.Header)

    assert len(result.extensions) == 2
    ext_dict = {k.value: v.value for k, v in result.extensions.items()}

    # Check x-rate-limit extension
    rate_limit = ext_dict["x-rate-limit"]
    assert isinstance(rate_limit, CommentedMap)
    assert rate_limit["requests"] == 1000
    assert rate_limit["window"] == 60

    # Check x-auth-type extension
    assert ext_dict["x-auth-type"] == "bearer"


def test_build_real_world_rate_limit_header():
    """Test a complete real-world rate limit Header."""
    yaml_content = textwrap.dedent(
        """
        description: |
          The number of allowed requests in the current period.
          Resets at the top of each hour.
        required: false
        deprecated: false
        schema:
          type: integer
          minimum: 0
          maximum: 5000
        example: 1000
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = header.build(root)
    assert isinstance(result, header.Header)

    assert isinstance(result.description, FieldSource)
    assert "The number of allowed requests" in result.description.value
    assert result.required is not None
    assert result.required.value is False
    assert result.deprecated is not None
    assert result.deprecated.value is False
    assert result.schema is not None
    assert isinstance(result.schema.value, Schema)
    assert result.schema.value.type is not None
    assert result.schema.value.type.value == "integer"
    assert result.example is not None
    assert result.example.value == 1000


def test_build_real_world_api_version_header():
    """Test a complete real-world API version Header."""
    yaml_content = textwrap.dedent(
        """
        description: API version header
        required: true
        schema:
          type: string
          enum:
            - v1
            - v2
            - v3
        example: v2
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = header.build(root)
    assert isinstance(result, header.Header)

    assert result.description is not None
    assert result.description.value == "API version header"
    assert result.required is not None
    assert result.required.value is True
    assert result.schema is not None
    assert isinstance(result.schema.value, Schema)
    assert result.schema.value.enum is not None
    enum_values = [item.value for item in result.schema.value.enum.value]
    assert enum_values == ["v1", "v2", "v3"]


def test_examples_source_tracking():
    """Test that examples maintain proper source tracking."""
    yaml_content = textwrap.dedent(
        """
        description: Header with examples
        schema:
          type: string
        examples:
          first:
            value: example1
          second:
            value: example2
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = header.build(root)
    assert isinstance(result, header.Header)

    assert result.examples is not None

    # Check that each example key has source tracking
    for example_key, example_value in result.examples.value.items():
        assert isinstance(example_key, KeySource)
        assert example_key.key_node is not None

        # Check that the Example or ValueSource has proper root_node/value_node
        if isinstance(example_value, Example):
            assert example_value.root_node is not None
        elif isinstance(example_value, ValueSource):
            assert example_value.value_node is not None


def test_build_with_content_multiple_media_types():
    """Test building Header with content field containing multiple media types."""
    yaml_content = textwrap.dedent(
        """
        description: Multi-format header
        content:
          application/json:
            schema:
              type: object
              properties:
                version:
                  type: string
          application/xml:
            schema:
              type: string
          text/plain:
            schema:
              type: string
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = header.build(root)
    assert isinstance(result, header.Header)

    from jentic.apitools.openapi.datamodels.low.v30.media_type import MediaType

    assert result.content is not None
    assert isinstance(result.content.value, dict)
    assert len(result.content.value) == 3

    # Check content keys
    content_keys = {k.value for k in result.content.value.keys()}
    assert content_keys == {"application/json", "application/xml", "text/plain"}

    # Check all are MediaType objects
    for media_type_value in result.content.value.values():
        assert isinstance(media_type_value, MediaType)
        assert media_type_value.schema is not None


def test_build_with_content_with_examples():
    """Test building Header with content containing examples."""
    yaml_content = textwrap.dedent(
        """
        description: Header with content examples
        content:
          application/json:
            schema:
              type: object
            examples:
              version1:
                value:
                  version: "1.0"
              version2:
                value:
                  version: "2.0"
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = header.build(root)
    assert isinstance(result, header.Header)

    from jentic.apitools.openapi.datamodels.low.v30.example import Example
    from jentic.apitools.openapi.datamodels.low.v30.media_type import MediaType

    assert result.content is not None
    json_key = next(k for k in result.content.value.keys() if k.value == "application/json")
    json_media_type = result.content.value[json_key]
    assert isinstance(json_media_type, MediaType)
    assert json_media_type.examples is not None
    assert len(json_media_type.examples.value) == 2

    # Check examples
    example_keys = {k.value for k in json_media_type.examples.value.keys()}
    assert example_keys == {"version1", "version2"}

    for example_value in json_media_type.examples.value.values():
        assert isinstance(example_value, Example)


def test_build_with_content_with_encoding():
    """Test building Header with content containing encoding."""
    yaml_content = textwrap.dedent(
        """
        description: Header with content encoding
        content:
          multipart/form-data:
            schema:
              type: object
              properties:
                file:
                  type: string
                  format: binary
            encoding:
              file:
                contentType: application/octet-stream
                headers:
                  Content-Disposition:
                    schema:
                      type: string
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = header.build(root)
    assert isinstance(result, header.Header)

    from jentic.apitools.openapi.datamodels.low.v30.encoding import Encoding
    from jentic.apitools.openapi.datamodels.low.v30.media_type import MediaType

    assert result.content is not None
    multipart_key = next(k for k in result.content.value.keys() if k.value == "multipart/form-data")
    multipart_media_type = result.content.value[multipart_key]
    assert isinstance(multipart_media_type, MediaType)
    assert multipart_media_type.encoding is not None
    assert len(multipart_media_type.encoding.value) == 1

    # Check encoding
    file_key = next(k for k in multipart_media_type.encoding.value.keys() if k.value == "file")
    file_encoding = multipart_media_type.encoding.value[file_key]
    assert isinstance(file_encoding, Encoding)
    assert file_encoding.contentType is not None
    assert file_encoding.contentType.value == "application/octet-stream"


def test_content_source_tracking():
    """Test that content maintains proper source tracking."""
    yaml_content = textwrap.dedent(
        """
        description: Header with content
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

    result = header.build(root)
    assert isinstance(result, header.Header)

    from jentic.apitools.openapi.datamodels.low.v30.media_type import MediaType

    assert result.content is not None

    # Check that each content key has source tracking
    for content_key, content_value in result.content.value.items():
        assert isinstance(content_key, KeySource)
        assert content_key.key_node is not None

        # Check that the MediaType has proper root_node
        assert isinstance(content_value, MediaType)
        assert content_value.root_node is not None


def test_build_with_content_invalid_data():
    """Test that invalid content data is preserved."""
    yaml_content = textwrap.dedent(
        """
        description: Test header
        content:
          application/json: invalid-string-not-object
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = header.build(root)
    assert isinstance(result, header.Header)

    assert result.content is not None
    assert len(result.content.value) == 1

    content_keys = list(result.content.value.keys())
    assert content_keys[0].value == "application/json"
    # The invalid data should be preserved - child builder returns ValueSource
    content_value = result.content.value[content_keys[0]]
    assert isinstance(content_value, ValueSource)
    assert content_value.value == "invalid-string-not-object"


def test_build_with_content_and_schema_mutual_exclusivity():
    """Test that Header can have both schema and content (even though they're mutually exclusive per spec)."""
    yaml_content = textwrap.dedent(
        """
        description: Header with both schema and content
        schema:
          type: string
        content:
          application/json:
            schema:
              type: object
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = header.build(root)
    assert isinstance(result, header.Header)

    from jentic.apitools.openapi.datamodels.low.v30.media_type import MediaType
    from jentic.apitools.openapi.datamodels.low.v30.schema import Schema

    # Both fields should be preserved even if they violate the spec
    # (validation layer will catch this)
    assert result.schema is not None
    assert isinstance(result.schema.value, Schema)
    assert result.content is not None
    assert len(result.content.value) == 1

    json_key = next(k for k in result.content.value.keys())
    json_media_type = result.content.value[json_key]
    assert isinstance(json_media_type, MediaType)
