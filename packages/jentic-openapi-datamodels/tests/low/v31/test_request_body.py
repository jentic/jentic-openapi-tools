"""Tests for RequestBody low-level datamodel."""

import textwrap

from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap

from jentic.apitools.openapi.datamodels.low.context import Context
from jentic.apitools.openapi.datamodels.low.sources import FieldSource, KeySource, ValueSource
from jentic.apitools.openapi.datamodels.low.v31 import request_body
from jentic.apitools.openapi.datamodels.low.v31.media_type import MediaType
from jentic.apitools.openapi.datamodels.low.v31.reference import Reference
from jentic.apitools.openapi.datamodels.low.v31.schema import Schema


def test_build_with_content_only():
    """Test building RequestBody with only content field."""
    yaml_content = textwrap.dedent(
        """
        content:
          application/json:
            schema:
              type: object
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = request_body.build(root)
    assert isinstance(result, request_body.RequestBody)

    assert result.root_node == root
    assert result.content is not None
    assert isinstance(result.content.value, dict)
    assert len(result.content.value) == 1

    # Optional fields should be None
    assert result.description is None
    assert result.required is None
    assert result.extensions == {}


def test_build_with_description():
    """Test building RequestBody with description field."""
    yaml_content = textwrap.dedent(
        """
        description: user to add to the system
        content:
          application/json:
            schema:
              type: object
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = request_body.build(root)
    assert isinstance(result, request_body.RequestBody)

    assert result.description is not None
    assert result.description.value == "user to add to the system"


def test_build_with_required():
    """Test building RequestBody with required field."""
    yaml_content = textwrap.dedent(
        """
        required: true
        content:
          application/json:
            schema:
              type: object
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = request_body.build(root)
    assert isinstance(result, request_body.RequestBody)

    assert result.required is not None
    assert result.required.value is True


def test_build_with_all_fields():
    """Test building RequestBody with all fields."""
    yaml_content = textwrap.dedent(
        """
        description: user to add to the system
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                name:
                  type: string
                email:
                  type: string
          application/xml:
            schema:
              type: object
        x-custom: value
        x-internal: true
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = request_body.build(root)
    assert isinstance(result, request_body.RequestBody)

    assert result.description is not None
    assert result.description.value == "user to add to the system"
    assert result.required is not None
    assert result.required.value is True
    assert result.content is not None
    assert len(result.content.value) == 2

    # Check extensions
    assert len(result.extensions) == 2
    ext_dict = {k.value: v.value for k, v in result.extensions.items()}
    assert ext_dict["x-custom"] == "value"
    assert ext_dict["x-internal"] is True


def test_build_with_multiple_media_types():
    """Test building RequestBody with multiple media types."""
    yaml_content = textwrap.dedent(
        """
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
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = request_body.build(root)
    assert isinstance(result, request_body.RequestBody)

    assert result.content is not None
    assert len(result.content.value) == 3

    content_keys = {k.value for k in result.content.value.keys()}
    assert content_keys == {"application/json", "application/xml", "text/plain"}

    # Verify all are MediaType objects
    for media_type_value in result.content.value.values():
        assert isinstance(media_type_value, MediaType)
        assert media_type_value.schema is not None


def test_build_with_empty_object():
    """Test building RequestBody from empty YAML object."""
    yaml_content = "{}"
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = request_body.build(root)
    assert isinstance(result, request_body.RequestBody)

    assert result.root_node == root
    assert result.description is None
    assert result.content is None
    assert result.required is None
    assert result.extensions == {}


def test_build_with_invalid_node_returns_value_source():
    """Test that build returns ValueSource for non-mapping nodes."""
    yaml_parser = YAML()

    # Scalar node
    scalar_root = yaml_parser.compose("not-a-request-body")
    result = request_body.build(scalar_root)
    assert isinstance(result, ValueSource)
    assert result.value == "not-a-request-body"
    assert result.value_node == scalar_root

    # Sequence node
    sequence_root = yaml_parser.compose("['item1', 'item2']")
    result = request_body.build(sequence_root)
    assert isinstance(result, ValueSource)
    assert result.value == ["item1", "item2"]
    assert result.value_node == sequence_root


def test_build_preserves_invalid_types():
    """Test that build preserves values even with 'wrong' types."""
    yaml_content = textwrap.dedent(
        """
        description: 12345
        required: not-a-boolean
        content: invalid-value
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = request_body.build(root)
    assert isinstance(result, request_body.RequestBody)

    # Should preserve the actual values, not convert them
    assert result.description is not None
    assert result.description.value == 12345

    assert result.required is not None
    assert result.required.value == "not-a-boolean"

    assert result.content is not None
    assert result.content.value == "invalid-value"


def test_build_with_custom_context():
    """Test building RequestBody with a custom context."""
    yaml_content = textwrap.dedent(
        """
        description: test request body
        content:
          application/json:
            schema:
              type: string
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    custom_context = Context()
    result = request_body.build(root, context=custom_context)
    assert isinstance(result, request_body.RequestBody)

    assert isinstance(result.description, FieldSource)
    assert result.description.value == "test request body"


def test_source_tracking():
    """Test that source location information is preserved."""
    yaml_content = textwrap.dedent(
        """
        description: test request body
        required: true
        content:
          application/json:
            schema:
              type: string
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = request_body.build(root)
    assert isinstance(result, request_body.RequestBody)

    # Check description source tracking
    assert isinstance(result.description, FieldSource)
    assert result.description.key_node is not None
    assert result.description.value_node is not None
    assert result.description.key_node.value == "description"

    # Check required source tracking
    assert isinstance(result.required, FieldSource)
    assert result.required.key_node is not None
    assert result.required.value_node is not None
    assert result.required.key_node.value == "required"

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
        required:
        content:
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = request_body.build(root)
    assert isinstance(result, request_body.RequestBody)

    assert result.description is not None
    assert result.description.value is None

    assert result.required is not None
    assert result.required.value is None

    assert result.content is not None
    assert result.content.value is None


def test_build_with_complex_extensions():
    """Test building RequestBody with complex extension objects."""
    yaml_content = textwrap.dedent(
        """
        content:
          application/json:
            schema:
              type: object
        x-validation:
          strict: true
          sanitize: false
        x-format: custom
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = request_body.build(root)
    assert isinstance(result, request_body.RequestBody)

    assert len(result.extensions) == 2
    ext_dict = {k.value: v.value for k, v in result.extensions.items()}

    # Check x-validation extension
    validation = ext_dict["x-validation"]
    assert isinstance(validation, CommentedMap)
    assert validation["strict"] is True
    assert validation["sanitize"] is False

    # Check x-format extension
    assert ext_dict["x-format"] == "custom"


def test_build_real_world_json_request_body():
    """Test a complete real-world application/json RequestBody."""
    yaml_content = textwrap.dedent(
        """
        description: user to add to the system
        required: true
        content:
          application/json:
            schema:
              type: object
              required:
                - username
                - email
              properties:
                username:
                  type: string
                email:
                  type: string
                  format: email
                firstName:
                  type: string
                lastName:
                  type: string
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = request_body.build(root)
    assert isinstance(result, request_body.RequestBody)

    assert result.description is not None
    assert result.description.value == "user to add to the system"
    assert result.required is not None
    assert result.required.value is True
    assert result.content is not None

    json_key = next(k for k in result.content.value.keys() if k.value == "application/json")
    json_media_type = result.content.value[json_key]
    assert isinstance(json_media_type, MediaType)
    assert json_media_type.schema is not None
    assert isinstance(json_media_type.schema.value, Schema)


def test_build_real_world_multipart_request_body():
    """Test a complete real-world multipart/form-data RequestBody."""
    yaml_content = textwrap.dedent(
        """
        description: Upload a file with metadata
        required: true
        content:
          multipart/form-data:
            schema:
              type: object
              properties:
                file:
                  type: string
                  format: binary
                metadata:
                  type: object
                  properties:
                    description:
                      type: string
            encoding:
              file:
                contentType: application/octet-stream
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = request_body.build(root)
    assert isinstance(result, request_body.RequestBody)

    assert result.content is not None
    multipart_key = next(k for k in result.content.value.keys() if k.value == "multipart/form-data")
    multipart_media_type = result.content.value[multipart_key]
    assert isinstance(multipart_media_type, MediaType)
    assert multipart_media_type.schema is not None
    assert multipart_media_type.encoding is not None


def test_content_source_tracking():
    """Test that content maintains proper source tracking."""
    yaml_content = textwrap.dedent(
        """
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

    result = request_body.build(root)
    assert isinstance(result, request_body.RequestBody)

    assert result.content is not None

    # Check that each content key has source tracking
    for content_key, content_value in result.content.value.items():
        assert isinstance(content_key, KeySource)
        assert content_key.key_node is not None

        # Check that the MediaType has proper root_node
        assert isinstance(content_value, MediaType)
        assert content_value.root_node is not None


def test_build_request_body_or_reference_with_request_body():
    """Test build_request_body_or_reference with a RequestBody object."""
    yaml_content = textwrap.dedent(
        """
        description: test request body
        content:
          application/json:
            schema:
              type: string
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    context = Context()
    result = request_body.build_request_body_or_reference(root, context)
    assert isinstance(result, request_body.RequestBody)
    assert result.description is not None
    assert result.description.value == "test request body"


def test_build_request_body_or_reference_with_reference():
    """Test build_request_body_or_reference with a $ref."""
    yaml_content = textwrap.dedent(
        """
        $ref: '#/components/requestBodies/UserRequest'
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    context = Context()
    result = request_body.build_request_body_or_reference(root, context)
    assert isinstance(result, Reference)
    assert result.ref is not None
    assert result.ref.value == "#/components/requestBodies/UserRequest"


def test_build_request_body_or_reference_with_invalid_node():
    """Test build_request_body_or_reference with invalid node."""
    yaml_parser = YAML()
    root = yaml_parser.compose("invalid-scalar")

    context = Context()
    result = request_body.build_request_body_or_reference(root, context)
    assert isinstance(result, ValueSource)
    assert result.value == "invalid-scalar"


def test_build_with_commonmark_description():
    """Test building RequestBody with CommonMark description."""
    yaml_content = textwrap.dedent(
        """
        description: |
          # User Request Body

          This request body contains **user data**.

          - username
          - email
        content:
          application/json:
            schema:
              type: object
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = request_body.build(root)
    assert isinstance(result, request_body.RequestBody)

    assert result.description is not None
    assert "# User Request Body" in result.description.value
    assert "**user data**" in result.description.value


def test_build_with_content_examples():
    """Test building RequestBody with content containing examples."""
    yaml_content = textwrap.dedent(
        """
        content:
          application/json:
            schema:
              type: object
            examples:
              user1:
                value:
                  username: johndoe
                  email: john@example.com
              user2:
                value:
                  username: janedoe
                  email: jane@example.com
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = request_body.build(root)
    assert isinstance(result, request_body.RequestBody)

    assert result.content is not None
    json_key = next(k for k in result.content.value.keys() if k.value == "application/json")
    json_media_type = result.content.value[json_key]
    assert isinstance(json_media_type, MediaType)
    assert json_media_type.examples is not None
    assert len(json_media_type.examples.value) == 2


def test_build_with_invalid_content_data():
    """Test that invalid content data is preserved."""
    yaml_content = textwrap.dedent(
        """
        content:
          application/json: invalid-string-not-object
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = request_body.build(root)
    assert isinstance(result, request_body.RequestBody)

    assert result.content is not None
    assert len(result.content.value) == 1

    content_keys = list(result.content.value.keys())
    assert content_keys[0].value == "application/json"
    # The invalid data should be preserved - child builder returns ValueSource
    content_value = result.content.value[content_keys[0]]
    assert isinstance(content_value, ValueSource)
    assert content_value.value == "invalid-string-not-object"


def test_build_with_required_false():
    """Test building RequestBody with required set to false."""
    yaml_content = textwrap.dedent(
        """
        required: false
        content:
          application/json:
            schema:
              type: object
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = request_body.build(root)
    assert isinstance(result, request_body.RequestBody)

    assert result.required is not None
    assert result.required.value is False
