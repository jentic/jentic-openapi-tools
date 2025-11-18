"""Tests for Info low-level datamodel."""

import textwrap

from ruamel.yaml import YAML

from jentic.apitools.openapi.datamodels.low.context import Context
from jentic.apitools.openapi.datamodels.low.sources import FieldSource, KeySource, ValueSource
from jentic.apitools.openapi.datamodels.low.v31 import info
from jentic.apitools.openapi.datamodels.low.v31.contact import Contact
from jentic.apitools.openapi.datamodels.low.v31.license import License


def test_build_with_all_fields(parse_yaml):
    """Test building Info with all specification fields."""
    yaml_content = textwrap.dedent(
        """
        title: Sample Pet Store App
        description: This is a sample server for a pet store.
        termsOfService: https://example.com/terms/
        contact:
          name: API Support
          url: https://www.example.com/support
          email: support@example.com
        license:
          name: Apache 2.0
          url: https://www.apache.org/licenses/LICENSE-2.0.html
        version: 1.0.1
        """
    )
    root = parse_yaml(yaml_content)

    result = info.build(root)
    assert isinstance(result, info.Info)

    assert result.root_node == root

    # Check required fields
    assert isinstance(result.title, FieldSource)
    assert result.title.value == "Sample Pet Store App"
    assert result.title.key_node is not None
    assert result.title.value_node is not None

    assert isinstance(result.version, FieldSource)
    assert result.version.value == "1.0.1"
    assert result.version.key_node is not None
    assert result.version.value_node is not None

    # Check optional fields
    assert isinstance(result.description, FieldSource)
    assert result.description.value == "This is a sample server for a pet store."

    assert isinstance(result.termsOfService, FieldSource)
    assert result.termsOfService.value == "https://example.com/terms/"

    # Check nested Contact object
    assert isinstance(result.contact, FieldSource)
    assert isinstance(result.contact.value, Contact)
    assert result.contact.value.name is not None
    assert result.contact.value.name.value == "API Support"
    assert result.contact.value.email is not None
    assert result.contact.value.email.value == "support@example.com"

    # Check nested License object
    assert isinstance(result.license, FieldSource)
    assert isinstance(result.license.value, License)
    assert result.license.value.name is not None
    assert result.license.value.name.value == "Apache 2.0"
    assert result.license.value.url is not None
    assert result.license.value.url.value == "https://www.apache.org/licenses/LICENSE-2.0.html"


def test_build_with_required_fields_only(parse_yaml):
    """Test building Info with only required fields (title and version)."""
    yaml_content = textwrap.dedent(
        """
        title: My API
        version: 1.0.0
        """
    )
    root = parse_yaml(yaml_content)

    result = info.build(root)
    assert isinstance(result, info.Info)

    assert result.root_node == root
    assert isinstance(result.title, FieldSource)
    assert result.title.value == "My API"
    assert isinstance(result.version, FieldSource)
    assert result.version.value == "1.0.0"

    # Optional fields should be None
    assert result.description is None
    assert result.termsOfService is None
    assert result.contact is None
    assert result.license is None
    # Extensions returns empty dict when no extensions present
    assert result.extensions == {}


def test_build_with_contact_only(parse_yaml):
    """Test building Info with contact information."""
    yaml_content = textwrap.dedent(
        """
        title: API with Contact
        version: 2.0.0
        contact:
          name: Support Team
          email: team@example.com
        """
    )
    root = parse_yaml(yaml_content)

    result = info.build(root)
    assert isinstance(result, info.Info)

    assert result.contact is not None
    assert isinstance(result.contact.value, Contact)
    assert result.contact.value.name is not None
    assert result.contact.value.name.value == "Support Team"


def test_build_with_license_only(parse_yaml):
    """Test building Info with license information."""
    yaml_content = textwrap.dedent(
        """
        title: API with License
        version: 3.0.0
        license:
          name: MIT
        """
    )
    root = parse_yaml(yaml_content)

    result = info.build(root)
    assert isinstance(result, info.Info)

    assert result.license is not None
    assert isinstance(result.license.value, License)
    assert result.license.value.name is not None
    assert result.license.value.name.value == "MIT"


