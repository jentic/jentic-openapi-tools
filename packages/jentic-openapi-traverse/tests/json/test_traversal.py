"""Tests for JSON traversal functionality."""

import pytest

from jentic.apitools.openapi.traverse.json import JSONPath, TraversalNode, traverse


class TestBasicTraversal:
    """Test basic traversal of dicts and lists."""

    def test_empty_dict(self):
        """Empty dict yields no nodes."""
        data = {}
        nodes = list(traverse(data))
        assert len(nodes) == 0

    def test_empty_list(self):
        """Empty list yields no nodes."""
        data = []
        nodes = list(traverse(data))
        assert len(nodes) == 0

    def test_simple_dict(self):
        """Simple dict yields one node per key-value pair."""
        data = {"a": 1, "b": 2, "c": 3}
        nodes = list(traverse(data))

        assert len(nodes) == 3
        segments = {node.segment for node in nodes}
        assert segments == {"a", "b", "c"}
        values = {node.value for node in nodes}  # type: ignore[misc]
        assert values == {1, 2, 3}

    def test_simple_list(self):
        """Simple list yields one node per item."""
        data = ["x", "y", "z"]
        nodes = list(traverse(data))

        assert len(nodes) == 3
        segments = [node.segment for node in nodes]
        assert segments == [0, 1, 2]
        values = [node.value for node in nodes]
        assert values == ["x", "y", "z"]

    def test_scalar_root_yields_nothing(self):
        """Scalar values at root don't yield nodes."""
        for scalar in [None, True, 42, 3.14, "hello"]:
            nodes = list(traverse(scalar))
            assert len(nodes) == 0


class TestNestedStructures:
    """Test traversal of nested dicts and lists."""

    def test_nested_dict(self):
        """Nested dicts traverse all levels."""
        data = {"a": {"b": {"c": 1}}}
        nodes = list(traverse(data))

        # Should get: a, b, c
        assert len(nodes) == 3

        # Find the deepest node
        c_node = [n for n in nodes if n.segment == "c"][0]
        assert c_node.value == 1
        assert c_node.full_path == ("a", "b", "c")

    def test_list_of_dicts(self):
        """List of dicts traverses both structures."""
        data = [{"name": "Alice"}, {"name": "Bob"}]
        nodes = list(traverse(data))

        # Should get: [0], name, [1], name
        assert len(nodes) == 4

        # Check first dict
        first_dict = [n for n in nodes if n.segment == 0][0]
        assert first_dict.value == {"name": "Alice"}

        # Check name nodes
        name_nodes = [n for n in nodes if n.segment == "name"]
        assert len(name_nodes) == 2
        assert {n.value for n in name_nodes} == {"Alice", "Bob"}  # type: ignore[misc]

    def test_dict_with_list(self):
        """Dict containing list traverses both structures."""
        data = {"users": ["Alice", "Bob", "Charlie"]}
        nodes = list(traverse(data))

        # Should get: users, [0], [1], [2]
        assert len(nodes) == 4

        users_node = [n for n in nodes if n.segment == "users"][0]
        assert isinstance(users_node.value, list)
        assert len(users_node.value) == 3

    def test_deeply_nested_mixed(self):
        """Complex nested structure."""
        data = {"level1": {"level2": [{"level3": "value1"}, {"level3": "value2"}]}}
        nodes = list(traverse(data))

        # Verify we can reach the deepest values
        level3_nodes = [n for n in nodes if n.segment == "level3"]
        assert len(level3_nodes) == 2
        assert {n.value for n in level3_nodes} == {"value1", "value2"}  # type: ignore[misc]


class TestPathTracking:
    """Test path and ancestor tracking."""

    def test_path_empty_at_root_level(self):
        """Root level items have empty path."""
        data = {"a": 1, "b": 2}
        nodes = list(traverse(data))

        for node in nodes:
            assert node.path == ()
            assert node.parent is data

    def test_path_tracks_nesting(self):
        """Path correctly tracks nesting."""
        data = {"a": {"b": {"c": 1}}}
        nodes = list(traverse(data))

        # Find each node and verify path
        a_node = [n for n in nodes if n.segment == "a"][0]
        assert a_node.path == ()

        b_node = [n for n in nodes if n.segment == "b"][0]
        assert b_node.path == ("a",)

        c_node = [n for n in nodes if n.segment == "c"][0]
        assert c_node.path == ("a", "b")

    def test_full_path_property(self):
        """full_path includes the current segment."""
        data = {"a": {"b": {"c": 1}}}
        nodes = list(traverse(data))

        c_node = [n for n in nodes if n.segment == "c"][0]
        assert c_node.path == ("a", "b")
        assert c_node.full_path == ("a", "b", "c")

    def test_ancestors_empty_at_root(self):
        """Root level items have no ancestors."""
        data = {"a": 1}
        nodes = list(traverse(data))

        assert nodes[0].ancestors == ()

    def test_ancestors_track_containers(self):
        """Ancestors contain parent containers."""
        data = {"outer": {"inner": {"value": 42}}}
        nodes = list(traverse(data))

        value_node = [n for n in nodes if n.segment == "value"][0]

        # Ancestors should be [root_dict, inner_dict]
        assert len(value_node.ancestors) == 2
        assert value_node.ancestors[0] is data
        assert value_node.ancestors[1] == {"inner": {"value": 42}}


