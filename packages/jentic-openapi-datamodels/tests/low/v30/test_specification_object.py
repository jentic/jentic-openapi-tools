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

    def test_underscore_prefixed_field_names(self):
        """Test that field names starting with underscore are treated as data, not private attributes."""
        # OpenAPI fields can legitimately start with underscore
        obj = ConcreteSpecificationObject({"_id": "12345", "_metadata": {"version": 1}})

        # Should be stored in the dict
        assert obj["_id"] == "12345"
        assert obj["_metadata"] == {"version": 1}

        # Should be accessible via attribute access
        assert obj._id == "12345"
        assert obj._metadata == {"version": 1}

        # Should be included in length and iteration
        assert len(obj) == 2
        assert "_id" in obj
        assert "_metadata" in obj

        # Should be included in to_mapping
        result = obj.to_mapping()
        assert result["_id"] == "12345"
        assert result["_metadata"] == {"version": 1}

        # Should support assignment via attribute access
        obj._custom = "value"
        assert obj["_custom"] == "value"

    def test_internal_class_attribute_collision(self):
        """Test that OpenAPI fields don't collide with internal class attributes."""
        # Create object with field names that match internal class attributes
        obj = ConcreteSpecificationObject(
            {
                "_supports_extensions": "collision_data",
                "_fixed_fields": ["field1", "field2"],
                "x-custom": "extension_value",
            }
        )

        # Instance data should be accessible
        assert obj["_supports_extensions"] == "collision_data"
        assert obj["_fixed_fields"] == ["field1", "field2"]
        assert obj._supports_extensions == "collision_data"  # Via attribute access
        assert obj._fixed_fields == ["field1", "field2"]

        # But internal methods should still use class attributes correctly
        # get_extensions() should work because it uses type(self)._supports_extensions
        extensions = obj.get_extensions()
        assert extensions == {"x-custom": "extension_value"}

        # get_fields() should exclude x-* because class attribute is True
        fields = obj.get_fields()
        assert "_supports_extensions" in fields
        assert "_fixed_fields" in fields
        assert "x-custom" not in fields  # Excluded because class supports extensions


class TestMetadata:
    """Tests for metadata functionality."""

    def test_meta_initialized_empty(self):
        """Test that _meta is initialized as empty dict."""
        obj = ConcreteSpecificationObject()
        assert hasattr(obj, "_meta")
        assert obj._meta == {}
        assert isinstance(obj._meta, dict)

    def test_meta_initialized_with_data(self):
        """Test that _meta can be initialized with metadata via constructor."""
        metadata = {"source": "/path/to/file.yaml", "line": 42, "validated": True}
        obj = ConcreteSpecificationObject({"title": "Test API"}, meta=metadata)

        assert obj._meta == metadata
        assert obj.get_meta("source") == "/path/to/file.yaml"
        assert obj.get_meta("line") == 42
        assert obj.get_meta("validated") is True

        # Metadata should not interfere with OpenAPI data
        assert obj["title"] == "Test API"
        assert len(obj) == 1  # Only counts OpenAPI data, not metadata

    def test_meta_initialized_defensive_copy(self):
        """Test that metadata passed to constructor is defensively copied."""
        metadata = {"source": "file.yaml"}
        obj = ConcreteSpecificationObject(meta=metadata)

        # Modify the original dict
        metadata["source"] = "modified.yaml"
        metadata["new_key"] = "new_value"

        # Object's metadata should not be affected
        assert obj.get_meta("source") == "file.yaml"
        assert obj.get_meta("new_key") is None

    def test_meta_not_in_dict_interface(self):
        """Test that _meta is filtered out of the dict interface."""
        obj = ConcreteSpecificationObject({"title": "Test"})

        # _meta is in Python's __dict__ but filtered from dict interface
        assert "_meta" in obj.__dict__  # Internal Python storage
        assert "_meta" not in obj  # Dict interface (uses __contains__)
        assert "title" in obj.__dict__
        assert "title" in obj  # Regular data is accessible

    def test_meta_not_serialized(self):
        """Test that _meta is not serialized by to_mapping()."""
        obj = ConcreteSpecificationObject({"title": "Test API"})
        obj._meta["source"] = "/path/to/file.yaml"
        obj._meta["line"] = 42

        result = obj.to_mapping()
        assert result == {"title": "Test API"}
        assert "_meta" not in result

    def test_meta_not_iterated(self):
        """Test that _meta is not included in iteration."""
        obj = ConcreteSpecificationObject({"title": "Test"})
        obj._meta["custom"] = "value"

        keys = list(obj)
        assert "title" in keys
        assert "_meta" not in keys

    def test_meta_not_counted_in_len(self):
        """Test that _meta is not counted in len()."""
        obj = ConcreteSpecificationObject({"title": "Test"})
        assert len(obj) == 1

        obj._meta["custom"] = "value"
        assert len(obj) == 1  # Still 1, _meta doesn't count

    def test_set_meta_method(self):
        """Test set_meta() convenience method."""
        obj = ConcreteSpecificationObject()
        obj.set_meta("source_file", "/path/to/api.yaml")
        obj.set_meta("line_number", 100)

        assert obj._meta["source_file"] == "/path/to/api.yaml"
        assert obj._meta["line_number"] == 100

    def test_get_meta_method(self):
        """Test get_meta() convenience method."""
        obj = ConcreteSpecificationObject()
        obj._meta["validated"] = True
        obj._meta["timestamp"] = "2024-01-01"

        assert obj.get_meta("validated") is True
        assert obj.get_meta("timestamp") == "2024-01-01"
        assert obj.get_meta("missing") is None
        assert obj.get_meta("missing", "default") == "default"

    def test_clear_meta_method(self):
        """Test clear_meta() convenience method."""
        obj = ConcreteSpecificationObject()
        obj.set_meta("key1", "value1")
        obj.set_meta("key2", "value2")
        assert len(obj._meta) == 2

        obj.clear_meta()
        assert len(obj._meta) == 0
        assert obj._meta == {}

    def test_meta_direct_access(self):
        """Test direct access to _meta dict."""
        obj = ConcreteSpecificationObject()
        obj._meta["custom_data"] = {"nested": "value"}

        assert obj._meta["custom_data"] == {"nested": "value"}
        assert "custom_data" in obj._meta

    def test_meta_doesnt_interfere_with_data(self):
        """Test that metadata doesn't interfere with OpenAPI data."""
        obj = ConcreteSpecificationObject({"title": "API", "version": "1.0.0"})
        obj.set_meta("source", "file.yaml")

        # Data accessible normally
        assert obj["title"] == "API"
        assert obj.title == "API"

        # Metadata separate
        assert obj.get_meta("source") == "file.yaml"

        # Serialization only includes data
        result = obj.to_mapping()
        assert result == {"title": "API", "version": "1.0.0"}

    def test_meta_field_name_reserved(self):
        """Test that '_meta' is reserved and cannot be used as OpenAPI field name."""
        import pytest

        # Trying to create object with '_meta' field should fail
        with pytest.raises(KeyError, match="Cannot set '_meta'"):
            ConcreteSpecificationObject({"_meta": "this is OpenAPI data"})

        # Trying to set '_meta' via dict access should fail
        obj = ConcreteSpecificationObject()
        with pytest.raises(KeyError, match="Cannot set '_meta'"):
            obj["_meta"] = "value"

        # But internal _meta should work fine
        obj.set_meta("source", "file.yaml")
        assert obj.get_meta("source") == "file.yaml"
        assert obj._meta == {"source": "file.yaml"}
