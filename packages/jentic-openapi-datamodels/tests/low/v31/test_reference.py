"""Tests for Reference low-level datamodel."""

import textwrap

from ruamel.yaml import YAML

from jentic.apitools.openapi.datamodels.low.context import Context
from jentic.apitools.openapi.datamodels.low.sources import FieldSource, ValueSource
from jentic.apitools.openapi.datamodels.low.v31 import reference


def test_build_with_ref_only(parse_yaml):
    """Test building Reference with only $ref field."""
    yaml_content = textwrap.dedent(
        """
        $ref: '#/components/schemas/Pet'
        """
    )
    root = parse_yaml(yaml_content)

    result = reference.build(root)
    assert isinstance(result, reference.Reference)

    assert result.root_node == root

    # Check $ref field
    assert isinstance(result.ref, FieldSource)
    assert result.ref.value == "#/components/schemas/Pet"
    assert result.ref.key_node is not None
    assert result.ref.value_node is not None

    # v3.1 fields should be None when not provided
    assert result.summary is None
    assert result.description is None


def test_build_with_summary(parse_yaml):
    """Test building Reference with $ref and summary (new in OpenAPI 3.1)."""
    yaml_content = textwrap.dedent(
        """
        $ref: '#/components/schemas/Pet'
        summary: A Pet reference
        """
    )
    root = parse_yaml(yaml_content)

    result = reference.build(root)
    assert isinstance(result, reference.Reference)

    assert result.ref is not None
    assert result.ref.value == "#/components/schemas/Pet"

    # Check summary field
    assert isinstance(result.summary, FieldSource)
    assert result.summary.value == "A Pet reference"
    assert result.summary.key_node is not None
    assert result.summary.value_node is not None


def test_build_with_description(parse_yaml):
    """Test building Reference with $ref and description (new in OpenAPI 3.1)."""
    yaml_content = textwrap.dedent(
        """
        $ref: '#/components/schemas/Pet'
        description: Reference to the Pet schema in components
        """
    )
    root = parse_yaml(yaml_content)

    result = reference.build(root)
    assert isinstance(result, reference.Reference)

    assert result.ref is not None
    assert result.ref.value == "#/components/schemas/Pet"

    # Check description field
    assert isinstance(result.description, FieldSource)
    assert result.description.value == "Reference to the Pet schema in components"
    assert result.description.key_node is not None
    assert result.description.value_node is not None


def test_build_with_all_fields(parse_yaml):
    """Test building Reference with $ref, summary, and description."""
    yaml_content = textwrap.dedent(
        """
        $ref: '#/components/schemas/Pet'
        summary: A Pet reference
        description: Reference to the Pet schema in components
        """
    )
    root = parse_yaml(yaml_content)

    result = reference.build(root)
    assert isinstance(result, reference.Reference)

    # Check all fields
    assert result.ref is not None
    assert result.ref.value == "#/components/schemas/Pet"

    assert result.summary is not None
    assert result.summary.value == "A Pet reference"

    assert result.description is not None
    assert result.description.value == "Reference to the Pet schema in components"


def test_build_with_description_markdown(parse_yaml):
    """Test building Reference with CommonMark description."""
    yaml_content = textwrap.dedent(
        """
        $ref: '#/components/schemas/Pet'
        description: |
          Reference to **Pet** schema.

          See [Pet documentation](https://example.com/pets) for more details.
        """
    )
    root = parse_yaml(yaml_content)

    result = reference.build(root)
    assert isinstance(result, reference.Reference)

    assert result.description is not None
    assert "**Pet**" in result.description.value
    assert "[Pet documentation]" in result.description.value


def test_build_with_external_ref(parse_yaml):
    """Test building Reference with external $ref."""
    yaml_content = textwrap.dedent(
        """
        $ref: 'https://example.com/schemas/Pet.yaml'
        """
    )
    root = parse_yaml(yaml_content)

    result = reference.build(root)
    assert isinstance(result, reference.Reference)

    assert result.ref is not None
    assert result.ref.value == "https://example.com/schemas/Pet.yaml"


def test_build_with_relative_ref(parse_yaml):
    """Test building Reference with relative $ref."""
    yaml_content = textwrap.dedent(
        """
        $ref: './schemas/Pet.yaml#/Pet'
        """
    )
    root = parse_yaml(yaml_content)

    result = reference.build(root)
    assert isinstance(result, reference.Reference)

    assert result.ref is not None
    assert result.ref.value == "./schemas/Pet.yaml#/Pet"


def test_build_preserves_invalid_types(parse_yaml):
    """Test that build preserves values even with 'wrong' types (low-level model principle)."""
    yaml_content = textwrap.dedent(
        """
        $ref: 123
        summary: 456
        description: ['invalid', 'array']
        """
    )
    root = parse_yaml(yaml_content)

    result = reference.build(root)
    assert isinstance(result, reference.Reference)

    # Should preserve the actual invalid values
    assert result.ref is not None
    assert result.ref.value == 123

    assert result.summary is not None
    assert result.summary.value == 456

    assert result.description is not None
    assert result.description.value == ["invalid", "array"]


