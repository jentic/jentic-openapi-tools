"""Tests for Example low-level datamodel."""

import textwrap

from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap

from jentic.apitools.openapi.datamodels.low.context import Context
from jentic.apitools.openapi.datamodels.low.sources import FieldSource, ValueSource
from jentic.apitools.openapi.datamodels.low.v31 import example


def test_build_with_value_only(parse_yaml):
    """Test building Example with only value field."""
    yaml_content = textwrap.dedent(
        """
        value:
          id: 1
          name: John Doe
        """
    )
    root = parse_yaml(yaml_content)

    result = example.build(root)
    assert isinstance(result, example.Example)

    assert result.root_node == root
    assert isinstance(result.value, FieldSource)
    assert isinstance(result.value.value, CommentedMap)
    assert result.value.value["id"] == 1
    assert result.value.value["name"] == "John Doe"

    # Optional fields should be None
    assert result.summary is None
    assert result.description is None
    assert result.external_value is None
    assert result.extensions == {}


def test_build_with_external_value_only(parse_yaml):
    """Test building Example with only externalValue field."""
    yaml_content = textwrap.dedent(
        """
        externalValue: https://example.com/examples/user.json
        """
    )
    root = parse_yaml(yaml_content)

    result = example.build(root)
    assert isinstance(result, example.Example)

    assert isinstance(result.external_value, FieldSource)
    assert result.external_value.value == "https://example.com/examples/user.json"

    assert result.summary is None
    assert result.description is None
    assert result.value is None


def test_build_with_summary_and_description(parse_yaml):
    """Test building Example with summary and description."""
    yaml_content = textwrap.dedent(
        """
        summary: A user example
        description: An example of a user object with id and name
        value:
          id: 42
          name: Alice
        """
    )
    root = parse_yaml(yaml_content)

    result = example.build(root)
    assert isinstance(result, example.Example)

    assert isinstance(result.summary, FieldSource)
    assert result.summary.value == "A user example"
    assert isinstance(result.description, FieldSource)
    assert result.description.value == "An example of a user object with id and name"
    assert isinstance(result.value, FieldSource)


def test_build_with_string_value(parse_yaml):
    """Test building Example with a simple string value."""
    yaml_content = textwrap.dedent(
        """
        summary: Simple string
        value: "Hello, World!"
        """
    )
    root = parse_yaml(yaml_content)

    result = example.build(root)
    assert isinstance(result, example.Example)

    assert isinstance(result.value, FieldSource)
    assert result.value.value == "Hello, World!"


def test_build_with_number_value(parse_yaml):
    """Test building Example with numeric values."""
    yaml_content = textwrap.dedent(
        """
        summary: Number example
        value: 42
        """
    )
    root = parse_yaml(yaml_content)

    result = example.build(root)
    assert isinstance(result, example.Example)

    assert isinstance(result.value, FieldSource)
    assert result.value.value == 42


def test_build_with_boolean_value(parse_yaml):
    """Test building Example with boolean value."""
    yaml_content = textwrap.dedent(
        """
        summary: Boolean example
        value: true
        """
    )
    root = parse_yaml(yaml_content)

    result = example.build(root)
    assert isinstance(result, example.Example)

    assert isinstance(result.value, FieldSource)
    assert result.value.value is True


def test_build_with_array_value(parse_yaml):
    """Test building Example with array value."""
    yaml_content = textwrap.dedent(
        """
        summary: Array of users
        value:
          - id: 1
            name: Alice
          - id: 2
            name: Bob
        """
    )
    root = parse_yaml(yaml_content)

    result = example.build(root)
    assert isinstance(result, example.Example)

    assert isinstance(result.value, FieldSource)
    assert isinstance(result.value.value, list)
    assert len(result.value.value) == 2
    assert result.value.value[0]["name"] == "Alice"
    assert result.value.value[1]["name"] == "Bob"


def test_build_with_null_value(parse_yaml):
    """Test building Example with null value."""
    yaml_content = textwrap.dedent(
        """
        summary: Null example
        value:
        """
    )
    root = parse_yaml(yaml_content)

    result = example.build(root)
    assert isinstance(result, example.Example)

    assert isinstance(result.value, FieldSource)
    assert result.value.value is None


def test_build_with_all_fields(parse_yaml):
    """Test building Example with all fields including extensions."""
    yaml_content = textwrap.dedent(
        """
        summary: Complete example
        description: A comprehensive example with all fields
        value:
          status: success
          code: 200
        x-internal-id: example-001
        x-category: successful-response
        """
    )
    root = parse_yaml(yaml_content)

    result = example.build(root)
    assert isinstance(result, example.Example)

    assert isinstance(result.summary, FieldSource)
    assert result.summary.value == "Complete example"
    assert isinstance(result.description, FieldSource)
    assert result.description.value == "A comprehensive example with all fields"
    assert isinstance(result.value, FieldSource)

    # Check extensions
    assert len(result.extensions) == 2
    ext_dict = {k.value: v.value for k, v in result.extensions.items()}
    assert ext_dict["x-internal-id"] == "example-001"
    assert ext_dict["x-category"] == "successful-response"


def test_build_with_commonmark_description(parse_yaml):
    """Test that Example description can contain CommonMark formatted text."""
    yaml_content = textwrap.dedent(
        """
        summary: Markdown example
        description: |
          # Example Description

          This is a **formatted** description with:
          - Bullet points
          - Multiple lines
          - `Code snippets`
        value: test
        """
    )
    root = parse_yaml(yaml_content)

    result = example.build(root)
    assert isinstance(result, example.Example)

    assert result.description is not None
    assert "# Example Description" in result.description.value
    assert "**formatted**" in result.description.value
    assert "- Bullet points" in result.description.value