def test_build_with_extensions(parse_yaml):
    """Test building Info with specification extensions (x-* fields)."""
    yaml_content = textwrap.dedent(
        """
        title: Extended API
        version: 1.0.0
        x-api-id: 12345
        x-audience: public
        x-logo:
          url: https://example.com/logo.png
        """
    )
    root = parse_yaml(yaml_content)

    result = info.build(root)
    assert isinstance(result, info.Info)

    assert result.extensions is not None
    assert len(result.extensions) == 3

    # Extensions should be dict[KeySource, ValueSource]
    keys = list(result.extensions.keys())
    assert all(isinstance(k, KeySource) for k in keys)
    assert all(isinstance(v, ValueSource) for v in result.extensions.values())

    # Check extension values
    ext_dict = {k.value: v.value for k, v in result.extensions.items()}
    assert ext_dict["x-api-id"] == 12345
    assert ext_dict["x-audience"] == "public"
    # x-logo is a dict, need to type assert for pyright
    x_logo = ext_dict["x-logo"]
    assert isinstance(x_logo, dict)
    assert x_logo["url"] == "https://example.com/logo.png"


def test_build_preserves_invalid_types(parse_yaml):
    """Test that build preserves values even with 'wrong' types (low-level model principle)."""
    yaml_content = textwrap.dedent(
        """
        title: 12345
        version: true
        description: 999
        contact: not-a-contact
        license: ['invalid', 'license']
        """
    )
    root = parse_yaml(yaml_content)

    result = info.build(root)
    assert isinstance(result, info.Info)

    assert result.title is not None
    assert result.version is not None
    assert result.description is not None
    assert result.contact is not None
    assert result.license is not None

    # Should preserve the actual values, not convert them
    assert result.title.value == 12345
    assert result.version.value is True
    assert result.description.value == 999
    assert result.contact.value == "not-a-contact"
    assert result.license.value == ["invalid", "license"]


def test_build_with_empty_object(parse_yaml):
    """Test building Info from empty YAML object."""
    yaml_content = "{}"
    root = parse_yaml(yaml_content)

    result = info.build(root)
    assert isinstance(result, info.Info)

    assert result.root_node == root
    assert result.title is None
    assert result.version is None
    assert result.description is None
    assert result.termsOfService is None
    assert result.contact is None
    assert result.license is None
    # Extensions returns empty dict when no extensions present
    assert result.extensions == {}


def test_build_with_invalid_node_returns_value_source():
    """Test that build returns ValueSource for non-mapping nodes (preserves invalid data)."""
    yaml_parser = YAML()

    # Scalar node
    scalar_root = yaml_parser.compose("API Info String")
    result = info.build(scalar_root)
    assert isinstance(result, ValueSource)
    assert result.value == "API Info String"
    assert result.value_node == scalar_root

    # Sequence node
    sequence_root = yaml_parser.compose("['title', 'version']")
    result = info.build(sequence_root)
    assert isinstance(result, ValueSource)
    assert result.value == ["title", "version"]
    assert result.value_node == sequence_root


def test_build_with_custom_context(parse_yaml):
    """Test building Info with a custom context."""
    yaml_content = textwrap.dedent(
        """
        title: Custom Context API
        version: 2.5.0
        """
    )
    root = parse_yaml(yaml_content)

    custom_context = Context()
    result = info.build(root, context=custom_context)
    assert isinstance(result, info.Info)

    assert result.title is not None
    assert result.version is not None
    assert result.title.value == "Custom Context API"
    assert result.version.value == "2.5.0"


