"""Tests for introspection utilities."""

from dataclasses import dataclass

from ruamel.yaml import YAML

from jentic.apitools.openapi.datamodels.low.sources import FieldSource, KeySource, ValueSource
from jentic.apitools.openapi.datamodels.low.v30.contact import Contact
from jentic.apitools.openapi.datamodels.low.v30.example import Example
from jentic.apitools.openapi.datamodels.low.v30.info import Info
from jentic.apitools.openapi.datamodels.low.v30.license import License
from jentic.apitools.openapi.datamodels.low.v30.openapi import OpenAPI30
from jentic.apitools.openapi.datamodels.low.v30.path_item import PathItem
from jentic.apitools.openapi.datamodels.low.v30.paths import Paths
from jentic.apitools.openapi.traverse.datamodels.low.introspection import (
    get_traversable_fields,
    is_datamodel_node,
    unwrap_value,
)


class TestIsDatamodelNode:
    """Test is_datamodel_node function."""

    def test_recognizes_low_level_datamodels(self):
        """Should return True for low-level datamodel objects."""
        yaml = YAML()
        yaml_node = yaml.compose("3.0.4")

        # Create actual low-level datamodels
        info = Info(root_node=yaml_node)
        openapi_doc = OpenAPI30(root_node=yaml_node)

        # Both should be recognized as datamodel nodes
        assert is_datamodel_node(info) is True
        assert is_datamodel_node(openapi_doc) is True

    def test_rejects_none(self):
        """Should return False for None."""
        assert is_datamodel_node(None) is False

    def test_rejects_primitives(self):
        """Should return False for primitive types."""
        assert is_datamodel_node("string") is False
        assert is_datamodel_node(123) is False
        assert is_datamodel_node(45.67) is False
        assert is_datamodel_node(True) is False
        assert is_datamodel_node([]) is False
        assert is_datamodel_node({}) is False

    def test_rejects_wrapper_types(self):
        """Should return False for FieldSource/ValueSource/KeySource."""
        # These are dataclasses but don't have root_node
        from ruamel.yaml import YAML

        yaml = YAML()
        node = yaml.compose("test")

        field_source = FieldSource(value="test", key_node=node, value_node=node)
        value_source = ValueSource(value="test", value_node=node)
        key_source = KeySource(value="test", key_node=node)

        assert is_datamodel_node(field_source) is False
        assert is_datamodel_node(value_source) is False
        assert is_datamodel_node(key_source) is False

    def test_rejects_arbitrary_dataclasses(self):
        """Should return False for arbitrary dataclasses without root_node."""

        @dataclass
        class CustomDataclass:
            name: str
            value: int

        obj = CustomDataclass(name="test", value=42)
        assert is_datamodel_node(obj) is False

    def test_accepts_dataclass_with_root_node(self):
        """Should return True for any dataclass with root_node attribute."""
        from ruamel.yaml import YAML

        @dataclass
        class MockDatamodel:
            root_node: object
            value: str

        yaml = YAML()
        node = yaml.compose("test")
        mock_obj = MockDatamodel(root_node=node, value="test")

        assert is_datamodel_node(mock_obj) is True


class TestUnwrapValue:
    """Test unwrap_value function."""

    def test_unwraps_field_source(self):
        """Should unwrap FieldSource to get actual value."""
        yaml = YAML()
        node = yaml.compose("test_value")

        field_source = FieldSource(value="test_value", key_node=node, value_node=node)
        unwrapped = unwrap_value(field_source)

        assert unwrapped == "test_value"

    def test_unwraps_value_source(self):
        """Should unwrap ValueSource to get actual value."""
        yaml = YAML()
        node = yaml.compose("42")

        value_source = ValueSource(value=42, value_node=node)
        unwrapped = unwrap_value(value_source)

        assert unwrapped == 42

    def test_unwraps_key_source(self):
        """Should unwrap KeySource to get actual value."""
        yaml = YAML()
        node = yaml.compose("my_key")

        key_source = KeySource(value="my_key", key_node=node)
        unwrapped = unwrap_value(key_source)

        assert unwrapped == "my_key"

    def test_does_not_unwrap_example_node(self):
        """Should NOT unwrap Example node (has .value field but is a datamodel)."""
        yaml = YAML()
        yaml_text = "summary: test example\nvalue: 123"
        node = yaml.compose(yaml_text)

        example = Example(root_node=node)
        unwrapped = unwrap_value(example)

        # Should return the Example itself, not its .value field
        assert unwrapped is example
        assert isinstance(unwrapped, Example)

    def test_does_not_unwrap_primitives(self):
        """Should NOT unwrap primitive types."""
        assert unwrap_value("string") == "string"
        assert unwrap_value(123) == 123
        assert unwrap_value(45.67) == 45.67
        assert unwrap_value(True) is True
        assert unwrap_value(None) is None

    def test_does_not_unwrap_collections(self):
        """Should NOT unwrap list or dict."""
        test_list = [1, 2, 3]
        test_dict = {"key": "value"}

        assert unwrap_value(test_list) is test_list
        assert unwrap_value(test_dict) is test_dict

    def test_does_not_unwrap_arbitrary_object_with_value_attr(self):
        """Should NOT unwrap arbitrary objects that happen to have .value attribute."""

        @dataclass
        class CustomObject:
            value: str

        obj = CustomObject(value="test")
        unwrapped = unwrap_value(obj)

        # Should return the object itself, not unwrap it
        assert unwrapped is obj

    def test_does_not_unwrap_non_dataclass_with_value(self):
        """Should NOT unwrap non-dataclass objects with .value attribute."""

        class RegularClass:
            def __init__(self):
                self.value = "test"
                self.key_node = "fake_node"

        obj = RegularClass()
        unwrapped = unwrap_value(obj)

        # Should return the object itself since it's not a dataclass
        assert unwrapped is obj


