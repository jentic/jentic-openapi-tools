"""Tests for SpecificationObject base class."""

import pytest

from jentic.apitools.openapi.datamodels.low.v30.specification_object import SpecificationObject


class ConcreteSpecificationObject(SpecificationObject):
    """Concrete implementation for testing."""

    _supports_extensions: bool = True


class TestSpecificationObject:
    """Tests for SpecificationObject."""

    def test_init_empty(self):
        """Test creating empty specification object."""
        obj = ConcreteSpecificationObject()
        assert len(obj) == 0
        assert dict(obj) == {}

    def test_init_with_data(self):
        """Test creating specification object with data."""
        data = {"foo": "bar", "baz": 123}
        obj = ConcreteSpecificationObject(data)
        assert len(obj) == 2
        assert obj["foo"] == "bar"
        assert obj["baz"] == 123

    def test_dict_access(self):
        """Test dictionary-style access."""
        obj = ConcreteSpecificationObject()
        obj["key"] = "value"
        assert obj["key"] == "value"
        assert "key" in obj
        del obj["key"]
        assert "key" not in obj

    def test_attribute_access(self):
        """Test attribute-style access."""
        obj = ConcreteSpecificationObject()
        obj.key = "value"
        assert obj.key == "value"
        assert obj["key"] == "value"

    def test_iteration(self):
        """Test iterating over keys."""
        obj = ConcreteSpecificationObject({"a": 1, "b": 2, "c": 3})
        keys = list(obj)
        assert keys == ["a", "b", "c"]

    def test_get_extensions_when_supported(self):
        """Test getting extensions when supported."""
        obj = ConcreteSpecificationObject({"foo": "bar", "x-custom": "extension"})
        extensions = obj.get_extensions()
        assert extensions == {"x-custom": "extension"}

    def test_get_extensions_when_not_supported(self):
        """Test getting extensions when not supported."""

        class NoExtensions(SpecificationObject):
            _supports_extensions: bool = False

        obj = NoExtensions({"foo": "bar", "x-custom": "value"})
        extensions = obj.get_extensions()
        assert extensions == {}

    def test_get_fields_with_extensions_supported(self):
        """Test getting fields when extensions are supported."""
        obj = ConcreteSpecificationObject({"foo": "bar", "x-custom": "extension"})
        fields = obj.get_fields()
        assert fields == {"foo": "bar"}

    def test_get_fields_without_extensions(self):
        """Test getting fields when extensions not supported."""

        class NoExtensions(SpecificationObject):
            _supports_extensions: bool = False

        obj = NoExtensions({"foo": "bar", "x-custom": "value"})
        fields = obj.get_fields()
        assert fields == {"foo": "bar", "x-custom": "value"}

    def test_to_mapping_simple(self):
        """Test converting to mapping."""
        obj = ConcreteSpecificationObject({"foo": "bar", "num": 123})
        result = obj.to_mapping()
        assert result == {"foo": "bar", "num": 123}

    def test_to_mapping_nested(self):
        """Test converting nested objects to mapping."""
        inner = ConcreteSpecificationObject({"inner": "value"})
        outer = ConcreteSpecificationObject({"outer": inner})
        result = outer.to_mapping()
        assert result == {"outer": {"inner": "value"}}

    def test_to_mapping_with_list(self):
        """Test converting objects with lists to mapping."""
        inner1 = ConcreteSpecificationObject({"a": 1})
        inner2 = ConcreteSpecificationObject({"b": 2})
        obj = ConcreteSpecificationObject({"items": [inner1, inner2]})
        result = obj.to_mapping()
        assert result == {"items": [{"a": 1}, {"b": 2}]}

    def test_from_mapping(self):
        """Test creating from mapping."""
        data = {"foo": "bar", "num": 123}
        obj = ConcreteSpecificationObject.from_mapping(data)
        assert obj["foo"] == "bar"
        assert obj["num"] == 123

    def test_from_mapping_invalid_type(self):
        """Test creating from invalid type raises error."""
        with pytest.raises(TypeError, match="Expected Mapping"):
            ConcreteSpecificationObject.from_mapping("not a mapping")  # type: ignore[arg-type]

    def test_repr(self):
        """Test string representation."""
        obj = ConcreteSpecificationObject({"foo": "bar", "x-custom": "ext"})
        repr_str = repr(obj)
        assert "ConcreteSpecificationObject" in repr_str
        assert "1 field" in repr_str
        assert "1 specification extension" in repr_str
