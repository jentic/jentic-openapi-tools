"""Tests for Tag low-level datamodel."""

import textwrap

from ruamel.yaml import YAML

from jentic.apitools.openapi.datamodels.low.context import Context
from jentic.apitools.openapi.datamodels.low.sources import FieldSource, KeySource, ValueSource
from jentic.apitools.openapi.datamodels.low.v30 import tag
from jentic.apitools.openapi.datamodels.low.v30.external_documentation import (
    ExternalDocumentation,
)


def test_build_with_all_fields():
    """Test building Tag with all specification fields."""
    yaml_content = textwrap.dedent(
        """
        name: pet
        description: Everything about your Pets
        externalDocs:
          url: https://example.com/docs/pets
          description: Find more info here
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = tag.build(root)
    assert isinstance(result, tag.Tag)

    assert result.root_node == root

    # Check name field
    assert isinstance(result.name, FieldSource)
    assert result.name.value == "pet"
    assert result.name.key_node is not None
    assert result.name.value_node is not None

    # Check description field
    assert isinstance(result.description, FieldSource)
    assert result.description.value == "Everything about your Pets"

    # Check externalDocs field
    assert isinstance(result.external_docs, FieldSource)
    assert isinstance(result.external_docs.value, ExternalDocumentation)
    assert result.external_docs.value.url is not None
    assert result.external_docs.value.url.value == "https://example.com/docs/pets"
    assert result.external_docs.value.description is not None
    assert result.external_docs.value.description.value == "Find more info here"


def test_build_with_minimal_fields():
    """Test building Tag with only required field (name)."""
    yaml_content = textwrap.dedent(
        """
        name: pet
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = tag.build(root)
    assert isinstance(result, tag.Tag)

    assert result.root_node == root
    assert isinstance(result.name, FieldSource)
    assert result.name.value == "pet"

    # Optional fields should be None
    assert result.description is None
    assert result.external_docs is None
    # Extensions returns empty dict when no extensions present
    assert result.extensions == {}


def test_build_with_extensions():
    """Test building Tag with specification extensions (x-* fields)."""
    yaml_content = textwrap.dedent(
        """
        name: pet
        description: Pet operations
        x-custom: custom-value
        x-internal: true
        x-order: 1
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = tag.build(root)
    assert isinstance(result, tag.Tag)

    assert result.extensions is not None
    assert len(result.extensions) == 3

    # Extensions should be dict[KeySource, ValueSource]
    keys = list(result.extensions.keys())
    assert all(isinstance(k, KeySource) for k in keys)
    assert all(isinstance(v, ValueSource) for v in result.extensions.values())

    # Check extension values
    ext_dict = {k.value: v.value for k, v in result.extensions.items()}
    assert ext_dict["x-custom"] == "custom-value"
    assert ext_dict["x-internal"] is True
    assert ext_dict["x-order"] == 1


def test_build_preserves_invalid_types():
    """Test that build preserves values even with 'wrong' types (low-level model principle)."""
    yaml_content = textwrap.dedent(
        """
        name: 12345
        description: true
        externalDocs: not-an-object
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = tag.build(root)
    assert isinstance(result, tag.Tag)

    assert result.name is not None
    assert result.description is not None
    assert result.external_docs is not None

    # Should preserve the actual values, not convert them
    assert result.name.value == 12345
    assert result.description.value is True
    # For nested objects with invalid types, FieldSource auto-unwraps ValueSource
    # so the value is stored directly (not wrapped in ValueSource)
    assert isinstance(result.external_docs, FieldSource)
    assert result.external_docs.value == "not-an-object"


def test_build_with_empty_object():
    """Test building Tag from empty YAML object."""
    yaml_content = "{}"
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = tag.build(root)
    assert isinstance(result, tag.Tag)

    assert result.root_node == root
    assert result.name is None
    assert result.description is None
    assert result.external_docs is None
    # Extensions returns empty dict when no extensions present
    assert result.extensions == {}


def test_build_with_invalid_node_returns_value_source():
    """Test that build returns ValueSource for non-mapping nodes (preserves invalid data)."""
    yaml_parser = YAML()

    # Scalar node
    scalar_root = yaml_parser.compose("pet")
    result = tag.build(scalar_root)
    assert isinstance(result, ValueSource)
    assert result.value == "pet"
    assert result.value_node == scalar_root

    # Sequence node
    sequence_root = yaml_parser.compose("['pet', 'store']")
    result = tag.build(sequence_root)
    assert isinstance(result, ValueSource)
    assert result.value == ["pet", "store"]
    assert result.value_node == sequence_root


def test_build_with_custom_context():
    """Test building Tag with a custom context."""
    yaml_content = textwrap.dedent(
        """
        name: pet
        description: Pet operations
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    custom_context = Context()
    result = tag.build(root, context=custom_context)
    assert isinstance(result, tag.Tag)

    assert result.name is not None
    assert result.description is not None
    assert result.name.value == "pet"
    assert result.description.value == "Pet operations"


def test_source_tracking():
    """Test that source location information is preserved."""
    yaml_content = textwrap.dedent(
        """
        name: pet
        description: Everything about your Pets
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = tag.build(root)
    assert isinstance(result, tag.Tag)

    assert result.name is not None

    # Check that key_node and value_node are tracked
    assert result.name.key_node is not None
    assert result.name.value_node is not None

    # The key_node should contain "name"
    assert result.name.key_node.value == "name"

    # The value_node should contain "pet"
    assert result.name.value_node.value == "pet"

    # Check line numbers are available (for error reporting)
    assert hasattr(result.name.key_node.start_mark, "line")
    assert hasattr(result.name.value_node.start_mark, "line")


def test_mixed_extensions_and_fixed_fields():
    """Test that extensions and fixed fields are properly separated."""
    yaml_content = textwrap.dedent(
        """
        name: pet
        x-custom: value
        description: Pet operations
        x-another: 123
        externalDocs:
          url: https://example.com
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = tag.build(root)
    assert isinstance(result, tag.Tag)

    assert result.name is not None
    assert result.description is not None
    assert result.external_docs is not None

    # Fixed fields should be present
    assert result.name.value == "pet"
    assert result.description.value == "Pet operations"
    assert isinstance(result.external_docs.value, ExternalDocumentation)

    # Extensions should be in extensions dict
    assert result.extensions is not None
    assert len(result.extensions) == 2

    ext_dict = {k.value: v.value for k, v in result.extensions.items()}
    assert ext_dict["x-custom"] == "value"
    assert ext_dict["x-another"] == 123


def test_commonmark_description():
    """Test that description field can contain CommonMark formatted text."""
    yaml_content = textwrap.dedent(
        """
        name: pet
        description: |
          # Pet Operations

          All operations related to **pets** in the store.

          - Create pet
          - Read pet
          - Update pet
          - Delete pet
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = tag.build(root)
    assert isinstance(result, tag.Tag)

    assert result.description is not None
    # The low-level model should preserve the exact markdown content
    assert "# Pet Operations" in result.description.value
    assert "**pets**" in result.description.value
    assert "- Create pet" in result.description.value


def test_external_docs_with_extensions():
    """Test that externalDocs can have its own extensions."""
    yaml_content = textwrap.dedent(
        """
        name: pet
        externalDocs:
          url: https://example.com/pets
          description: Pet documentation
          x-internal: true
          x-version: "1.0"
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = tag.build(root)
    assert isinstance(result, tag.Tag)

    assert result.external_docs is not None
    assert isinstance(result.external_docs.value, ExternalDocumentation)

    external_docs = result.external_docs.value
    assert external_docs.url is not None
    assert external_docs.url.value == "https://example.com/pets"
    assert external_docs.description is not None
    assert external_docs.description.value == "Pet documentation"

    # Check extensions in the nested externalDocs object
    assert external_docs.extensions is not None
    assert len(external_docs.extensions) == 2

    ext_dict = {k.value: v.value for k, v in external_docs.extensions.items()}
    assert ext_dict["x-internal"] is True
    assert ext_dict["x-version"] == "1.0"


def test_multiple_tags():
    """Test building multiple Tag objects (as would appear in OpenAPI spec)."""
    yaml_content = textwrap.dedent(
        """
        - name: pet
          description: Everything about your Pets
        - name: store
          description: Access to Petstore orders
        - name: user
          description: Operations about user
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    # Root is a sequence, so we need to iterate
    assert hasattr(root, "value")  # SequenceNode has value attribute
    tags = [tag.build(node) for node in root.value]

    assert len(tags) == 3
    assert all(isinstance(t, tag.Tag) for t in tags)

    # Type narrow for accessing Tag attributes
    assert isinstance(tags[0], tag.Tag)
    assert isinstance(tags[1], tag.Tag)
    assert isinstance(tags[2], tag.Tag)

    assert tags[0].name is not None
    assert tags[0].name.value == "pet"
    assert tags[1].name is not None
    assert tags[1].name.value == "store"
    assert tags[2].name is not None
    assert tags[2].name.value == "user"

    assert tags[0].description is not None
    assert tags[0].description.value == "Everything about your Pets"
    assert tags[1].description is not None
    assert tags[1].description.value == "Access to Petstore orders"
    assert tags[2].description is not None
    assert tags[2].description.value == "Operations about user"