def test_source_tracking(parse_yaml):
    """Test that source location information is preserved."""
    yaml_content = textwrap.dedent(
        """
        title: Tracked API
        version: 1.0.0
        description: API with tracked sources
        """
    )
    root = parse_yaml(yaml_content)

    result = info.build(root)
    assert isinstance(result, info.Info)

    assert result.title is not None
    assert result.version is not None
    assert result.description is not None

    # Check that key_node and value_node are tracked
    assert result.title.key_node is not None
    assert result.title.value_node is not None
    assert result.version.key_node is not None
    assert result.version.value_node is not None

    # The key_nodes should contain the field names
    assert result.title.key_node.value == "title"
    assert result.version.key_node.value == "version"
    assert result.description.key_node.value == "description"

    # The value_nodes should contain the actual values
    assert result.title.value_node.value == "Tracked API"
    assert result.version.value_node.value == "1.0.0"
    assert result.description.value_node is not None
    assert result.description.value_node.value == "API with tracked sources"

    # Check line numbers are available (for error reporting)
    assert hasattr(result.title.key_node.start_mark, "line")
    assert hasattr(result.title.value_node.start_mark, "line")


def test_mixed_extensions_and_fixed_fields(parse_yaml):
    """Test that extensions and fixed fields are properly separated."""
    yaml_content = textwrap.dedent(
        """
        title: Mixed Fields API
        x-custom: value
        version: 1.0.0
        x-another: 123
        description: An API with mixed fields
        """
    )
    root = parse_yaml(yaml_content)

    result = info.build(root)
    assert isinstance(result, info.Info)

    assert result.title is not None
    assert result.version is not None
    assert result.description is not None

    # Fixed fields should be present
    assert result.title.value == "Mixed Fields API"
    assert result.version.value == "1.0.0"
    assert result.description.value == "An API with mixed fields"

    # Extensions should be in extensions dict
    assert result.extensions is not None
    assert len(result.extensions) == 2

    ext_dict = {k.value: v.value for k, v in result.extensions.items()}
    assert ext_dict["x-custom"] == "value"
    assert ext_dict["x-another"] == 123


def test_commonmark_description(parse_yaml):
    """Test that description field can contain CommonMark formatted text."""
    yaml_content = textwrap.dedent(
        """
        title: Markdown API
        version: 1.0.0
        description: |
          # API Documentation

          This is a **bold** statement with [a link](https://example.com).

          ## Features
          - Feature 1
          - Feature 2

          ```json
          {"example": "code"}
          ```
        """
    )
    root = parse_yaml(yaml_content)

    result = info.build(root)
    assert isinstance(result, info.Info)

    assert result.description is not None
    # The low-level model should preserve the exact markdown content
    assert "# API Documentation" in result.description.value
    assert "**bold**" in result.description.value
    assert "[a link](https://example.com)" in result.description.value
    assert '{"example": "code"}' in result.description.value


def test_version_formats(parse_yaml):
    """Test that Info handles various version formats."""
    test_cases = [
        ("1.0.0", "1.0.0"),
        ("2.1.3", "2.1.3"),
        ("1.0.0-alpha", "1.0.0-alpha"),
        ("1.0.0-beta.1", "1.0.0-beta.1"),
        ("1.0.0-rc.1+build.123", "1.0.0-rc.1+build.123"),
        ("v1.0.0", "v1.0.0"),
        ('"2023-01-15"', "2023-01-15"),  # Quoted to prevent YAML date parsing
    ]

    yaml_parser = YAML()

    for version_yaml, expected_value in test_cases:
        yaml_content = f"title: API\nversion: {version_yaml}"
        root = yaml_parser.compose(yaml_content)
        result = info.build(root)

        assert isinstance(result, info.Info)
        assert result.version is not None
        assert result.version.value == expected_value


def test_nested_contact_with_invalid_data(parse_yaml):
    """Test that invalid contact data is preserved."""
    yaml_content = textwrap.dedent(
        """
        title: API
        version: 1.0.0
        contact: invalid-string
        """
    )
    root = parse_yaml(yaml_content)

    result = info.build(root)
    assert isinstance(result, info.Info)

    assert result.contact is not None
    # Should preserve the invalid string
    assert result.contact.value == "invalid-string"


