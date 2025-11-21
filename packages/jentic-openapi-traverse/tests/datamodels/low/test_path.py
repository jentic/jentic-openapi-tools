"""Tests for NodePath path formatting."""

from ruamel.yaml import YAML

from jentic.apitools.openapi.datamodels.low.v30.info import Info
from jentic.apitools.openapi.traverse.datamodels.low.path import NodePath


class TestFormatPathJSONPointer:
    """Test format_path with JSONPointer format (RFC 6901)."""

    def test_root_node(self):
        """Root node should return empty string."""
        yaml = YAML()
        node = yaml.compose("test")
        info = Info(root_node=node)

        path = NodePath(
            node=info,
            parent=None,
            parent_field=None,
            parent_key=None,
            ancestors=(),
        )

        assert path.format_path() == ""
        assert path.format_path(path_format="jsonpointer") == ""

    def test_single_field(self):
        """Single field should return /field."""
        yaml = YAML()
        node = yaml.compose("test")
        info = Info(root_node=node)

        path = NodePath(
            node=info,
            parent=None,
            parent_field="info",
            parent_key=None,
            ancestors=(info,),
        )

        assert path.format_path() == "/info"

    def test_field_with_object_key(self):
        """Field with object key should return /field/key."""
        yaml = YAML()
        node = yaml.compose("test")
        info = Info(root_node=node)

        path = NodePath(
            node=info,
            parent=None,
            parent_field="paths",
            parent_key="/pets",
            ancestors=(info,),
        )

        # JSONPointer escapes / as ~1
        assert path.format_path() == "/paths/~1pets"

    def test_field_with_array_index(self):
        """Field with array index should return /field/index."""
        yaml = YAML()
        node = yaml.compose("test")
        info = Info(root_node=node)

        path = NodePath(
            node=info,
            parent=None,
            parent_field="parameters",
            parent_key=0,
            ancestors=(info,),
        )

        assert path.format_path() == "/parameters/0"

    def test_field_with_tilde_in_key(self):
        """Field with ~ in key should escape as ~0."""
        yaml = YAML()
        node = yaml.compose("test")
        info = Info(root_node=node)

        path = NodePath(
            node=info,
            parent=None,
            parent_field="schemas",
            parent_key="User~Draft",
            ancestors=(info,),
        )

        # JSONPointer escapes ~ as ~0
        assert path.format_path() == "/schemas/User~0Draft"

    def test_field_with_slash_and_tilde(self):
        """Field with both / and ~ should escape both."""
        yaml = YAML()
        node = yaml.compose("test")
        info = Info(root_node=node)

        path = NodePath(
            node=info,
            parent=None,
            parent_field="paths",
            parent_key="/users~1/{id}",
            ancestors=(info,),
        )

        # JSONPointer escapes ~ as ~0 and / as ~1
        assert path.format_path() == "/paths/~1users~01~1{id}"


