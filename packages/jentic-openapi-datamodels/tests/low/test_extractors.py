"""Tests for extractor functions."""

import textwrap

from ruamel.yaml import YAML

from jentic.apitools.openapi.datamodels.low.extractors import (
    extract_extension_fields,
    extract_unknown_fields,
)
from jentic.apitools.openapi.datamodels.low.sources import KeySource, ValueSource
from jentic.apitools.openapi.datamodels.low.v30.xml import XML


def test_extract_extension_fields(parse_yaml):
    """Test extracting extension fields (x-* fields) from YAML."""
    yaml_content = textwrap.dedent(
        """
        name: id
        x-custom: value
        namespace: https://example.com/schema
        x-internal: true
        x-list:
          - item1
          - item2
        """
    )
    root = parse_yaml(yaml_content)

    extensions = extract_extension_fields(root)

    assert extensions is not None
    assert len(extensions) == 3

    # Check types
    assert all(isinstance(k, KeySource) for k in extensions.keys())
    assert all(isinstance(v, ValueSource) for v in extensions.values())

    # Check values
    ext_dict = {k.value: v.value for k, v in extensions.items()}
    assert ext_dict["x-custom"] == "value"
    assert ext_dict["x-internal"] is True
    assert ext_dict["x-list"] == ["item1", "item2"]


def test_extract_extension_fields_with_none(parse_yaml):
    """Test that non-extension fields are not extracted."""
    yaml_content = textwrap.dedent(
        """
        name: id
        namespace: https://example.com/schema
        prefix: ex
        """
    )
    root = parse_yaml(yaml_content)

    extensions = extract_extension_fields(root)

    # Should return empty dict when no extensions
    assert extensions == {}


def test_extract_extension_fields_invalid_node():
    """Test that extract_extension_fields returns empty dict for non-mapping nodes."""
    yaml_parser = YAML()

    # Scalar node
    scalar_root = yaml_parser.compose("just-a-string")
    assert extract_extension_fields(scalar_root) == {}

    # Sequence node
    sequence_root = yaml_parser.compose("['item1', 'item2']")
    assert extract_extension_fields(sequence_root) == {}


def test_extract_unknown_fields(parse_yaml):
    """Test extracting unknown fields (not spec fields, not extensions)."""
    yaml_content = textwrap.dedent(
        """
        name: id
        namespace: https://example.com/schema
        typo: this-is-a-typo
        unknownField: value
        x-custom: extension
        """
    )
    root = parse_yaml(yaml_content)

    unknown = extract_unknown_fields(root, XML)

    assert unknown is not None
    assert len(unknown) == 2

    # Check types
    assert all(isinstance(k, KeySource) for k in unknown.keys())
    assert all(isinstance(v, ValueSource) for v in unknown.values())

    # Check values
    unknown_dict = {k.value: v.value for k, v in unknown.items()}
    assert unknown_dict["typo"] == "this-is-a-typo"
    assert unknown_dict["unknownField"] == "value"

    # Extension should not be in unknown fields
    assert "x-custom" not in unknown_dict

    # Valid fields should not be in unknown fields
    assert "name" not in unknown_dict
    assert "namespace" not in unknown_dict


def test_extract_unknown_fields_with_none(parse_yaml):
    """Test that only valid fields and extensions are present."""
    yaml_content = textwrap.dedent(
        """
        name: id
        namespace: https://example.com/schema
        x-custom: extension
        """
    )
    root = parse_yaml(yaml_content)

    unknown = extract_unknown_fields(root, XML)

    # Should return empty dict when no unknown fields
    assert unknown == {}


def test_extract_unknown_fields_invalid_node():
    """Test that extract_unknown_fields returns empty dict for non-mapping nodes."""
    yaml_parser = YAML()

    # Scalar node
    scalar_root = yaml_parser.compose("just-a-string")
    assert extract_unknown_fields(scalar_root, XML) == {}

    # Sequence node
    sequence_root = yaml_parser.compose("['item1', 'item2']")
    assert extract_unknown_fields(sequence_root, XML) == {}


def test_extract_unknown_fields_source_tracking(parse_yaml):
    """Test that unknown fields preserve source location information."""
    yaml_content = textwrap.dedent(
        """
        name: id
        unknownField: value
        """
    )
    root = parse_yaml(yaml_content)

    unknown = extract_unknown_fields(root, XML)

    assert unknown is not None
    assert len(unknown) == 1

    key, value = next(iter(unknown.items()))

    # Check that source nodes are tracked
    assert key.key_node is not None
    assert key.key_node.value == "unknownField"

    assert value.value_node is not None
    assert value.value_node.value == "value"

    # Check line numbers are available
    assert hasattr(key.key_node.start_mark, "line")
    assert hasattr(value.value_node.start_mark, "line")


def test_extract_extension_fields_source_tracking(parse_yaml):
    """Test that extension fields preserve source location information."""
    yaml_content = textwrap.dedent(
        """
        name: id
        x-custom: value
        """
    )
    root = parse_yaml(yaml_content)

    extensions = extract_extension_fields(root)

    assert extensions is not None
    assert len(extensions) == 1

    key, value = next(iter(extensions.items()))

    # Check that source nodes are tracked
    assert key.key_node is not None
    assert key.key_node.value == "x-custom"

    assert value.value_node is not None
    assert value.value_node.value == "value"

    # Check line numbers are available
    assert hasattr(key.key_node.start_mark, "line")
    assert hasattr(value.value_node.start_mark, "line")


def test_extract_unknown_fields_with_various_types(parse_yaml):
    """Test that unknown fields preserve all value types."""
    yaml_content = textwrap.dedent(
        """
        name: id
        stringField: text
        numberField: 123
        boolField: true
        arrayField: [1, 2, 3]
        objectField: {key: value}
        """
    )
    root = parse_yaml(yaml_content)

    unknown = extract_unknown_fields(root, XML)

    assert unknown is not None
    assert len(unknown) == 5

    unknown_dict = {k.value: v.value for k, v in unknown.items()}
    assert unknown_dict["stringField"] == "text"
    assert unknown_dict["numberField"] == 123
    assert unknown_dict["boolField"] is True
    assert unknown_dict["arrayField"] == [1, 2, 3]
    assert unknown_dict["objectField"] == {"key": "value"}