def test_nested_license_with_invalid_data(parse_yaml):
    """Test that invalid license data is preserved."""
    yaml_content = textwrap.dedent(
        """
        title: API
        version: 1.0.0
        license: 123
        """
    )
    root = parse_yaml(yaml_content)

    result = info.build(root)
    assert isinstance(result, info.Info)

    assert result.license is not None
    # Should preserve the invalid number
    assert result.license.value == 123


def test_complete_real_world_example(parse_yaml):
    """Test a complete real-world Info object."""
    yaml_content = textwrap.dedent(
        """
        title: Swagger Petstore
        description: |
          This is a sample server Petstore server.
          You can find out more about Swagger at
          [http://swagger.io](http://swagger.io) or on
          [irc.freenode.net, #swagger](http://swagger.io/irc/).
        termsOfService: http://swagger.io/terms/
        contact:
          name: API Support
          url: http://www.swagger.io/support
          email: apiteam@swagger.io
        license:
          name: Apache 2.0
          url: https://www.apache.org/licenses/LICENSE-2.0.html
        version: 1.0.5
        """
    )
    root = parse_yaml(yaml_content)

    result = info.build(root)
    assert isinstance(result, info.Info)

    assert result.title is not None
    assert result.title.value == "Swagger Petstore"
    assert result.version is not None
    assert result.version.value == "1.0.5"
    assert result.description is not None
    assert "swagger.io" in result.description.value.lower()
    assert result.termsOfService is not None
    assert result.termsOfService.value == "http://swagger.io/terms/"

    # Verify nested objects
    assert result.contact is not None
    assert isinstance(result.contact.value, Contact)
    assert result.contact.value.name is not None
    assert result.contact.value.name.value == "API Support"

    assert result.license is not None
    assert isinstance(result.license.value, License)
    assert result.license.value.name is not None
    assert result.license.value.name.value == "Apache 2.0"


def test_build_with_summary_field(parse_yaml):
    """Test building Info with summary field (new in OpenAPI 3.1)."""
    yaml_content = textwrap.dedent(
        """
        title: Sample Pet Store App
        summary: A pet store API
        version: 1.0.1
        description: This is a sample server for a pet store.
        """
    )
    root = parse_yaml(yaml_content)

    result = info.build(root)
    assert isinstance(result, info.Info)

    assert result.title is not None
    assert result.title.value == "Sample Pet Store App"
    assert result.summary is not None
    assert result.summary.value == "A pet store API"
    assert result.description is not None
    assert result.description.value == "This is a sample server for a pet store."
    assert result.version is not None
    assert result.version.value == "1.0.1"


def test_build_with_summary_only(parse_yaml):
    """Test building Info with summary but no description."""
    yaml_content = textwrap.dedent(
        """
        title: API
        summary: Short summary
        version: 1.0.0
        """
    )
    root = parse_yaml(yaml_content)

    result = info.build(root)
    assert isinstance(result, info.Info)

    assert result.summary is not None
    assert result.summary.value == "Short summary"
    assert result.description is None


def test_build_without_summary(parse_yaml):
    """Test building Info without summary field (optional in OpenAPI 3.1)."""
    yaml_content = textwrap.dedent(
        """
        title: API
        version: 1.0.0
        description: A description without summary
        """
    )
    root = parse_yaml(yaml_content)

    result = info.build(root)
    assert isinstance(result, info.Info)

    assert result.summary is None
    assert result.description is not None
    assert result.description.value == "A description without summary"


def test_summary_source_tracking(parse_yaml):
    """Test that summary field preserves source location information."""
    yaml_content = textwrap.dedent(
        """
        title: Test API
        summary: Test summary
        version: 1.0.0
        """
    )
    root = parse_yaml(yaml_content)

    result = info.build(root)
    assert isinstance(result, info.Info)

    # Check that summary has source tracking
    assert result.summary is not None
    assert isinstance(result.summary, FieldSource)
    assert result.summary.key_node is not None
    assert result.summary.value_node is not None
    assert result.summary.value == "Test summary"
