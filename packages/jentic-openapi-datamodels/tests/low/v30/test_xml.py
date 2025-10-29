"""Tests for XML low-level datamodel."""

import textwrap

from ruamel.yaml import YAML

from jentic.apitools.openapi.datamodels.low.context import Context
from jentic.apitools.openapi.datamodels.low.sources import FieldSource, KeySource, ValueSource
from jentic.apitools.openapi.datamodels.low.v30 import xml


def test_build_with_all_fields():
    """Test building XML with all specification fields."""
    yaml_content = textwrap.dedent(
        """
        name: id
        namespace: https://example.com/schema
        prefix: ex
        attribute: true
        wrapped: false
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = xml.build(root)
    assert isinstance(result, xml.XML)

    assert result.root_node == root

    # Check all fields are FieldSource instances
    assert isinstance(result.name, FieldSource)
    assert result.name.value == "id"
    assert result.name.key_node is not None
    assert result.name.value_node is not None

    assert isinstance(result.namespace, FieldSource)
    assert result.namespace.value == "https://example.com/schema"

    assert isinstance(result.prefix, FieldSource)
    assert result.prefix.value == "ex"

    assert isinstance(result.attribute, FieldSource)
    assert result.attribute.value is True

    assert isinstance(result.wrapped, FieldSource)
    assert result.wrapped.value is False


def test_build_with_minimal_fields():
    """Test building XML with only required fields."""
    yaml_content = textwrap.dedent(
        """
        name: id
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = xml.build(root)
    assert isinstance(result, xml.XML)

    assert result.root_node == root
    assert isinstance(result.name, FieldSource)
    assert result.name.value == "id"

    # Other fields should be None
    assert result.namespace is None
    assert result.prefix is None
    assert result.attribute is None
    assert result.wrapped is None
    # Extensions returns empty dict when no extensions present
    assert result.extensions == {}


def test_build_with_extensions():
    """Test building XML with specification extensions (x-* fields)."""
    yaml_content = textwrap.dedent(
        """
        name: id
        x-custom: custom-value
        x-internal: true
        x-array:
          - item1
          - item2
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = xml.build(root)
    assert isinstance(result, xml.XML)

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
    assert ext_dict["x-array"] == ["item1", "item2"]


def test_build_preserves_invalid_types():
    """Test that build preserves values even with 'wrong' types (low-level model principle)."""
    yaml_content = textwrap.dedent(
        """
        name: 123
        namespace: true
        attribute: not-a-boolean
        wrapped: 42
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = xml.build(root)
    assert isinstance(result, xml.XML)

    assert result.name is not None
    assert result.namespace is not None
    assert result.attribute is not None
    assert result.wrapped is not None

    # Should preserve the actual values, not convert them
    assert result.name.value == 123
    assert result.namespace.value is True
    assert result.attribute.value == "not-a-boolean"
    assert result.wrapped.value == 42


def test_build_with_empty_object():
    """Test building XML from empty YAML object."""
    yaml_content = "{}"
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = xml.build(root)
    assert isinstance(result, xml.XML)

    assert result.root_node == root
    assert result.name is None
    assert result.namespace is None
    assert result.prefix is None
    assert result.attribute is None
    assert result.wrapped is None
    # Extensions returns empty dict when no extensions present
    assert result.extensions == {}


def test_build_with_invalid_node_returns_none():
    """Test that build returns ValueSource for non-mapping nodes (preserves invalid data)."""
    yaml_parser = YAML()

    # Scalar node
    scalar_root = yaml_parser.compose("just-a-string")
    result = xml.build(scalar_root)
    assert isinstance(result, ValueSource)
    assert result.value == "just-a-string"
    assert result.value_node == scalar_root

    # Sequence node
    sequence_root = yaml_parser.compose("['item1', 'item2']")
    result = xml.build(sequence_root)
    assert isinstance(result, ValueSource)
    assert result.value == ["item1", "item2"]
    assert result.value_node == sequence_root


def test_build_with_custom_context():
    """Test building XML with a custom context."""
    yaml_content = textwrap.dedent(
        """
        name: id
        namespace: https://example.com/schema
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    custom_context = Context()
    result = xml.build(root, context=custom_context)
    assert isinstance(result, xml.XML)

    assert result.name is not None
    assert result.namespace is not None
    assert result.name.value == "id"
    assert result.namespace.value == "https://example.com/schema"


def test_source_tracking():
    """Test that source location information is preserved."""
    yaml_content = textwrap.dedent(
        """
        name: id
        namespace: https://example.com/schema
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = xml.build(root)
    assert isinstance(result, xml.XML)

    assert result.name is not None

    # Check that key_node and value_node are tracked
    assert result.name.key_node is not None
    assert result.name.value_node is not None

    # The key_node should contain "name"
    assert result.name.key_node.value == "name"

    # The value_node should contain "id"
    assert result.name.value_node.value == "id"

    # Check line numbers are available (for error reporting)
    assert hasattr(result.name.key_node.start_mark, "line")
    assert hasattr(result.name.value_node.start_mark, "line")


def test_mixed_extensions_and_fixed_fields():
    """Test that extensions and fixed fields are properly separated."""
    yaml_content = textwrap.dedent(
        """
        name: id
        x-custom: value
        namespace: https://example.com/schema
        x-another: 123
        prefix: ex
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = xml.build(root)
    assert isinstance(result, xml.XML)

    assert result.name is not None
    assert result.namespace is not None
    assert result.prefix is not None

    # Fixed fields should be present
    assert result.name.value == "id"
    assert result.namespace.value == "https://example.com/schema"
    assert result.prefix.value == "ex"

    # Extensions should be in extensions dict
    assert result.extensions is not None
    assert len(result.extensions) == 2

    ext_dict = {k.value: v.value for k, v in result.extensions.items()}
    assert ext_dict["x-custom"] == "value"
    assert ext_dict["x-another"] == 123
