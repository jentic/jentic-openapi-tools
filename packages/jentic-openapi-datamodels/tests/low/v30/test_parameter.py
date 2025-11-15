"""Tests for Parameter low-level datamodel."""

import textwrap

from ruamel.yaml import YAML

from jentic.apitools.openapi.datamodels.low.context import Context
from jentic.apitools.openapi.datamodels.low.sources import FieldSource, KeySource, ValueSource
from jentic.apitools.openapi.datamodels.low.v30 import parameter
from jentic.apitools.openapi.datamodels.low.v30.example import Example
from jentic.apitools.openapi.datamodels.low.v30.media_type import MediaType
from jentic.apitools.openapi.datamodels.low.v30.reference import Reference
from jentic.apitools.openapi.datamodels.low.v30.schema import Schema


def test_build_with_required_fields_only():
    """Test building Parameter with only required fields (name and in)."""
    yaml_content = textwrap.dedent(
        """
        name: userId
        in: path
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = parameter.build(root)
    assert isinstance(result, parameter.Parameter)

    assert result.name is not None
    assert result.name.value == "userId"
    assert result.in_ is not None
    assert result.in_.value == "path"


def test_build_with_path_parameter():
    """Test building a path parameter."""
    yaml_content = textwrap.dedent(
        """
        name: id
        in: path
        required: true
        schema:
          type: integer
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = parameter.build(root)
    assert isinstance(result, parameter.Parameter)

    assert result.name is not None
    assert result.name.value == "id"
    assert result.in_ is not None
    assert result.in_.value == "path"
    assert result.required is not None
    assert result.required.value is True
    assert result.schema is not None
    assert isinstance(result.schema.value, Schema)


def test_build_with_query_parameter():
    """Test building a query parameter."""
    yaml_content = textwrap.dedent(
        """
        name: page
        in: query
        schema:
          type: integer
          default: 1
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = parameter.build(root)
    assert isinstance(result, parameter.Parameter)

    assert result.name is not None
    assert result.name.value == "page"
    assert result.in_ is not None
    assert result.in_.value == "query"
    assert result.schema is not None
    assert isinstance(result.schema.value, Schema)


def test_build_with_header_parameter():
    """Test building a header parameter."""
    yaml_content = textwrap.dedent(
        """
        name: X-Request-ID
        in: header
        required: true
        schema:
          type: string
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = parameter.build(root)
    assert isinstance(result, parameter.Parameter)

    assert result.name is not None
    assert result.name.value == "X-Request-ID"
    assert result.in_ is not None
    assert result.in_.value == "header"
    assert result.required is not None
    assert result.required.value is True


def test_build_with_cookie_parameter():
    """Test building a cookie parameter."""
    yaml_content = textwrap.dedent(
        """
        name: sessionId
        in: cookie
        schema:
          type: string
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = parameter.build(root)
    assert isinstance(result, parameter.Parameter)

    assert result.name is not None
    assert result.name.value == "sessionId"
    assert result.in_ is not None
    assert result.in_.value == "cookie"


def test_build_with_description():
    """Test building Parameter with description."""
    yaml_content = textwrap.dedent(
        """
        name: userId
        in: path
        description: The unique identifier for a user
        required: true
        schema:
          type: string
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = parameter.build(root)
    assert isinstance(result, parameter.Parameter)

    assert result.description is not None
    assert result.description.value == "The unique identifier for a user"


def test_build_with_deprecated():
    """Test building Parameter with deprecated flag."""
    yaml_content = textwrap.dedent(
        """
        name: oldParam
        in: query
        deprecated: true
        schema:
          type: string
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = parameter.build(root)
    assert isinstance(result, parameter.Parameter)

    assert result.deprecated is not None
    assert result.deprecated.value is True


def test_build_with_allow_empty_value():
    """Test building Parameter with allowEmptyValue."""
    yaml_content = textwrap.dedent(
        """
        name: filter
        in: query
        allowEmptyValue: true
        schema:
          type: string
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = parameter.build(root)
    assert isinstance(result, parameter.Parameter)

    assert result.allow_empty_value is not None
    assert result.allow_empty_value.value is True


def test_build_with_style_and_explode():
    """Test building Parameter with style and explode."""
    yaml_content = textwrap.dedent(
        """
        name: ids
        in: query
        style: form
        explode: true
        schema:
          type: array
          items:
            type: integer
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = parameter.build(root)
    assert isinstance(result, parameter.Parameter)

    assert result.style is not None
    assert result.style.value == "form"
    assert result.explode is not None
    assert result.explode.value is True


def test_build_with_allow_reserved():
    """Test building Parameter with allowReserved."""
    yaml_content = textwrap.dedent(
        """
        name: url
        in: query
        allowReserved: true
        schema:
          type: string
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = parameter.build(root)
    assert isinstance(result, parameter.Parameter)

    assert result.allow_reserved is not None
    assert result.allow_reserved.value is True


def test_build_with_example():
    """Test building Parameter with example."""
    yaml_content = textwrap.dedent(
        """
        name: userId
        in: query
        schema:
          type: integer
        example: 12345
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = parameter.build(root)
    assert isinstance(result, parameter.Parameter)

    assert result.example is not None
    assert result.example.value == 12345


def test_build_with_examples():
    """Test building Parameter with examples."""
    yaml_content = textwrap.dedent(
        """
        name: status
        in: query
        schema:
          type: string
        examples:
          active:
            value: active
          inactive:
            value: inactive
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = parameter.build(root)
    assert isinstance(result, parameter.Parameter)

    assert result.examples is not None
    assert len(result.examples.value) == 2
    example_keys = {k.value for k in result.examples.value.keys()}
    assert example_keys == {"active", "inactive"}

    # Check that examples are Example objects
    for example_value in result.examples.value.values():
        assert isinstance(example_value, Example)


def test_build_with_examples_reference():
    """Test building Parameter with example references."""
    yaml_content = textwrap.dedent(
        """
        name: status
        in: query
        schema:
          type: string
        examples:
          active:
            $ref: '#/components/examples/ActiveStatus'
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = parameter.build(root)
    assert isinstance(result, parameter.Parameter)

    assert result.examples is not None
    key_active = next(k for k in result.examples.value.keys() if k.value == "active")
    assert isinstance(result.examples.value[key_active], Reference)


def test_build_with_schema_reference():
    """Test building Parameter with schema reference."""
    yaml_content = textwrap.dedent(
        """
        name: userId
        in: path
        required: true
        schema:
          $ref: '#/components/schemas/UserId'
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = parameter.build(root)
    assert isinstance(result, parameter.Parameter)

    assert result.schema is not None
    assert isinstance(result.schema.value, Reference)
    assert result.schema.value.ref is not None
    assert result.schema.value.ref.value == "#/components/schemas/UserId"


def test_build_with_content():
    """Test building Parameter with content field."""
    yaml_content = textwrap.dedent(
        """
        name: coordinates
        in: query
        content:
          application/json:
            schema:
              type: object
              properties:
                lat:
                  type: number
                lng:
                  type: number
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = parameter.build(root)
    assert isinstance(result, parameter.Parameter)

    assert result.content is not None
    assert len(result.content.value) == 1
    content_keys = {k.value for k in result.content.value.keys()}
    assert "application/json" in content_keys

    # Check that content is MediaType object
    key_json = next(k for k in result.content.value.keys() if k.value == "application/json")
    assert isinstance(result.content.value[key_json], MediaType)


def test_build_with_all_fields():
    """Test building Parameter with all possible fields."""
    yaml_content = textwrap.dedent(
        """
        name: userId
        in: query
        description: User identifier
        required: false
        deprecated: false
        allowEmptyValue: false
        style: form
        explode: false
        allowReserved: false
        schema:
          type: integer
        example: 123
        x-custom: value
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = parameter.build(root)
    assert isinstance(result, parameter.Parameter)

    assert result.name is not None
    assert result.name.value == "userId"
    assert result.in_ is not None
    assert result.in_.value == "query"
    assert result.description is not None
    assert result.description.value == "User identifier"
    assert result.required is not None
    assert result.required.value is False
    assert result.deprecated is not None
    assert result.deprecated.value is False
    assert result.allow_empty_value is not None
    assert result.allow_empty_value.value is False
    assert result.style is not None
    assert result.style.value == "form"
    assert result.explode is not None
    assert result.explode.value is False
    assert result.allow_reserved is not None
    assert result.allow_reserved.value is False
    assert result.schema is not None
    assert result.example is not None
    assert result.example.value == 123
    assert len(result.extensions) == 1


def test_build_with_extensions():
    """Test building Parameter with specification extensions."""
    yaml_content = textwrap.dedent(
        """
        name: userId
        in: path
        required: true
        schema:
          type: string
        x-internal: true
        x-rate-limit: 100
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = parameter.build(root)
    assert isinstance(result, parameter.Parameter)

    assert len(result.extensions) == 2
    ext_dict = {k.value: v.value for k, v in result.extensions.items()}
    assert ext_dict["x-internal"] is True
    assert ext_dict["x-rate-limit"] == 100


def test_build_with_empty_object():
    """Test building Parameter from empty YAML object."""
    yaml_content = "{}"
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = parameter.build(root)
    assert isinstance(result, parameter.Parameter)

    assert result.root_node == root
    assert result.name is None
    assert result.in_ is None
    assert result.extensions == {}


def test_build_with_invalid_node_returns_value_source():
    """Test that build returns ValueSource for non-mapping nodes."""
    yaml_parser = YAML()

    # Scalar node
    scalar_root = yaml_parser.compose("not-a-parameter-object")
    result = parameter.build(scalar_root)
    assert isinstance(result, ValueSource)
    assert result.value == "not-a-parameter-object"
    assert result.value_node == scalar_root

    # Sequence node
    sequence_root = yaml_parser.compose("['name', 'in']")
    result = parameter.build(sequence_root)
    assert isinstance(result, ValueSource)
    assert result.value == ["name", "in"]
    assert result.value_node == sequence_root


def test_build_preserves_invalid_types():
    """Test that build preserves invalid field values."""
    yaml_content = textwrap.dedent(
        """
        name: 12345
        in: invalid-location
        required: not-a-boolean
        schema:
          type: string
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = parameter.build(root)
    assert isinstance(result, parameter.Parameter)

    # All invalid values should be preserved
    assert result.name is not None
    assert result.name.value == 12345
    assert result.in_ is not None
    assert result.in_.value == "invalid-location"
    assert result.required is not None
    assert result.required.value == "not-a-boolean"


def test_build_with_custom_context():
    """Test building Parameter with a custom context."""
    yaml_content = textwrap.dedent(
        """
        name: userId
        in: path
        required: true
        schema:
          type: integer
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    custom_context = Context()
    result = parameter.build(root, context=custom_context)
    assert isinstance(result, parameter.Parameter)

    assert result.name is not None
    assert result.name.value == "userId"


def test_source_tracking():
    """Test that source location information is preserved."""
    yaml_content = textwrap.dedent(
        """
        name: userId
        in: path
        required: true
        schema:
          type: integer
        x-custom: value
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = parameter.build(root)
    assert isinstance(result, parameter.Parameter)

    # Check field source tracking
    assert isinstance(result.name, FieldSource)
    assert result.name.key_node is not None
    assert result.name.value_node is not None
    assert result.name.key_node.value == "name"

    # Check extension source tracking
    for key_source, value_source in result.extensions.items():
        assert isinstance(key_source, KeySource)
        assert key_source.key_node is not None
        assert isinstance(value_source, ValueSource)
        assert value_source.value_node is not None

    # Check line numbers are available
    assert hasattr(result.name.key_node.start_mark, "line")
    assert hasattr(result.name.value_node.start_mark, "line")


def test_build_with_null_values():
    """Test that build preserves null values."""
    yaml_content = textwrap.dedent(
        """
        name: userId
        in: path
        description:
        required: true
        schema:
          type: string
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = parameter.build(root)
    assert isinstance(result, parameter.Parameter)

    assert result.description is not None
    assert result.description.value is None


def test_build_with_commonmark_description():
    """Test building Parameter with CommonMark description."""
    yaml_content = textwrap.dedent(
        """
        name: userId
        in: path
        description: |
          The **user identifier**

          See [documentation](https://example.com) for details.
        required: true
        schema:
          type: string
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = parameter.build(root)
    assert isinstance(result, parameter.Parameter)

    assert result.description is not None
    assert "**user identifier**" in result.description.value
    assert "[documentation]" in result.description.value


def test_build_real_world_pagination_parameter():
    """Test a complete real-world pagination parameter."""
    yaml_content = textwrap.dedent(
        """
        name: page
        in: query
        description: Page number for pagination
        required: false
        schema:
          type: integer
          minimum: 1
          default: 1
        example: 2
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = parameter.build(root)
    assert isinstance(result, parameter.Parameter)

    assert result.name is not None
    assert result.name.value == "page"
    assert result.in_ is not None
    assert result.in_.value == "query"
    assert result.required is not None
    assert result.required.value is False
    assert result.schema is not None
    assert result.example is not None
    assert result.example.value == 2


def test_build_real_world_array_parameter():
    """Test a real-world array parameter with style and explode."""
    yaml_content = textwrap.dedent(
        """
        name: tags
        in: query
        description: Filter by tags
        style: form
        explode: true
        schema:
          type: array
          items:
            type: string
        examples:
          singleTag:
            value: [technology]
          multipleTags:
            value: [technology, science]
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = parameter.build(root)
    assert isinstance(result, parameter.Parameter)

    assert result.name is not None
    assert result.name.value == "tags"
    assert result.style is not None
    assert result.style.value == "form"
    assert result.explode is not None
    assert result.explode.value is True
    assert result.examples is not None
    assert len(result.examples.value) == 2


def test_examples_source_tracking():
    """Test source tracking for examples field."""
    yaml_content = textwrap.dedent(
        """
        name: status
        in: query
        schema:
          type: string
        examples:
          active:
            value: active
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = parameter.build(root)
    assert isinstance(result, parameter.Parameter)

    assert result.examples is not None
    for key_source in result.examples.value.keys():
        assert isinstance(key_source, KeySource)
        assert key_source.key_node is not None


def test_content_source_tracking():
    """Test source tracking for content field."""
    yaml_content = textwrap.dedent(
        """
        name: data
        in: query
        content:
          application/json:
            schema:
              type: object
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = parameter.build(root)
    assert isinstance(result, parameter.Parameter)

    assert result.content is not None
    for key_source in result.content.value.keys():
        assert isinstance(key_source, KeySource)
        assert key_source.key_node is not None


def test_build_with_invalid_examples_data():
    """Test that invalid examples data is preserved."""
    yaml_content = textwrap.dedent(
        """
        name: userId
        in: query
        schema:
          type: string
        examples: invalid-not-object
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = parameter.build(root)
    assert isinstance(result, parameter.Parameter)

    # Invalid examples should be preserved as-is
    assert result.examples is not None
    assert result.examples.value == "invalid-not-object"


def test_build_with_invalid_content_data():
    """Test that invalid content data is preserved."""
    yaml_content = textwrap.dedent(
        """
        name: data
        in: query
        content: invalid-string
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = parameter.build(root)
    assert isinstance(result, parameter.Parameter)

    # Invalid content should be preserved as-is
    assert result.content is not None
    assert result.content.value == "invalid-string"


def test_build_parameter_or_reference_with_parameter():
    """Test build_parameter_or_reference with a Parameter object."""
    yaml_content = textwrap.dedent(
        """
        name: userId
        in: path
        required: true
        schema:
          type: string
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = parameter.build_parameter_or_reference(root, Context())
    assert isinstance(result, parameter.Parameter)
    assert result.name is not None
    assert result.name.value == "userId"
    assert result.in_ is not None
    assert result.in_.value == "path"


def test_build_parameter_or_reference_with_reference():
    """Test build_parameter_or_reference with a Reference object."""
    yaml_content = textwrap.dedent(
        """
        $ref: '#/components/parameters/UserId'
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = parameter.build_parameter_or_reference(root, Context())
    assert isinstance(result, Reference)
    assert result.ref is not None
    assert result.ref.value == "#/components/parameters/UserId"


def test_build_parameter_or_reference_with_invalid_data():
    """Test build_parameter_or_reference with invalid data."""
    yaml_parser = YAML()

    # Scalar node
    scalar_root = yaml_parser.compose("not-a-parameter")
    result = parameter.build_parameter_or_reference(scalar_root, Context())
    assert isinstance(result, ValueSource)
    assert result.value == "not-a-parameter"
