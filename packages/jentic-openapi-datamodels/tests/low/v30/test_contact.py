"""Tests for Contact low-level datamodel."""

import textwrap

from ruamel.yaml import YAML

from jentic.apitools.openapi.datamodels.low.context import Context
from jentic.apitools.openapi.datamodels.low.sources import FieldSource, KeySource, ValueSource
from jentic.apitools.openapi.datamodels.low.v30 import contact


def test_build_with_all_fields(parse_yaml):
    """Test building Contact with all specification fields."""
    yaml_content = textwrap.dedent(
        """
        name: API Support Team
        url: https://www.example.com/support
        email: support@example.com
        """
    )
    root = parse_yaml(yaml_content)

    result = contact.build(root)
    assert isinstance(result, contact.Contact)

    assert result.root_node == root

    # Check all fields are FieldSource instances
    assert isinstance(result.name, FieldSource)
    assert result.name.value == "API Support Team"
    assert result.name.key_node is not None
    assert result.name.value_node is not None

    assert isinstance(result.url, FieldSource)
    assert result.url.value == "https://www.example.com/support"
    assert result.url.key_node is not None
    assert result.url.value_node is not None

    assert isinstance(result.email, FieldSource)
    assert result.email.value == "support@example.com"
    assert result.email.key_node is not None
    assert result.email.value_node is not None


def test_build_with_name_only(parse_yaml):
    """Test building Contact with only name field."""
    yaml_content = textwrap.dedent(
        """
        name: John Doe
        """
    )
    root = parse_yaml(yaml_content)

    result = contact.build(root)
    assert isinstance(result, contact.Contact)

    assert result.root_node == root
    assert isinstance(result.name, FieldSource)
    assert result.name.value == "John Doe"

    # Other fields are optional
    assert result.url is None
    assert result.email is None
    # Extensions returns empty dict when no extensions present
    assert result.extensions == {}


def test_build_with_url_only(parse_yaml):
    """Test building Contact with only url field."""
    yaml_content = textwrap.dedent(
        """
        url: https://example.com/contact
        """
    )
    root = parse_yaml(yaml_content)

    result = contact.build(root)
    assert isinstance(result, contact.Contact)

    assert isinstance(result.url, FieldSource)
    assert result.url.value == "https://example.com/contact"

    assert result.name is None
    assert result.email is None


def test_build_with_email_only(parse_yaml):
    """Test building Contact with only email field."""
    yaml_content = textwrap.dedent(
        """
        email: contact@example.com
        """
    )
    root = parse_yaml(yaml_content)

    result = contact.build(root)
    assert isinstance(result, contact.Contact)

    assert isinstance(result.email, FieldSource)
    assert result.email.value == "contact@example.com"

    assert result.name is None
    assert result.url is None


def test_build_with_extensions(parse_yaml):
    """Test building Contact with specification extensions (x-* fields)."""
    yaml_content = textwrap.dedent(
        """
        name: Support Team
        email: support@example.com
        x-phone: +1-555-0100
        x-timezone: America/New_York
        x-available: true
        """
    )
    root = parse_yaml(yaml_content)

    result = contact.build(root)
    assert isinstance(result, contact.Contact)

    assert result.extensions is not None
    assert len(result.extensions) == 3

    # Extensions should be dict[KeySource, ValueSource]
    keys = list(result.extensions.keys())
    assert all(isinstance(k, KeySource) for k in keys)
    assert all(isinstance(v, ValueSource) for v in result.extensions.values())

    # Check extension values
    ext_dict = {k.value: v.value for k, v in result.extensions.items()}
    assert ext_dict["x-phone"] == "+1-555-0100"
    assert ext_dict["x-timezone"] == "America/New_York"
    assert ext_dict["x-available"] is True


def test_build_preserves_invalid_types(parse_yaml):
    """Test that build preserves values even with 'wrong' types (low-level model principle)."""
    yaml_content = textwrap.dedent(
        """
        name: 12345
        url: true
        email: ['not', 'an', 'email']
        """
    )
    root = parse_yaml(yaml_content)

    result = contact.build(root)
    assert isinstance(result, contact.Contact)

    assert result.name is not None
    assert result.url is not None
    assert result.email is not None

    # Should preserve the actual values, not convert them
    assert result.name.value == 12345
    assert result.url.value is True
    assert result.email.value == ["not", "an", "email"]


def test_build_with_empty_object(parse_yaml):
    """Test building Contact from empty YAML object."""
    yaml_content = "{}"
    root = parse_yaml(yaml_content)

    result = contact.build(root)
    assert isinstance(result, contact.Contact)

    assert result.root_node == root
    assert result.name is None
    assert result.url is None
    assert result.email is None
    # Extensions returns empty dict when no extensions present
    assert result.extensions == {}