class TestFormatPath:
    """Test path formatting."""

    def test_format_path_default_separator(self):
        """Default separator is dot."""
        data = {"a": {"b": {"c": 1}}}
        nodes = list(traverse(data))

        c_node = [n for n in nodes if n.segment == "c"][0]
        assert c_node.format_path() == "a.b.c"

    def test_format_path_custom_separator(self):
        """Custom separator works."""
        data = {"a": {"b": {"c": 1}}}
        nodes = list(traverse(data))

        c_node = [n for n in nodes if n.segment == "c"][0]
        assert c_node.format_path(separator="/") == "a/b/c"

    def test_format_path_with_list_indices(self):
        """List indices formatted with brackets."""
        data = {"users": [{"name": "Alice"}]}
        nodes = list(traverse(data))

        name_node = [n for n in nodes if n.segment == "name"][0]
        assert name_node.format_path() == "users[0].name"

    def test_format_path_single_segment(self):
        """Single segment has no separator."""
        data = {"key": "value"}
        nodes = list(traverse(data))

        assert nodes[0].format_path() == "key"

    def test_format_path_list_only(self):
        """List-only path formats correctly."""
        data = [[["nested"]]]
        nodes = list(traverse(data))

        deepest = [n for n in nodes if n.value == "nested"][0]
        assert deepest.format_path() == "[0][0][0]"


class TestTraversalNode:
    """Test TraversalNode dataclass properties."""

    def test_node_immutable(self):
        """TraversalNode is frozen."""
        from dataclasses import FrozenInstanceError

        data = {"a": 1}
        node = list(traverse(data))[0]

        with pytest.raises(FrozenInstanceError):
            node.segment = "changed"  # type: ignore

    def test_node_has_all_attributes(self):
        """TraversalNode has all required attributes."""
        data = {"key": "value"}
        node = list(traverse(data))[0]

        assert hasattr(node, "path")
        assert hasattr(node, "parent")
        assert hasattr(node, "segment")
        assert hasattr(node, "value")
        assert hasattr(node, "ancestors")


class TestRealWorldStructures:
    """Test with realistic OpenAPI-like structures."""

    def test_openapi_like_structure(self):
        """Traverse OpenAPI-like document structure."""
        data = {
            "openapi": "3.1.0",
            "info": {"title": "My API", "version": "1.0.0"},
            "paths": {
                "/users": {
                    "get": {
                        "summary": "List users",
                        "responses": {"200": {"description": "Success"}},
                    }
                }
            },
        }

        nodes = list(traverse(data))

        # Verify we traverse all levels
        segments = {node.segment for node in nodes}
        assert "openapi" in segments
        assert "info" in segments
        assert "title" in segments
        assert "paths" in segments
        assert "/users" in segments
        assert "get" in segments
        assert "responses" in segments
        assert "200" in segments
        assert "description" in segments

        # Verify deep nesting works
        description_nodes = [n for n in nodes if n.segment == "description"]
        assert len(description_nodes) == 1
        assert description_nodes[0].value == "Success"
        assert len(description_nodes[0].ancestors) == 5  # depth from root


class TestEdgeCases:
    """Test edge cases and special values."""

    def test_none_values(self):
        """None values are traversed."""
        data = {"key": None}
        nodes = list(traverse(data))

        assert len(nodes) == 1
        assert nodes[0].value is None

    def test_mixed_types_in_list(self):
        """Lists with mixed types."""
        data = [1, "two", 3.0, None, True, {"key": "value"}, [1, 2]]
        nodes = list(traverse(data))

        # All 7 items plus nested dict and list items
        assert len(nodes) > 7

    def test_unicode_keys(self):
        """Unicode in dict keys."""
        data = {"emoji": "😀", "中文": "Chinese"}
        nodes = list(traverse(data))

        segments = {node.segment for node in nodes}
        assert "emoji" in segments
        assert "中文" in segments

    def test_numbers_as_string_keys(self):
        """Numeric strings as dict keys."""
        data = {"1": "one", "2": "two"}
        nodes = list(traverse(data))

        # String keys, not integers
        segments = {node.segment for node in nodes}
        assert "1" in segments
        assert "2" in segments
        assert 1 not in segments


class TestTypeAliases:
    """Test that type aliases are exported correctly."""

    def test_json_path_type_exists(self):
        """JSONPath type is available."""
        path: JSONPath = ("a", "b", 0, "c")
        assert isinstance(path, tuple)

    def test_traversal_node_type_exists(self):
        """TraversalNode type is available."""
        data = {"key": "value"}
        node = list(traverse(data))[0]
        assert isinstance(node, TraversalNode)
