"""Tests for Reference low-level datamodel."""

import textwrap

from ruamel.yaml import YAML

from jentic.apitools.openapi.datamodels.low.context import Context
from jentic.apitools.openapi.datamodels.low.sources import FieldSource, ValueSource
from jentic.apitools.openapi.datamodels.low.v30 import reference


def test_build_with_ref_only():
    """Test building Reference with only $ref field."""
    yaml_content = textwrap.dedent(
        """
        $ref: '#/components/schemas/Pet'
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = reference.build(root)
    assert isinstance(result, reference.Reference)

    assert result.root_node == root

    # Check $ref field
    assert isinstance(result.ref, FieldSource)
    assert result.ref.value == "#/components/schemas/Pet"
    assert result.ref.key_node is not None
    assert result.ref.value_node is not None


def test_build_with_external_ref():
    """Test building Reference with external $ref."""
    yaml_content = textwrap.dedent(
        """
        $ref: 'https://example.com/schemas/Pet.yaml'
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = reference.build(root)
    assert isinstance(result, reference.Reference)

    assert result.ref is not None
    assert result.ref.value == "https://example.com/schemas/Pet.yaml"


def test_build_with_relative_ref():
    """Test building Reference with relative $ref."""
    yaml_content = textwrap.dedent(
        """
        $ref: './schemas/Pet.yaml#/Pet'
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = reference.build(root)
    assert isinstance(result, reference.Reference)

    assert result.ref is not None
    assert result.ref.value == "./schemas/Pet.yaml#/Pet"


def test_build_preserves_invalid_types():
    """Test that build preserves values even with 'wrong' types (low-level model principle)."""
    yaml_content = textwrap.dedent(
        """
        $ref: 123
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = reference.build(root)
    assert isinstance(result, reference.Reference)

    assert result.ref is not None

    # Should preserve the actual invalid value
    assert result.ref.value == 123


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


def test_build_with_custom_context():
    """Test building Reference with a custom context."""
    yaml_content = textwrap.dedent(
        """
        $ref: '#/components/schemas/CustomType'
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    custom_context = Context()
    result = reference.build(root, context=custom_context)
    assert isinstance(result, reference.Reference)

    assert result.ref is not None
    assert result.ref.value == "#/components/schemas/CustomType"


def test_source_tracking():
    """Test that source location information is preserved."""
    yaml_content = textwrap.dedent(
        """
        $ref: '#/components/schemas/Pet'
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = reference.build(root)
    assert isinstance(result, reference.Reference)

    assert result.ref is not None

    # Check that key_node and value_node are tracked
    assert result.ref.key_node is not None
    assert result.ref.value_node is not None

    # Verify key_node contains correct field name
    assert result.ref.key_node.value == "$ref"


def test_build_with_empty_object():
    """Test building Reference with empty object."""
    yaml_content = textwrap.dedent(
        """
        {}
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = reference.build(root)
    assert isinstance(result, reference.Reference)

    # $ref should be None
    assert result.ref is None


def test_build_with_null_ref():
    """Test building Reference with null $ref value."""
    yaml_content = textwrap.dedent(
        """
        $ref:
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = reference.build(root)
    assert isinstance(result, reference.Reference)

    assert result.ref is not None
    assert result.ref.value is None


def test_build_with_component_refs():
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


def test_build_with_url_encoded_ref():
    """Test building Reference with URL-encoded characters in $ref."""
    yaml_content = textwrap.dedent(
        """
        $ref: '#/components/schemas/My%20Pet'
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = reference.build(root)
    assert isinstance(result, reference.Reference)

    assert result.ref is not None
    assert result.ref.value == "#/components/schemas/My%20Pet"


def test_build_ignores_non_ref_fields():
    """Test that build ignores fields other than $ref (for OpenAPI 3.0)."""
    yaml_content = textwrap.dedent(
        """
        $ref: '#/components/schemas/Pet'
        summary: This should be ignored in OpenAPI 3.0
        description: This too
        x-custom: Also ignored
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = reference.build(root)
    assert isinstance(result, reference.Reference)

    assert result.ref is not None
    # Only $ref should be present
    assert result.ref.value == "#/components/schemas/Pet"
    # Reference object in OpenAPI 3.0 only has ref field
    assert not hasattr(result, "summary")
    assert not hasattr(result, "description")
    assert not hasattr(result, "extensions")