def test_build_with_invalid_node_returns_value_source():
    """Test that build returns ValueSource for non-mapping nodes (preserves invalid data)."""
    yaml_parser = YAML()

    # Scalar node
    scalar_root = yaml_parser.compose("contact@example.com")
    result = contact.build(scalar_root)
    assert isinstance(result, ValueSource)
    assert result.value == "contact@example.com"
    assert result.value_node == scalar_root

    # Sequence node
    sequence_root = yaml_parser.compose("['name', 'email']")
    result = contact.build(sequence_root)
    assert isinstance(result, ValueSource)
    assert result.value == ["name", "email"]
    assert result.value_node == sequence_root


def test_build_with_custom_context(parse_yaml):
    """Test building Contact with a custom context."""
    yaml_content = textwrap.dedent(
        """
        name: API Team
        email: api@example.com
        """
    )
    root = parse_yaml(yaml_content)

    custom_context = Context()
    result = contact.build(root, context=custom_context)
    assert isinstance(result, contact.Contact)

    assert result.name is not None
    assert result.email is not None
    assert result.name.value == "API Team"
    assert result.email.value == "api@example.com"


def test_source_tracking(parse_yaml):
    """Test that source location information is preserved."""
    yaml_content = textwrap.dedent(
        """
        name: Support
        url: https://example.com
        email: support@example.com
        """
    )
    root = parse_yaml(yaml_content)

    result = contact.build(root)
    assert isinstance(result, contact.Contact)

    assert result.name is not None
    assert result.url is not None
    assert result.email is not None

    # Check that key_node and value_node are tracked
    assert result.name.key_node is not None
    assert result.name.value_node is not None
    assert result.url.key_node is not None
    assert result.url.value_node is not None
    assert result.email.key_node is not None
    assert result.email.value_node is not None

    # The key_nodes should contain the field names
    assert result.name.key_node.value == "name"
    assert result.url.key_node.value == "url"
    assert result.email.key_node.value == "email"

    # The value_nodes should contain the actual values
    assert result.name.value_node.value == "Support"
    assert result.url.value_node.value == "https://example.com"
    assert result.email.value_node.value == "support@example.com"

    # Check line numbers are available (for error reporting)
    assert hasattr(result.name.key_node.start_mark, "line")
    assert hasattr(result.name.value_node.start_mark, "line")


def test_mixed_extensions_and_fixed_fields(parse_yaml):
    """Test that extensions and fixed fields are properly separated."""
    yaml_content = textwrap.dedent(
        """
        name: John Doe
        x-department: Engineering
        url: https://example.com/john
        x-employee-id: 12345
        email: john@example.com
        """
    )
    root = parse_yaml(yaml_content)

    result = contact.build(root)
    assert isinstance(result, contact.Contact)

    assert result.name is not None
    assert result.url is not None
    assert result.email is not None

    # Fixed fields should be present
    assert result.name.value == "John Doe"
    assert result.url.value == "https://example.com/john"
    assert result.email.value == "john@example.com"

    # Extensions should be in extensions dict
    assert result.extensions is not None
    assert len(result.extensions) == 2

    ext_dict = {k.value: v.value for k, v in result.extensions.items()}
    assert ext_dict["x-department"] == "Engineering"
    assert ext_dict["x-employee-id"] == 12345


def test_international_email_addresses(parse_yaml):
    """Test that Contact can handle international email addresses."""
    yaml_content = textwrap.dedent(
        """
        name: München Support
        email: info@münchen.de
        """
    )
    root = parse_yaml(yaml_content)

    result = contact.build(root)
    assert isinstance(result, contact.Contact)

    assert result.name is not None
    assert result.name.value == "München Support"
    assert result.email is not None
    assert result.email.value == "info@münchen.de"


def test_various_url_formats(parse_yaml):
    """Test that Contact preserves various URL formats."""
    test_cases = [
        "https://example.com/contact",
        "http://example.com",
        "https://example.com:8080/path",
        "https://user:pass@example.com",
        "https://example.com/path?query=value",
        "https://example.com/path#fragment",
    ]

    for url in test_cases:
        yaml_content = f"url: {url}"
        root = parse_yaml(yaml_content)
        result = contact.build(root)

        assert isinstance(result, contact.Contact)
        assert result.url is not None
        assert result.url.value == url


def test_null_values(parse_yaml):
    """Test handling of explicit null values."""
    yaml_content = textwrap.dedent(
        """
        name: John Doe
        url: null
        email:
        """
    )
    root = parse_yaml(yaml_content)

    result = contact.build(root)
    assert isinstance(result, contact.Contact)

    assert result.name is not None
    assert result.name.value == "John Doe"

    # Null values should be preserved
    assert result.url is not None
    assert result.url.value is None

    assert result.email is not None
    assert result.email.value is None


def test_multiline_name(parse_yaml):
    """Test that Contact can handle multiline names (though unusual)."""
    yaml_content = textwrap.dedent(
        """
        name: |
          API Support Team
          Engineering Division
        email: support@example.com
        """
    )
    root = parse_yaml(yaml_content)

    result = contact.build(root)
    assert isinstance(result, contact.Contact)

    # Low-level model should preserve the multiline string exactly
    assert result.name is not None
    assert "API Support Team" in result.name.value
    assert "Engineering Division" in result.name.value
