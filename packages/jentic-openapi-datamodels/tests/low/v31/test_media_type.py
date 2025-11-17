"""Tests for MediaType low-level datamodel."""

import textwrap

from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap

from jentic.apitools.openapi.datamodels.low.context import Context
from jentic.apitools.openapi.datamodels.low.sources import FieldSource, KeySource, ValueSource
from jentic.apitools.openapi.datamodels.low.v31 import media_type
from jentic.apitools.openapi.datamodels.low.v31.encoding import Encoding
from jentic.apitools.openapi.datamodels.low.v31.example import Example
from jentic.apitools.openapi.datamodels.low.v31.reference import Reference
from jentic.apitools.openapi.datamodels.low.v31.schema import Schema


def test_build_with_schema_only():
    """Test building MediaType with only schema field."""
    yaml_content = textwrap.dedent(
        """
        schema:
          type: string
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = media_type.build(root)
    assert isinstance(result, media_type.MediaType)

    assert result.root_node == root
    assert isinstance(result.schema, FieldSource)
    assert isinstance(result.schema.value, Schema)
    assert result.schema.value.type is not None
    assert result.schema.value.type.value == "string"

    # Optional fields should be None
    assert result.example is None
    assert result.examples is None
    assert result.encoding is None
    assert result.extensions == {}


def test_build_with_schema_reference():
    """Test building MediaType with schema as $ref."""
    yaml_content = textwrap.dedent(
        """
        schema:
          $ref: '#/components/schemas/User'
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = media_type.build(root)
    assert isinstance(result, media_type.MediaType)

    assert result.schema is not None
    assert isinstance(result.schema.value, Schema)  # In OpenAPI 3.1, schemas are Schema objects


def test_build_with_example():
    """Test building MediaType with example field."""
    yaml_content = textwrap.dedent(
        """
        schema:
          type: object
        example:
          id: 1
          name: John Doe
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = media_type.build(root)
    assert isinstance(result, media_type.MediaType)

    assert result.example is not None
    assert isinstance(result.example.value, CommentedMap)
    assert result.example.value["id"] == 1
    assert result.example.value["name"] == "John Doe"


def test_build_with_examples():
    """Test building MediaType with examples field."""
    yaml_content = textwrap.dedent(
        """
        schema:
          type: string
        examples:
          user1:
            value: John Doe
            summary: First user
          user2:
            value: Jane Smith
            summary: Second user
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = media_type.build(root)
    assert isinstance(result, media_type.MediaType)

    assert result.examples is not None
    assert isinstance(result.examples.value, dict)
    assert len(result.examples.value) == 2

    # Check example keys
    example_keys = {k.value for k in result.examples.value.keys()}
    assert example_keys == {"user1", "user2"}

    # Check user1 example
    user1_key = next(k for k in result.examples.value.keys() if k.value == "user1")
    user1_example = result.examples.value[user1_key]
    assert isinstance(user1_example, Example)
    assert user1_example.value is not None
    assert user1_example.value.value == "John Doe"


def test_build_with_examples_reference():
    """Test building MediaType with examples containing $ref."""
    yaml_content = textwrap.dedent(
        """
        schema:
          type: string
        examples:
          default:
            $ref: '#/components/examples/DefaultUser'
          custom:
            value: Custom User
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = media_type.build(root)
    assert isinstance(result, media_type.MediaType)

    assert result.examples is not None
    assert len(result.examples.value) == 2

    # Check that default is a Reference
    default_key = next(k for k in result.examples.value.keys() if k.value == "default")
    default_example = result.examples.value[default_key]
    assert isinstance(default_example, Reference)
    assert default_example.ref is not None
    assert default_example.ref.value == "#/components/examples/DefaultUser"

    # Check that custom is an Example
    custom_key = next(k for k in result.examples.value.keys() if k.value == "custom")
    custom_example = result.examples.value[custom_key]
    assert isinstance(custom_example, Example)


def test_build_with_encoding():
    """Test building MediaType with encoding field."""
    yaml_content = textwrap.dedent(
        """
        schema:
          type: object
          properties:
            profileImage:
              type: string
              format: binary
        encoding:
          profileImage:
            contentType: image/png
            headers:
              X-Rate-Limit:
                description: Rate limit header
                schema:
                  type: integer
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = media_type.build(root)
    assert isinstance(result, media_type.MediaType)

    assert result.encoding is not None
    assert isinstance(result.encoding.value, dict)
    assert len(result.encoding.value) == 1

    # Check encoding keys
    encoding_keys = list(result.encoding.value.keys())
    assert encoding_keys[0].value == "profileImage"

    # Check profileImage encoding
    profile_image_encoding = result.encoding.value[encoding_keys[0]]
    assert isinstance(profile_image_encoding, Encoding)
    assert profile_image_encoding.contentType is not None
    assert profile_image_encoding.contentType.value == "image/png"


def test_build_with_all_fields():
    """Test building MediaType with all fields."""
    yaml_content = textwrap.dedent(
        """
        schema:
          type: object
          properties:
            name:
              type: string
        example:
          name: Example User
        examples:
          user1:
            value:
              name: John Doe
        encoding:
          name:
            contentType: text/plain
        x-custom: value
        x-internal: true
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = media_type.build(root)
    assert isinstance(result, media_type.MediaType)

    assert result.schema is not None
    assert isinstance(result.schema.value, Schema)
    assert result.example is not None
    assert result.examples is not None
    assert len(result.examples.value) == 1
    assert result.encoding is not None
    assert len(result.encoding.value) == 1

    # Check extensions
    assert len(result.extensions) == 2
    ext_dict = {k.value: v.value for k, v in result.extensions.items()}
    assert ext_dict["x-custom"] == "value"
    assert ext_dict["x-internal"] is True


def test_build_with_empty_object():
    """Test building MediaType from empty YAML object."""
    yaml_content = "{}"
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = media_type.build(root)
    assert isinstance(result, media_type.MediaType)

    assert result.root_node == root
    assert result.schema is None
    assert result.example is None
    assert result.examples is None
    assert result.encoding is None
    assert result.extensions == {}


def test_build_with_invalid_node_returns_value_source():
    """Test that build returns ValueSource for non-mapping nodes."""
    yaml_parser = YAML()

    # Scalar node
    scalar_root = yaml_parser.compose("not-a-media-type-object")
    result = media_type.build(scalar_root)
    assert isinstance(result, ValueSource)
    assert result.value == "not-a-media-type-object"
    assert result.value_node == scalar_root

    # Sequence node
    sequence_root = yaml_parser.compose("['item1', 'item2']")
    result = media_type.build(sequence_root)
    assert isinstance(result, ValueSource)
    assert result.value == ["item1", "item2"]
    assert result.value_node == sequence_root


def test_build_preserves_invalid_types():
    """Test that build preserves values even with 'wrong' types."""
    yaml_content = textwrap.dedent(
        """
        schema: invalid-string
        example: true
        examples: not-a-mapping
        encoding: 123
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = media_type.build(root)
    assert isinstance(result, media_type.MediaType)

    # Should preserve the actual values, not convert them
    assert result.schema is not None
    assert result.schema.value == "invalid-string"

    assert result.example is not None
    assert result.example.value is True

    assert result.examples is not None
    assert result.examples.value == "not-a-mapping"

    assert result.encoding is not None
    assert result.encoding.value == 123


def test_build_with_custom_context():
    """Test building MediaType with a custom context."""
    yaml_content = textwrap.dedent(
        """
        schema:
          type: string
        example: test value
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    custom_context = Context()
    result = media_type.build(root, context=custom_context)
    assert isinstance(result, media_type.MediaType)

    assert isinstance(result.schema, FieldSource)
    assert result.example is not None
    assert result.example.value == "test value"


def test_source_tracking():
    """Test that source location information is preserved."""
    yaml_content = textwrap.dedent(
        """
        schema:
          type: string
        example: test
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = media_type.build(root)
    assert isinstance(result, media_type.MediaType)

    # Check schema source tracking
    assert isinstance(result.schema, FieldSource)
    assert result.schema.key_node is not None
    assert result.schema.value_node is not None
    assert result.schema.key_node.value == "schema"

    # Check example source tracking
    assert isinstance(result.example, FieldSource)
    assert result.example.key_node is not None
    assert result.example.value_node is not None
    assert result.example.key_node.value == "example"
    assert result.example.value_node.value == "test"

    # Check line numbers are available
    assert hasattr(result.schema.key_node.start_mark, "line")
    assert hasattr(result.schema.value_node.start_mark, "line")


def test_build_with_null_values():
    """Test that build preserves null values."""
    yaml_content = textwrap.dedent(
        """
        schema:
        example:
        examples:
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = media_type.build(root)
    assert isinstance(result, media_type.MediaType)

    assert result.schema is not None
    assert result.schema.value is None

    assert result.example is not None
    assert result.example.value is None

    assert result.examples is not None
    assert result.examples.value is None


def test_build_with_complex_extensions():
    """Test building MediaType with complex extension objects."""
    yaml_content = textwrap.dedent(
        """
        schema:
          type: string
        x-format-config:
          validation: strict
          transform: uppercase
        x-cache-ttl: 3600
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = media_type.build(root)
    assert isinstance(result, media_type.MediaType)

    assert len(result.extensions) == 2
    ext_dict = {k.value: v.value for k, v in result.extensions.items()}

    # Check x-format-config extension
    format_config = ext_dict["x-format-config"]
    assert isinstance(format_config, CommentedMap)
    assert format_config["validation"] == "strict"
    assert format_config["transform"] == "uppercase"

    # Check x-cache-ttl extension
    assert ext_dict["x-cache-ttl"] == 3600


def test_build_real_world_json_media_type():
    """Test a complete real-world application/json MediaType."""
    yaml_content = textwrap.dedent(
        """
        schema:
          type: object
          required:
            - id
            - name
          properties:
            id:
              type: integer
            name:
              type: string
            email:
              type: string
              format: email
        example:
          id: 42
          name: John Doe
          email: john@example.com
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = media_type.build(root)
    assert isinstance(result, media_type.MediaType)

    assert isinstance(result.schema, FieldSource)
    assert isinstance(result.schema.value, Schema)
    assert result.schema.value.type is not None
    assert result.schema.value.type.value == "object"
    assert result.schema.value.required is not None
    assert len(result.schema.value.required.value) == 2

    assert result.example is not None
    assert isinstance(result.example.value, CommentedMap)
    assert result.example.value["id"] == 42
    assert result.example.value["name"] == "John Doe"


def test_build_real_world_multipart_media_type():
    """Test a complete real-world multipart/form-data MediaType."""
    yaml_content = textwrap.dedent(
        """
        schema:
          type: object
          properties:
            file:
              type: string
              format: binary
            metadata:
              type: object
        encoding:
          file:
            contentType: application/octet-stream
            headers:
              Content-Disposition:
                schema:
                  type: string
          metadata:
            contentType: application/json
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = media_type.build(root)
    assert isinstance(result, media_type.MediaType)

    assert result.schema is not None
    assert isinstance(result.schema.value, Schema)
    assert result.encoding is not None
    assert len(result.encoding.value) == 2

    # Check file encoding
    file_key = next(k for k in result.encoding.value.keys() if k.value == "file")
    file_encoding = result.encoding.value[file_key]
    assert isinstance(file_encoding, Encoding)
    assert file_encoding.contentType is not None
    assert file_encoding.contentType.value == "application/octet-stream"


def test_examples_source_tracking():
    """Test that examples maintain proper source tracking."""
    yaml_content = textwrap.dedent(
        """
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

    result = media_type.build(root)
    assert isinstance(result, media_type.MediaType)

    assert result.examples is not None

    # Check that each example key has source tracking
    for example_key, example_value in result.examples.value.items():
        assert isinstance(example_key, KeySource)
        assert example_key.key_node is not None

        # Check that the Example has proper root_node
        if isinstance(example_value, Example):
            assert example_value.root_node is not None


def test_encoding_source_tracking():
    """Test that encoding maintains proper source tracking."""
    yaml_content = textwrap.dedent(
        """
        schema:
          type: object
        encoding:
          field1:
            contentType: text/plain
          field2:
            contentType: application/json
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = media_type.build(root)
    assert isinstance(result, media_type.MediaType)

    assert result.encoding is not None

    # Check that each encoding key has source tracking
    for encoding_key, encoding_value in result.encoding.value.items():
        assert isinstance(encoding_key, KeySource)
        assert encoding_key.key_node is not None

        # Check that the Encoding has proper root_node
        if isinstance(encoding_value, Encoding):
            assert encoding_value.root_node is not None


def test_build_with_complex_schema():
    """Test building MediaType with complex nested schema."""
    yaml_content = textwrap.dedent(
        """
        schema:
          oneOf:
            - type: object
              properties:
                type:
                  type: string
                  enum: [user]
                name:
                  type: string
            - type: object
              properties:
                type:
                  type: string
                  enum: [admin]
                permissions:
                  type: array
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = media_type.build(root)
    assert isinstance(result, media_type.MediaType)

    assert result.schema is not None
    assert isinstance(result.schema.value, Schema)
    assert result.schema.value.oneOf is not None
    assert len(result.schema.value.oneOf.value) == 2


def test_build_with_array_example():
    """Test building MediaType with array example."""
    yaml_content = textwrap.dedent(
        """
        schema:
          type: array
          items:
            type: string
        example:
          - item1
          - item2
          - item3
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = media_type.build(root)
    assert isinstance(result, media_type.MediaType)

    assert result.example is not None
    assert isinstance(result.example.value, list)
    assert len(result.example.value) == 3
    assert result.example.value[0] == "item1"
