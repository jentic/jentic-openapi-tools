"""Tests for External Documentation low-level datamodel."""

import textwrap

from ruamel.yaml import YAML

from jentic.apitools.openapi.datamodels.low.context import Context
from jentic.apitools.openapi.datamodels.low.sources import FieldSource, KeySource, ValueSource
from jentic.apitools.openapi.datamodels.low.v30 import external_documentation


def test_build_with_all_fields():
    """Test building ExternalDocumentation with all specification fields."""
    yaml_content = textwrap.dedent(
        """
        description: Find more info here
        url: https://example.com/docs
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = external_documentation.build(root)
    assert isinstance(result, external_documentation.ExternalDocumentation)

    assert result.root_node == root

    # Check all fields are FieldSource instances
    assert isinstance(result.description, FieldSource)
    assert result.description.value == "Find more info here"
    assert result.description.key_node is not None
    assert result.description.value_node is not None

    assert isinstance(result.url, FieldSource)
    assert result.url.value == "https://example.com/docs"
    assert result.url.key_node is not None
    assert result.url.value_node is not None


def test_build_with_minimal_fields():
    """Test building ExternalDocumentation with only required field (url)."""
    yaml_content = textwrap.dedent(
        """
        url: https://example.com/docs
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = external_documentation.build(root)
    assert isinstance(result, external_documentation.ExternalDocumentation)

    assert result.root_node == root
    assert isinstance(result.url, FieldSource)
    assert result.url.value == "https://example.com/docs"

    # Description is optional
    assert result.description is None
    # Extensions returns empty dict when no extensions present
    assert result.extensions == {}


def test_build_with_extensions():
    """Test building ExternalDocumentation with specification extensions (x-* fields)."""
    yaml_content = textwrap.dedent(
        """
        url: https://example.com/docs
        description: API Documentation
        x-custom: custom-value
        x-internal: true
        x-priority: 10
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = external_documentation.build(root)
    assert isinstance(result, external_documentation.ExternalDocumentation)

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
    assert ext_dict["x-priority"] == 10


def test_build_preserves_invalid_types():
    """Test that build preserves values even with 'wrong' types (low-level model principle)."""
    yaml_content = textwrap.dedent(
        """
        url: 12345
        description: true
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = external_documentation.build(root)
    assert isinstance(result, external_documentation.ExternalDocumentation)

    assert result.url is not None
    assert result.description is not None

    # Should preserve the actual values, not convert them
    assert result.url.value == 12345
    assert result.description.value is True


def test_build_with_empty_object():
    """Test building ExternalDocumentation from empty YAML object."""
    yaml_content = "{}"
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = external_documentation.build(root)
    assert isinstance(result, external_documentation.ExternalDocumentation)

    assert result.root_node == root
    assert result.url is None
    assert result.description is None
    # Extensions returns empty dict when no extensions present
    assert result.extensions == {}


def test_build_with_invalid_node_returns_value_source():
    """Test that build returns ValueSource for non-mapping nodes (preserves invalid data)."""
    yaml_parser = YAML()

    # Scalar node
    scalar_root = yaml_parser.compose("https://example.com")
    result = external_documentation.build(scalar_root)
    assert isinstance(result, ValueSource)
    assert result.value == "https://example.com"
    assert result.value_node == scalar_root

    # Sequence node
    sequence_root = yaml_parser.compose("['url1', 'url2']")
    result = external_documentation.build(sequence_root)
    assert isinstance(result, ValueSource)
    assert result.value == ["url1", "url2"]
    assert result.value_node == sequence_root


def test_build_with_custom_context():
    """Test building ExternalDocumentation with a custom context."""
    yaml_content = textwrap.dedent(
        """
        url: https://example.com/docs
        description: Documentation
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    custom_context = Context()
    result = external_documentation.build(root, context=custom_context)
    assert isinstance(result, external_documentation.ExternalDocumentation)

    assert result.url is not None
    assert result.description is not None
    assert result.url.value == "https://example.com/docs"
    assert result.description.value == "Documentation"


def test_source_tracking():
    """Test that source location information is preserved."""
    yaml_content = textwrap.dedent(
        """
        url: https://example.com/docs
        description: More information
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = external_documentation.build(root)
    assert isinstance(result, external_documentation.ExternalDocumentation)

    assert result.url is not None

    # Check that key_node and value_node are tracked
    assert result.url.key_node is not None
    assert result.url.value_node is not None

    # The key_node should contain "url"
    assert result.url.key_node.value == "url"

    # The value_node should contain the URL
    assert result.url.value_node.value == "https://example.com/docs"

    # Check line numbers are available (for error reporting)
    assert hasattr(result.url.key_node.start_mark, "line")
    assert hasattr(result.url.value_node.start_mark, "line")


def test_mixed_extensions_and_fixed_fields():
    """Test that extensions and fixed fields are properly separated."""
    yaml_content = textwrap.dedent(
        """
        url: https://example.com/docs
        x-custom: value
        description: API Documentation
        x-another: 123
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = external_documentation.build(root)
    assert isinstance(result, external_documentation.ExternalDocumentation)

    assert result.url is not None
    assert result.description is not None

    # Fixed fields should be present
    assert result.url.value == "https://example.com/docs"
    assert result.description.value == "API Documentation"

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
        url: https://example.com/docs
        description: |
          # API Documentation

          This is a **bold** statement with [a link](https://example.com).

          - Item 1
          - Item 2
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = external_documentation.build(root)
    assert isinstance(result, external_documentation.ExternalDocumentation)

    assert result.description is not None
    # The low-level model should preserve the exact markdown content
    assert "# API Documentation" in result.description.value
    assert "**bold**" in result.description.value
    assert "[a link](https://example.com)" in result.description.value