class TestFormatPathJSONPath:
    """Test format_path with JSONPath format (RFC 9535 Normalized Path)."""

    def test_root_node(self):
        """Root node should return $."""
        yaml = YAML()
        node = yaml.compose("test")
        info = Info(root_node=node)

        path = NodePath(
            node=info,
            parent=None,
            parent_field=None,
            parent_key=None,
            ancestors=(),
        )

        assert path.format_path(path_format="jsonpath") == "$"

    def test_single_field(self):
        """Single field should return $['field']."""
        yaml = YAML()
        node = yaml.compose("test")
        info = Info(root_node=node)

        path = NodePath(
            node=info,
            parent=None,
            parent_field="info",
            parent_key=None,
            ancestors=(info,),
        )

        assert path.format_path(path_format="jsonpath") == "$['info']"

    def test_field_with_object_key(self):
        """Field with object key should return $['field']['key']."""
        yaml = YAML()
        node = yaml.compose("test")
        info = Info(root_node=node)

        path = NodePath(
            node=info,
            parent=None,
            parent_field="paths",
            parent_key="/pets",
            ancestors=(info,),
        )

        # JSONPath keeps / as-is (no escaping needed)
        assert path.format_path(path_format="jsonpath") == "$['paths']['/pets']"

    def test_field_with_array_index(self):
        """Field with array index should return $['field'][index]."""
        yaml = YAML()
        node = yaml.compose("test")
        info = Info(root_node=node)

        path = NodePath(
            node=info,
            parent=None,
            parent_field="parameters",
            parent_key=0,
            ancestors=(info,),
        )

        assert path.format_path(path_format="jsonpath") == "$['parameters'][0]"

    def test_field_with_single_quote_in_key(self):
        """Field with single quote in key should escape it."""
        yaml = YAML()
        node = yaml.compose("test")
        info = Info(root_node=node)

        path = NodePath(
            node=info,
            parent=None,
            parent_field="schemas",
            parent_key="User's Draft",
            ancestors=(info,),
        )

        # JSONPath escapes ' as \'
        assert path.format_path(path_format="jsonpath") == "$['schemas']['User\\'s Draft']"

    def test_field_with_curly_braces(self):
        """Field with curly braces should keep them as-is."""
        yaml = YAML()
        node = yaml.compose("test")
        info = Info(root_node=node)

        path = NodePath(
            node=info,
            parent=None,
            parent_field="paths",
            parent_key="/users/{id}",
            ancestors=(info,),
        )

        assert path.format_path(path_format="jsonpath") == "$['paths']['/users/{id}']"

    def test_nested_array_index(self):
        """Nested structure with array index."""
        yaml = YAML()
        node = yaml.compose("test")
        info = Info(root_node=node)

        path = NodePath(
            node=info,
            parent=None,
            parent_field="items",
            parent_key=5,
            ancestors=(info,),
        )

        assert path.format_path(path_format="jsonpath") == "$['items'][5]"


class TestFormatPathEdgeCases:
    """Test edge cases for format_path."""

    def test_integer_key_in_dict(self):
        """Integer keys in dicts should work in both formats."""
        yaml = YAML()
        node = yaml.compose("test")
        info = Info(root_node=node)

        path = NodePath(
            node=info,
            parent=None,
            parent_field="responses",
            parent_key=200,
            ancestors=(info,),
        )

        # JSONPointer: /responses/200
        assert path.format_path(path_format="jsonpointer") == "/responses/200"
        # JSONPath: $['responses'][200]
        assert path.format_path(path_format="jsonpath") == "$['responses'][200]"

    def test_empty_string_key(self):
        """Empty string key should be handled correctly."""
        yaml = YAML()
        node = yaml.compose("test")
        info = Info(root_node=node)

        path = NodePath(
            node=info,
            parent=None,
            parent_field="schemas",
            parent_key="",
            ancestors=(info,),
        )

        # JSONPointer: /schemas/
        assert path.format_path(path_format="jsonpointer") == "/schemas/"
        # JSONPath: $['schemas']['']
        assert path.format_path(path_format="jsonpath") == "$['schemas']['']"

    def test_unicode_in_key(self):
        """Unicode characters in keys should be preserved."""
        yaml = YAML()
        node = yaml.compose("test")
        info = Info(root_node=node)

        path = NodePath(
            node=info,
            parent=None,
            parent_field="schemas",
            parent_key="用户",
            ancestors=(info,),
        )

        # JSONPointer: /schemas/用户
        assert path.format_path(path_format="jsonpointer") == "/schemas/用户"
        # JSONPath: $['schemas']['用户']
        assert path.format_path(path_format="jsonpath") == "$['schemas']['用户']"

    def test_field_only_no_key(self):
        """Field without parent_key should work."""
        yaml = YAML()
        node = yaml.compose("test")
        info = Info(root_node=node)

        path = NodePath(
            node=info,
            parent=None,
            parent_field="components",
            parent_key=None,
            ancestors=(info,),
        )

        # JSONPointer: /components
        assert path.format_path(path_format="jsonpointer") == "/components"
        # JSONPath: $['components']
        assert path.format_path(path_format="jsonpath") == "$['components']"
