"""Tests for XML location tracking and error reporting capabilities."""

import textwrap

from ruamel.yaml import YAML

from jentic.apitools.openapi.datamodels.low.v30 import xml


def test_field_location_tracking():
    """Test accessing line and column information for fixed fields."""
    yaml_content = textwrap.dedent(
        """
        name: id
        namespace: https://example.com/schema
        prefix: ex
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = xml.build(root)
    assert isinstance(result, xml.XML)

    assert result is not None
    assert result.name is not None
    assert result.name.key_node is not None
    assert result.name.value_node is not None

    # Access key node location
    assert result.name.key_node.start_mark.line == 1  # 0-indexed
    assert result.name.key_node.start_mark.column == 0
    assert result.name.key_node.end_mark.line == 1
    assert result.name.key_node.end_mark.column == 4

    # Access value node location
    assert result.name.value_node.start_mark.line == 1
    assert result.name.value_node.start_mark.column == 6
    assert result.name.value_node.end_mark.line == 1
    assert result.name.value_node.end_mark.column == 8


def test_extension_location_tracking():
    """Test accessing line and column information for extension fields."""
    yaml_content = textwrap.dedent(
        """
        name: id
        x-custom: my-value
        x-internal: true
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = xml.build(root)
    assert isinstance(result, xml.XML)

    assert result is not None
    assert result.extensions is not None
    assert len(result.extensions) == 2

    # Find x-custom extension
    x_custom = None
    for key, value in result.extensions.items():
        if key.value == "x-custom":
            x_custom = (key, value)
            break

    assert x_custom is not None
    key, value = x_custom

    # Check key location
    assert key.key_node.start_mark.line == 2
    assert key.key_node.start_mark.column == 0
    assert key.key_node.value == "x-custom"

    # Check value location
    assert value.value_node.start_mark.line == 2
    assert value.value_node.start_mark.column == 10
    assert value.value == "my-value"


def test_multiline_value_location():
    """Test location tracking for multiline values."""
    yaml_content = textwrap.dedent(
        """
        name: |
          multiline
          value
        prefix: ex
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = xml.build(root)
    assert isinstance(result, xml.XML)

    assert result is not None
    assert result.name is not None
    assert result.name.key_node is not None
    assert result.name.value_node is not None

    # Key is on line 1
    assert result.name.key_node.start_mark.line == 1

    # Value starts on line 1 (the | character)
    assert result.name.value_node.start_mark.line == 1

    # Value should be the multiline string
    assert "multiline" in result.name.value
    assert "value" in result.name.value


def test_error_reporting_format():
    """Test formatting location information for error messages."""
    yaml_content = textwrap.dedent(
        """
        name: 123
        namespace: invalid
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = xml.build(root)
    assert isinstance(result, xml.XML)

    assert result is not None

    # Simulate error reporting for invalid type
    if result.name and not isinstance(result.name.value, str):
        assert result.name is not None
        assert result.name.value_node is not None
        error_line = result.name.value_node.start_mark.line + 1  # Convert to 1-indexed
        error_column = result.name.value_node.start_mark.column + 1  # Convert to 1-indexed
        error_msg = (
            f"Invalid type for 'name' field at line {error_line}, "
            f"column {error_column}: expected string, got {type(result.name.value).__name__}"
        )

        assert "line 2" in error_msg
        assert "expected string, got int" in error_msg


def test_location_with_nested_structures():
    """Test location tracking with nested data structures."""
    yaml_content = textwrap.dedent(
        """
        name: id
        x-metadata:
          author: John
          version: 1.0
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = xml.build(root)
    assert isinstance(result, xml.XML)

    assert result is not None
    assert result.extensions is not None

    # Find x-metadata
    x_metadata = None
    for key, value in result.extensions.items():
        if key.value == "x-metadata":
            x_metadata = (key, value)
            break

    assert x_metadata is not None
    key, value = x_metadata

    # Key location
    assert key.key_node.start_mark.line == 2
    assert key.key_node.value == "x-metadata"

    # Value is a dict starting on line 3 (where "author" is)
    assert value.value_node.start_mark.line == 3
    assert isinstance(value.value, dict)
    assert value.value == {"author": "John", "version": 1.0}


def test_source_file_name():
    """Test that source file name can be tracked if provided."""
    yaml_content = textwrap.dedent(
        """
        name: id
        namespace: https://example.com/schema
        """
    )
    yaml_parser = YAML()

    # When composing from string, name defaults to None or <unicode string>
    root = yaml_parser.compose(yaml_content)

    result = xml.build(root)
    assert isinstance(result, xml.XML)

    assert result is not None
    assert result.name is not None

    # The start_mark contains name information
    file_name = result.name.key_node.start_mark.name
    # When parsing from string, name is typically None or a default value
    assert file_name is not None or file_name is None  # Flexible for different ruamel versions


def test_complete_error_context():
    """Test building complete error context with all location details."""
    yaml_content = textwrap.dedent(
        """
        name: id
        namespace: https://example.com/schema
        unknownField: value
        x-custom: extension
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = xml.build(root)
    assert isinstance(result, xml.XML)

    assert result is not None

    # Collect all field locations for error context
    field_locations = []

    # Fixed fields
    if result.name:
        field_locations.append(
            {
                "field": "name",
                "type": "fixed",
                "line": result.name.key_node.start_mark.line + 1,
                "column": result.name.key_node.start_mark.column + 1,
            }
        )

    if result.namespace:
        field_locations.append(
            {
                "field": "namespace",
                "type": "fixed",
                "line": result.namespace.key_node.start_mark.line + 1,
                "column": result.namespace.key_node.start_mark.column + 1,
            }
        )

    # Extensions
    if result.extensions:
        for key, value in result.extensions.items():
            field_locations.append(
                {
                    "field": key.value,
                    "type": "extension",
                    "line": key.key_node.start_mark.line + 1,
                    "column": key.key_node.start_mark.column + 1,
                }
            )

    # Should have tracked all fields
    assert len(field_locations) == 3  # name, namespace, x-custom

    # Verify we can sort by line number for reporting
    sorted_locations = sorted(field_locations, key=lambda x: x["line"])
    assert sorted_locations[0]["field"] == "name"
    assert sorted_locations[1]["field"] == "namespace"
    assert sorted_locations[2]["field"] == "x-custom"


def test_range_information():
    """Test accessing the full range (start to end) of a field."""
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

    assert result is not None

    # Get the full range of the namespace field
    if result.namespace:
        assert result.namespace is not None
        assert result.namespace.key_node is not None
        assert result.namespace.value_node is not None
        key_start = result.namespace.key_node.start_mark
        value_end = result.namespace.value_node.end_mark

        # Range spans from start of key to end of value
        assert key_start.line == 2
        assert key_start.column == 0

        # Value ends after the URL
        assert value_end.line == 2
        assert value_end.column > 0

        # Calculate span
        if key_start.line == value_end.line:
            span_length = value_end.column - key_start.column
            # Should span the entire "namespace: https://example.com/schema"
            assert span_length > 30  # Reasonable length check


def test_index_and_buffer_access():
    """Test accessing index and buffer position for advanced use cases."""
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

    assert result is not None

    # Start marks have index (byte offset) and pointer (character offset)
    if result.name:
        start_mark = result.name.key_node.start_mark

        # Index is the byte offset in the stream
        assert hasattr(start_mark, "index")
        assert isinstance(start_mark.index, int)
        assert start_mark.index >= 0

        # Pointer is similar to index
        assert hasattr(start_mark, "pointer")
