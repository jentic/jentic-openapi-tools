"""Tests for Discriminator low-level datamodel."""

import textwrap

from ruamel.yaml import YAML

from jentic.apitools.openapi.datamodels.low.context import Context
from jentic.apitools.openapi.datamodels.low.sources import FieldSource, ValueSource
from jentic.apitools.openapi.datamodels.low.v31 import discriminator


def test_build_with_all_fields():
    """Test building Discriminator with all specification fields."""
    yaml_content = textwrap.dedent(
        """
        propertyName: petType
        mapping:
          dog: '#/components/schemas/Dog'
          cat: '#/components/schemas/Cat'
          bird: '#/components/schemas/Bird'
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = discriminator.build(root)
    assert isinstance(result, discriminator.Discriminator)

    assert result.root_node == root

    # Check propertyName
    assert isinstance(result.property_name, FieldSource)
    assert result.property_name.value == "petType"
    assert result.property_name.key_node is not None
    assert result.property_name.value_node is not None

    # Check mapping
    assert isinstance(result.mapping, FieldSource)
    assert isinstance(result.mapping.value, dict)

    # Extract values from KeySource/ValueSource wrappers
    mapping_dict = {k.value: v.value for k, v in result.mapping.value.items()}
    assert mapping_dict["dog"] == "#/components/schemas/Dog"
    assert mapping_dict["cat"] == "#/components/schemas/Cat"
    assert mapping_dict["bird"] == "#/components/schemas/Bird"


def test_build_with_required_field_only():
    """Test building Discriminator with only required propertyName field."""
    yaml_content = textwrap.dedent(
        """
        propertyName: objectType
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = discriminator.build(root)
    assert isinstance(result, discriminator.Discriminator)

    assert result.root_node == root
    assert isinstance(result.property_name, FieldSource)
    assert result.property_name.value == "objectType"

    # Mapping should be None
    assert result.mapping is None


def test_build_preserves_invalid_types():
    """Test that build preserves values even with 'wrong' types (low-level model principle)."""
    yaml_content = textwrap.dedent(
        """
        propertyName: 123
        mapping: not-a-dict
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = discriminator.build(root)
    assert isinstance(result, discriminator.Discriminator)

    assert result.property_name is not None
    assert result.mapping is not None

    # Should preserve the actual values, not convert them
    assert result.property_name.value == 123
    assert result.mapping.value == "not-a-dict"


def test_build_with_empty_mapping():
    """Test building Discriminator with empty mapping object."""
    yaml_content = textwrap.dedent(
        """
        propertyName: type
        mapping: {}
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = discriminator.build(root)
    assert isinstance(result, discriminator.Discriminator)

    assert result.property_name is not None
    assert result.property_name.value == "type"
    assert isinstance(result.mapping, FieldSource)
    assert result.mapping.value == {}


def test_build_with_invalid_node_returns_none():
    """Test that build returns ValueSource for non-mapping nodes (preserves invalid data)."""
    yaml_parser = YAML()

    # Scalar node
    scalar_root = yaml_parser.compose("just-a-string")
    result = discriminator.build(scalar_root)
    assert isinstance(result, ValueSource)
    assert result.value == "just-a-string"
    assert result.value_node == scalar_root

    # Sequence node
    sequence_root = yaml_parser.compose("['item1', 'item2']")
    result = discriminator.build(sequence_root)
    assert isinstance(result, ValueSource)
    assert result.value == ["item1", "item2"]
    assert result.value_node == sequence_root


def test_build_with_custom_context():
    """Test building Discriminator with a custom context."""
    yaml_content = textwrap.dedent(
        """
        propertyName: discriminatorField
        mapping:
          option1: Schema1
          option2: Schema2
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    custom_context = Context()
    result = discriminator.build(root, context=custom_context)
    assert isinstance(result, discriminator.Discriminator)

    assert result.property_name is not None
    assert result.property_name.value == "discriminatorField"

    # Extract values from KeySource/ValueSource wrappers
    assert result.mapping is not None
    mapping_dict = {k.value: v.value for k, v in result.mapping.value.items()}
    assert mapping_dict["option1"] == "Schema1"


def test_source_tracking():
    """Test that source location information is preserved."""
    yaml_content = textwrap.dedent(
        """
        propertyName: petType
        mapping:
          dog: Dog
          cat: Cat
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = discriminator.build(root)
    assert isinstance(result, discriminator.Discriminator)

    assert result.property_name is not None

    # Check that key_node and value_node are tracked
    assert result.property_name.key_node is not None
    assert result.property_name.value_node is not None

    # The key_node should contain "propertyName"
    assert result.property_name.key_node.value == "propertyName"

    # The value_node should contain "petType"
    assert result.property_name.value_node.value == "petType"

    # Check line numbers are available (for error reporting)
    assert hasattr(result.property_name.key_node.start_mark, "line")
    assert hasattr(result.property_name.value_node.start_mark, "line")


def test_mapping_with_component_references():
    """Test discriminator mapping with schema component references."""
    yaml_content = textwrap.dedent(
        """
        propertyName: petType
        mapping:
          dog: '#/components/schemas/Dog'
          cat: '#/components/schemas/Cat'
          lizard: '#/components/schemas/Lizard'
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = discriminator.build(root)
    assert isinstance(result, discriminator.Discriminator)

    assert result.mapping is not None

    # Verify mapping structure
    mapping_value = result.mapping.value
    assert isinstance(mapping_value, dict)
    assert len(mapping_value) == 3

    # Extract values from KeySource/ValueSource wrappers
    mapping_dict = {k.value: v.value for k, v in mapping_value.items()}

    # Check specific mappings
    assert mapping_dict["dog"] == "#/components/schemas/Dog"
    assert mapping_dict["cat"] == "#/components/schemas/Cat"
    assert mapping_dict["lizard"] == "#/components/schemas/Lizard"


def test_mapping_with_simple_names():
    """Test discriminator mapping with simple schema names."""
    yaml_content = textwrap.dedent(
        """
        propertyName: objectType
        mapping:
          user: User
          admin: Administrator
          guest: GuestUser
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = discriminator.build(root)
    assert isinstance(result, discriminator.Discriminator)

    assert result.mapping is not None

    # Extract values from KeySource/ValueSource wrappers
    mapping_value = result.mapping.value
    mapping_dict = {k.value: v.value for k, v in mapping_value.items()}

    assert mapping_dict["user"] == "User"
    assert mapping_dict["admin"] == "Administrator"
    assert mapping_dict["guest"] == "GuestUser"


def test_build_with_extensions():
    """Test building Discriminator with specification extensions (new in OpenAPI 3.1)."""
    yaml_content = textwrap.dedent(
        """
        propertyName: petType
        mapping:
          dog: Dog
          cat: Cat
        x-custom: custom value
        x-internal-id: 12345
        x-enabled: true
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = discriminator.build(root)
    assert isinstance(result, discriminator.Discriminator)

    assert result.property_name is not None
    assert result.property_name.value == "petType"

    # Check extensions
    assert result.extensions is not None
    assert len(result.extensions) == 3

    ext_dict = {k.value: v.value for k, v in result.extensions.items()}
    assert ext_dict["x-custom"] == "custom value"
    assert ext_dict["x-internal-id"] == 12345
    assert ext_dict["x-enabled"] is True


def test_build_with_only_extensions():
    """Test building Discriminator with only extensions (no mapping)."""
    yaml_content = textwrap.dedent(
        """
        propertyName: type
        x-custom: value
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = discriminator.build(root)
    assert isinstance(result, discriminator.Discriminator)

    assert result.property_name is not None
    assert result.property_name.value == "type"
    assert result.mapping is None

    assert result.extensions is not None
    assert len(result.extensions) == 1
    ext_dict = {k.value: v.value for k, v in result.extensions.items()}
    assert ext_dict["x-custom"] == "value"


def test_build_with_complex_extension_values():
    """Test building Discriminator with complex extension values."""
    yaml_content = textwrap.dedent(
        """
        propertyName: objectType
        x-config:
          enabled: true
          timeout: 30
        x-tags:
          - production
          - api
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = discriminator.build(root)
    assert isinstance(result, discriminator.Discriminator)

    assert result.extensions is not None
    assert len(result.extensions) == 2

    ext_dict = {k.value: v.value for k, v in result.extensions.items()}
    assert ext_dict["x-config"] == {"enabled": True, "timeout": 30}
    assert ext_dict["x-tags"] == ["production", "api"]


def test_build_without_extensions():
    """Test building Discriminator without extensions returns empty dict."""
    yaml_content = textwrap.dedent(
        """
        propertyName: petType
        mapping:
          dog: Dog
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = discriminator.build(root)
    assert isinstance(result, discriminator.Discriminator)

    # Extensions should be empty dict when not provided
    assert result.extensions == {}


def test_extensions_preserve_source_tracking():
    """Test that extensions preserve source location information."""
    yaml_content = textwrap.dedent(
        """
        propertyName: type
        x-custom: value
        x-other: 123
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = discriminator.build(root)
    assert isinstance(result, discriminator.Discriminator)

    # Check that KeySource and ValueSource have node tracking
    for key_source in result.extensions.keys():
        assert key_source.key_node is not None
        assert key_source.value.startswith("x-")

    for value_source in result.extensions.values():
        assert value_source.value_node is not None