def test_build_with_invalid_node_returns_none():
    """Test that build returns ValueSource for non-mapping nodes (preserves invalid data)."""
    yaml_parser = YAML()

    # Scalar node
    scalar_root = yaml_parser.compose("just-a-string")
    result = reference.build(scalar_root)
    assert isinstance(result, ValueSource)
    assert result.value == "just-a-string"
    assert result.value_node == scalar_root

    # Sequence node
    sequence_root = yaml_parser.compose("['item1', 'item2']")
    result = reference.build(sequence_root)
    assert isinstance(result, ValueSource)
    assert result.value == ["item1", "item2"]
    assert result.value_node == sequence_root


def test_build_with_custom_context(parse_yaml):
    """Test building Reference with a custom context."""
    yaml_content = textwrap.dedent(
        """
        $ref: '#/components/schemas/CustomType'
        summary: Custom reference
        """
    )
    root = parse_yaml(yaml_content)

    custom_context = Context()
    result = reference.build(root, context=custom_context)
    assert isinstance(result, reference.Reference)

    assert result.ref is not None
    assert result.ref.value == "#/components/schemas/CustomType"

    assert result.summary is not None
    assert result.summary.value == "Custom reference"


def test_source_tracking(parse_yaml):
    """Test that source location information is preserved."""
    yaml_content = textwrap.dedent(
        """
        $ref: '#/components/schemas/Pet'
        summary: Pet reference
        description: A reference to Pet
        """
    )
    root = parse_yaml(yaml_content)

    result = reference.build(root)
    assert isinstance(result, reference.Reference)

    # Check $ref source tracking
    assert result.ref is not None
    assert result.ref.key_node is not None
    assert result.ref.value_node is not None
    assert result.ref.key_node.value == "$ref"

    # Check summary source tracking
    assert result.summary is not None
    assert result.summary.key_node is not None
    assert result.summary.value_node is not None
    assert result.summary.key_node.value == "summary"

    # Check description source tracking
    assert result.description is not None
    assert result.description.key_node is not None
    assert result.description.value_node is not None
    assert result.description.key_node.value == "description"


def test_build_with_empty_object(parse_yaml):
    """Test building Reference with empty object."""
    yaml_content = textwrap.dedent(
        """
        {}
        """
    )
    root = parse_yaml(yaml_content)

    result = reference.build(root)
    assert isinstance(result, reference.Reference)

    # All fields should be None
    assert result.ref is None
    assert result.summary is None
    assert result.description is None


def test_build_with_null_ref(parse_yaml):
    """Test building Reference with null $ref value."""
    yaml_content = textwrap.dedent(
        """
        $ref:
        """
    )
    root = parse_yaml(yaml_content)

    result = reference.build(root)
    assert isinstance(result, reference.Reference)

    assert result.ref is not None
    assert result.ref.value is None


def test_build_with_null_summary(parse_yaml):
    """Test building Reference with null summary value."""
    yaml_content = textwrap.dedent(
        """
        $ref: '#/components/schemas/Pet'
        summary:
        """
    )
    root = parse_yaml(yaml_content)

    result = reference.build(root)
    assert isinstance(result, reference.Reference)

    assert result.summary is not None
    assert result.summary.value is None


def test_build_with_null_description(parse_yaml):
    """Test building Reference with null description value."""
    yaml_content = textwrap.dedent(
        """
        $ref: '#/components/schemas/Pet'
        description:
        """
    )
    root = parse_yaml(yaml_content)

    result = reference.build(root)
    assert isinstance(result, reference.Reference)

    assert result.description is not None
    assert result.description.value is None


def test_build_with_component_refs(parse_yaml):
    """Test building Reference with various component reference patterns."""
    test_cases = [
        "#/components/schemas/Pet",
        "#/components/responses/NotFound",
        "#/components/parameters/limit",
        "#/components/examples/frog-example",
        "#/components/requestBodies/body",
        "#/components/headers/X-Rate-Limit",
        "#/components/securitySchemes/api_key",
        "#/components/links/UserRepositories",
        "#/components/callbacks/myEvent",
    ]

    yaml_parser = YAML()

    for ref_string in test_cases:
        yaml_content = f"$ref: '{ref_string}'"
        root = yaml_parser.compose(yaml_content)
        result = reference.build(root)
        assert isinstance(result, reference.Reference)

        assert result.ref is not None
        assert result.ref.value == ref_string


def test_build_with_url_encoded_ref(parse_yaml):
    """Test building Reference with URL-encoded characters in $ref."""
    yaml_content = textwrap.dedent(
        """
        $ref: '#/components/schemas/My%20Pet'
        """
    )
    root = parse_yaml(yaml_content)

    result = reference.build(root)
    assert isinstance(result, reference.Reference)

    assert result.ref is not None
    assert result.ref.value == "#/components/schemas/My%20Pet"


def test_build_with_extensions(parse_yaml):
    """Test that build ignores extension fields (x-* fields) in OpenAPI 3.1."""
    yaml_content = textwrap.dedent(
        """
        $ref: '#/components/schemas/Pet'
        summary: A Pet reference
        x-custom: Custom extension
        x-internal-id: 12345
        """
    )
    root = parse_yaml(yaml_content)

    result = reference.build(root)
    assert isinstance(result, reference.Reference)

    assert result.ref is not None
    assert result.ref.value == "#/components/schemas/Pet"

    assert result.summary is not None
    assert result.summary.value == "A Pet reference"

    # Extensions are not part of Reference Object in v31
    # (Reference doesn't have extensions field unlike other objects)
    assert not hasattr(result, "extensions")