def test_build_with_empty_object(parse_yaml):
    """Test building Example from empty YAML object."""
    yaml_content = "{}"
    root = parse_yaml(yaml_content)

    result = example.build(root)
    assert isinstance(result, example.Example)

    assert result.root_node == root
    assert result.summary is None
    assert result.description is None
    assert result.value is None
    assert result.external_value is None
    assert result.extensions == {}


def test_build_with_invalid_node_returns_value_source():
    """Test that build returns ValueSource for non-mapping nodes."""
    yaml_parser = YAML()

    # Scalar node
    scalar_root = yaml_parser.compose("just-a-string")
    result = example.build(scalar_root)
    assert isinstance(result, ValueSource)
    assert result.value == "just-a-string"
    assert result.value_node == scalar_root

    # Sequence node
    sequence_root = yaml_parser.compose("['item1', 'item2']")
    result = example.build(sequence_root)
    assert isinstance(result, ValueSource)
    assert result.value == ["item1", "item2"]
    assert result.value_node == sequence_root


def test_build_preserves_invalid_types(parse_yaml):
    """Test that build preserves values even with 'wrong' types."""
    yaml_content = textwrap.dedent(
        """
        summary: 12345
        description: true
        value: will-be-preserved
        externalValue: 999
        """
    )
    root = parse_yaml(yaml_content)

    result = example.build(root)
    assert isinstance(result, example.Example)

    # Should preserve the actual values, not convert them
    assert result.summary is not None
    assert result.summary.value == 12345

    assert result.description is not None
    assert result.description.value is True

    assert result.value is not None
    assert result.value.value == "will-be-preserved"

    assert result.external_value is not None
    assert result.external_value.value == 999


def test_build_with_custom_context(parse_yaml):
    """Test building Example with a custom context."""
    yaml_content = textwrap.dedent(
        """
        summary: Custom context example
        value: test-value
        """
    )
    root = parse_yaml(yaml_content)

    custom_context = Context()
    result = example.build(root, context=custom_context)
    assert isinstance(result, example.Example)

    assert isinstance(result.summary, FieldSource)
    assert result.summary.value == "Custom context example"
    assert isinstance(result.value, FieldSource)
    assert result.value.value == "test-value"


def test_source_tracking(parse_yaml):
    """Test that source location information is preserved."""
    yaml_content = textwrap.dedent(
        """
        summary: Tracked example
        description: Testing source tracking
        value:
          key: value
        """
    )
    root = parse_yaml(yaml_content)

    result = example.build(root)
    assert isinstance(result, example.Example)

    # Check summary source tracking
    assert isinstance(result.summary, FieldSource)
    assert result.summary.key_node is not None
    assert result.summary.value_node is not None
    assert result.summary.key_node.value == "summary"

    # Check description source tracking
    assert isinstance(result.description, FieldSource)
    assert result.description.key_node is not None
    assert result.description.value_node is not None
    assert result.description.key_node.value == "description"

    # Check value source tracking
    assert isinstance(result.value, FieldSource)
    assert result.value.key_node is not None
    assert result.value.value_node is not None
    assert result.value.key_node.value == "value"

    # Check line numbers are available
    assert hasattr(result.summary.key_node.start_mark, "line")
    assert hasattr(result.summary.value_node.start_mark, "line")


def test_build_with_complex_nested_value(parse_yaml):
    """Test building Example with deeply nested value structure."""
    yaml_content = textwrap.dedent(
        """
        summary: Complex nested example
        value:
          user:
            id: 123
            profile:
              name: John Doe
              email: john@example.com
              addresses:
                - type: home
                  street: 123 Main St
                - type: work
                  street: 456 Work Ave
            preferences:
              notifications: true
              theme: dark
        """
    )
    root = parse_yaml(yaml_content)

    result = example.build(root)
    assert isinstance(result, example.Example)

    assert isinstance(result.value, FieldSource)
    assert isinstance(result.value.value, CommentedMap)
    value_obj = result.value.value
    assert value_obj["user"]["id"] == 123
    assert value_obj["user"]["profile"]["name"] == "John Doe"
    assert len(value_obj["user"]["profile"]["addresses"]) == 2
    assert value_obj["user"]["preferences"]["theme"] == "dark"


def test_build_real_world_json_example(parse_yaml):
    """Test a real-world JSON response example."""
    yaml_content = textwrap.dedent(
        """
        summary: User response
        description: Example of a successful user retrieval
        value:
          id: "abc123"
          username: "johndoe"
          email: "john@example.com"
          created_at: "2023-01-15T10:30:00Z"
          is_active: true
          role: "user"
          metadata:
            last_login: "2024-01-10T14:22:00Z"
            login_count: 47
        """
    )
    root = parse_yaml(yaml_content)

    result = example.build(root)
    assert isinstance(result, example.Example)

    assert isinstance(result.summary, FieldSource)
    assert result.summary.value == "User response"
    assert isinstance(result.value, FieldSource)
    assert isinstance(result.value.value, CommentedMap)
    value_obj = result.value.value
    assert value_obj["id"] == "abc123"
    assert value_obj["is_active"] is True
    assert value_obj["metadata"]["login_count"] == 47