class TestGetTraversableFields:
    """Test get_traversable_fields function."""

    def test_returns_empty_for_non_dataclass(self):
        """Should return empty list for non-dataclass values."""
        assert get_traversable_fields("string") == []
        assert get_traversable_fields(123) == []
        assert get_traversable_fields(None) == []
        assert get_traversable_fields([1, 2, 3]) == []
        assert get_traversable_fields({"key": "value"}) == []

    def test_returns_fixed_fields_with_datamodel_values(self):
        """Should return fixed fields that contain datamodel nodes."""
        yaml = YAML()
        node = yaml.compose("test")

        # Create Info with contact and license (both are datamodel nodes)
        contact = Contact(root_node=node)
        license_obj = License(root_node=node)

        info = Info(
            root_node=node,
            contact=FieldSource(value=contact, key_node=node, value_node=node),
            license=FieldSource(value=license_obj, key_node=node, value_node=node),
        )

        fields = get_traversable_fields(info)
        field_names = [name for name, _ in fields]

        # Should include contact and license (they contain datamodels)
        assert "contact" in field_names
        assert "license" in field_names

    def test_skips_none_values(self):
        """Should skip fields with None values."""
        yaml = YAML()
        node = yaml.compose("test")

        # Create Info with only title (required), rest are None
        info = Info(
            root_node=node,
            title=FieldSource(value="Test API", key_node=node, value_node=node),
            version=FieldSource(value="1.0.0", key_node=node, value_node=node),
            # contact, license, etc. are None
        )

        fields = get_traversable_fields(info)
        field_names = [name for name, _ in fields]

        # Should not include None fields
        assert "contact" not in field_names
        assert "license" not in field_names

    def test_skips_scalar_primitive_values(self):
        """Should skip fields with scalar primitive values."""
        yaml = YAML()
        node = yaml.compose("test")

        # Create Info with string values (title, version, description)
        info = Info(
            root_node=node,
            title=FieldSource(value="Test API", key_node=node, value_node=node),
            version=FieldSource(value="1.0.0", key_node=node, value_node=node),
            description=FieldSource(value="A test API", key_node=node, value_node=node),
        )

        fields = get_traversable_fields(info)
        field_names = [name for name, _ in fields]

        # Scalar strings should be filtered out
        assert "title" not in field_names
        assert "version" not in field_names
        assert "description" not in field_names

    def test_returns_wrapped_values_not_unwrapped(self):
        """Should return FieldSource wrappers, not the unwrapped values."""
        yaml = YAML()
        node = yaml.compose("test")

        contact = Contact(root_node=node)
        contact_wrapped = FieldSource(value=contact, key_node=node, value_node=node)

        info = Info(root_node=node, contact=contact_wrapped)

        fields = get_traversable_fields(info)

        # Find contact field
        contact_field = next((value for name, value in fields if name == "contact"), None)

        # Should return the wrapped value, not the unwrapped Contact
        assert contact_field is contact_wrapped
        assert isinstance(contact_field, FieldSource)

    def test_includes_collections_of_datamodels(self):
        """Should include fields containing lists/dicts with datamodels."""
        yaml = YAML()
        node = yaml.compose("test")

        # Create Info with servers (list of Server objects)
        # servers is a fixed field in OpenAPI30 that contains a list
        doc = OpenAPI30(
            root_node=node,
            info=FieldSource(value=Info(root_node=node), key_node=node, value_node=node),
        )

        fields = get_traversable_fields(doc)
        field_names = [name for name, _ in fields]

        # info contains a datamodel, should be included
        assert "info" in field_names

    def test_caching_works(self):
        """Should cache field names for same class type."""
        yaml = YAML()
        node1 = yaml.compose("test1")
        node2 = yaml.compose("test2")

        info1 = Info(root_node=node1)
        info2 = Info(root_node=node2)

        # First call - computes and caches
        fields1 = get_traversable_fields(info1)

        # Second call - should use cache
        fields2 = get_traversable_fields(info2)

        # Both should have same field names structure
        names1 = {name for name, _ in fields1}
        names2 = {name for name, _ in fields2}
        assert names1 == names2

    def test_does_not_return_root_node(self):
        """Should not return root_node field."""
        yaml = YAML()
        node = yaml.compose("test")

        info = Info(root_node=node)

        fields = get_traversable_fields(info)
        field_names = [name for name, _ in fields]

        # root_node is infrastructure, shouldn't be in traversable fields
        assert "root_node" not in field_names

    def test_returns_patterned_fields(self):
        """Should return patterned fields (like Paths.paths)."""
        yaml = YAML()
        node = yaml.compose("test")

        # Paths.paths is a patterned field (holds dynamic path keys)
        path_item = PathItem(root_node=node)
        paths = Paths(
            root_node=node,
            paths={KeySource(value="/users", key_node=node): path_item},
        )

        fields = get_traversable_fields(paths)
        field_names = [name for name, _ in fields]

        # paths is a patterned field containing dict with PathItem values
        assert "paths" in field_names
