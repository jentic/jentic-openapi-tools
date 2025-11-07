"""Tests for ServerVariable low-level datamodel."""

import textwrap

from ruamel.yaml import YAML

from jentic.apitools.openapi.datamodels.low.context import Context
from jentic.apitools.openapi.datamodels.low.sources import FieldSource, KeySource, ValueSource
from jentic.apitools.openapi.datamodels.low.v30 import server_variable


def test_build_with_all_fields():
    """Test building ServerVariable with all specification fields."""
    yaml_content = textwrap.dedent(
        """
        default: production
        enum:
          - production
          - staging
          - development
        description: The deployment environment
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = server_variable.build(root)
    assert isinstance(result, server_variable.ServerVariable)

    assert result.root_node == root

    # Check required field
    assert isinstance(result.default, FieldSource)
    assert result.default.value == "production"
    assert result.default.key_node is not None
    assert result.default.value_node is not None

    # Check optional fields
    assert isinstance(result.enum, FieldSource)
    assert len(result.enum.value) == 3
    assert all(isinstance(item, ValueSource) for item in result.enum.value)
    assert [item.value for item in result.enum.value] == ["production", "staging", "development"]
    assert result.enum.key_node is not None
    assert result.enum.value_node is not None

    assert isinstance(result.description, FieldSource)
    assert result.description.value == "The deployment environment"


def test_build_with_default_only():
    """Test building ServerVariable with only required default field."""
    yaml_content = textwrap.dedent(
        """
        default: v1
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = server_variable.build(root)
    assert isinstance(result, server_variable.ServerVariable)

    assert result.root_node == root
    assert isinstance(result.default, FieldSource)
    assert result.default.value == "v1"

    # Optional fields should be None
    assert result.enum is None
    assert result.description is None
    # Extensions returns empty dict when no extensions present
    assert result.extensions == {}


def test_build_with_enum_values():
    """Test building ServerVariable with enum values."""
    yaml_content = textwrap.dedent(
        """
        default: '8443'
        enum:
          - '8443'
          - '443'
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = server_variable.build(root)
    assert isinstance(result, server_variable.ServerVariable)

    assert result.default is not None
    assert result.default.value == "8443"
    assert result.enum is not None
    assert [item.value for item in result.enum.value] == ["8443", "443"]


def test_build_with_extensions():
    """Test building ServerVariable with specification extensions (x-* fields)."""
    yaml_content = textwrap.dedent(
        """
        default: api
        x-custom-property: custom-value
        x-internal: true
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = server_variable.build(root)
    assert isinstance(result, server_variable.ServerVariable)

    assert result.extensions is not None
    assert len(result.extensions) == 2

    # Extensions should be dict[KeySource, ValueSource]
    keys = list(result.extensions.keys())
    assert all(isinstance(k, KeySource) for k in keys)
    assert all(isinstance(v, ValueSource) for v in result.extensions.values())

    # Check extension values
    ext_dict = {k.value: v.value for k, v in result.extensions.items()}
    assert ext_dict["x-custom-property"] == "custom-value"
    assert ext_dict["x-internal"] is True


def test_build_preserves_invalid_types():
    """Test that build preserves values even with 'wrong' types (low-level model principle)."""
    yaml_content = textwrap.dedent(
        """
        default: 12345
        enum: not-a-list
        description: 999
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = server_variable.build(root)
    assert isinstance(result, server_variable.ServerVariable)

    assert result.default is not None
    assert result.enum is not None
    assert result.description is not None

    # Should preserve the actual values, not convert them
    assert result.default.value == 12345
    assert result.enum.value == "not-a-list"
    assert result.description.value == 999


def test_build_with_empty_object():
    """Test building ServerVariable from empty YAML object."""
    yaml_content = "{}"
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = server_variable.build(root)
    assert isinstance(result, server_variable.ServerVariable)

    assert result.root_node == root
    assert result.default is None
    assert result.enum is None
    assert result.description is None
    # Extensions returns empty dict when no extensions present
    assert result.extensions == {}


def test_build_with_invalid_node_returns_value_source():
    """Test that build returns ValueSource for non-mapping nodes (preserves invalid data)."""
    yaml_parser = YAML()

    # Scalar node
    scalar_root = yaml_parser.compose("production")
    result = server_variable.build(scalar_root)
    assert isinstance(result, ValueSource)
    assert result.value == "production"
    assert result.value_node == scalar_root

    # Sequence node
    sequence_root = yaml_parser.compose("['prod', 'staging']")
    result = server_variable.build(sequence_root)
    assert isinstance(result, ValueSource)
    assert result.value == ["prod", "staging"]
    assert result.value_node == sequence_root


def test_build_with_custom_context():
    """Test building ServerVariable with a custom context."""
    yaml_content = textwrap.dedent(
        """
        default: localhost
        description: Local server
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    custom_context = Context()
    result = server_variable.build(root, context=custom_context)
    assert isinstance(result, server_variable.ServerVariable)

    assert result.default is not None
    assert result.description is not None
    assert result.default.value == "localhost"
    assert result.description.value == "Local server"


def test_source_tracking():
    """Test that source location information is preserved."""
    yaml_content = textwrap.dedent(
        """
        default: api
        enum:
          - api
          - www
        description: Subdomain selection
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = server_variable.build(root)
    assert isinstance(result, server_variable.ServerVariable)

    assert result.default is not None
    assert result.enum is not None
    assert result.description is not None

    # Check that key_node and value_node are tracked
    assert result.default.key_node is not None
    assert result.default.value_node is not None
    assert result.enum.key_node is not None
    assert result.enum.value_node is not None

    # The key_nodes should contain the field names
    assert result.default.key_node.value == "default"
    assert result.enum.key_node.value == "enum"
    assert result.description.key_node.value == "description"

    # The value_nodes should contain the actual values
    assert result.default.value_node.value == "api"
    # Check individual enum items and their source tracking
    assert len(result.enum.value) == 2
    assert all(isinstance(item, ValueSource) for item in result.enum.value)
    assert [item.value for item in result.enum.value] == ["api", "www"]
    # Each item should have source tracking
    assert result.enum.value[0].value_node.value == "api"
    assert result.enum.value[1].value_node.value == "www"
    assert result.description.value_node is not None
    assert result.description.value_node.value == "Subdomain selection"

    # Check line numbers are available (for error reporting)
    assert hasattr(result.default.key_node.start_mark, "line")
    assert hasattr(result.default.value_node.start_mark, "line")


def test_mixed_extensions_and_fixed_fields():
    """Test that extensions and fixed fields are properly separated."""
    yaml_content = textwrap.dedent(
        """
        default: prod
        x-custom: value
        enum:
          - prod
          - dev
        x-another: 123
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = server_variable.build(root)
    assert isinstance(result, server_variable.ServerVariable)

    assert result.default is not None
    assert result.enum is not None

    # Fixed fields should be present
    assert result.default.value == "prod"
    assert [item.value for item in result.enum.value] == ["prod", "dev"]

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
        default: v1
        description: |
          # API Version

          Choose the **API version** to use:
          - `v1` - Current stable version
          - `v2` - Beta version with new features

          See [documentation](https://example.com/docs) for details.
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = server_variable.build(root)
    assert isinstance(result, server_variable.ServerVariable)

    assert result.description is not None
    # The low-level model should preserve the exact markdown content
    assert "# API Version" in result.description.value
    assert "**API version**" in result.description.value
    assert "[documentation](https://example.com/docs)" in result.description.value


def test_port_number_variables():
    """Test ServerVariable for port number substitution."""
    yaml_content = textwrap.dedent(
        """
        default: '8443'
        enum:
          - '443'
          - '8443'
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = server_variable.build(root)
    assert isinstance(result, server_variable.ServerVariable)

    assert result.default is not None
    assert result.default.value == "8443"
    assert result.enum is not None
    assert [item.value for item in result.enum.value] == ["443", "8443"]


def test_protocol_variables():
    """Test ServerVariable for protocol substitution."""
    yaml_content = textwrap.dedent(
        """
        default: https
        enum:
          - https
          - http
        description: The transfer protocol
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = server_variable.build(root)
    assert isinstance(result, server_variable.ServerVariable)

    assert result.default is not None
    assert result.default.value == "https"
    assert result.enum is not None
    assert [item.value for item in result.enum.value] == ["https", "http"]


def test_version_variables():
    """Test ServerVariable for API version substitution."""
    yaml_content = textwrap.dedent(
        """
        default: v2
        enum:
          - v1
          - v2
          - v3
        description: API version
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = server_variable.build(root)
    assert isinstance(result, server_variable.ServerVariable)

    assert result.default is not None
    assert result.default.value == "v2"
    assert result.enum is not None
    assert len(result.enum.value) == 3


def test_environment_variables():
    """Test ServerVariable for environment substitution."""
    yaml_content = textwrap.dedent(
        """
        default: production
        enum:
          - development
          - staging
          - production
        description: The deployment environment
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = server_variable.build(root)
    assert isinstance(result, server_variable.ServerVariable)

    assert result.default is not None
    assert result.default.value == "production"
    assert result.enum is not None
    assert [item.value for item in result.enum.value] == ["development", "staging", "production"]


def test_null_values():
    """Test handling of explicit null values."""
    yaml_content = textwrap.dedent(
        """
        default: default-value
        enum: null
        description:
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = server_variable.build(root)
    assert isinstance(result, server_variable.ServerVariable)

    assert result.default is not None
    assert result.default.value == "default-value"

    # Null values should be preserved
    assert result.enum is not None
    assert result.enum.value is None

    assert result.description is not None
    assert result.description.value is None


def test_empty_enum_array():
    """Test that empty enum arrays are preserved (even though spec says they SHOULD NOT be empty)."""
    yaml_content = textwrap.dedent(
        """
        default: value
        enum: []
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = server_variable.build(root)
    assert isinstance(result, server_variable.ServerVariable)

    assert result.default is not None
    assert result.enum is not None
    # Low-level model preserves the empty array
    assert len(result.enum.value) == 0
    assert result.enum.value == []


def test_default_not_in_enum():
    """Test that low-level model preserves default even when not in enum (validation layer's job)."""
    yaml_content = textwrap.dedent(
        """
        default: prod
        enum:
          - production
          - staging
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = server_variable.build(root)
    assert isinstance(result, server_variable.ServerVariable)

    # Low-level model preserves the data as-is
    assert result.default is not None
    assert result.default.value == "prod"
    assert result.enum is not None
    assert "prod" not in [item.value for item in result.enum.value]
