"""Tests for serialization module."""

import json
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from pathlib import Path
from uuid import UUID

import attrs
import pytest

from jentic.apitools.openapi.parser.core.serialization import CustomEncoder, json_dumps


class TestCustomEncoder:
    """Tests for CustomEncoder class."""

    def test_encode_datetime(self):
        """Test encoding datetime objects."""
        dt = datetime(2025, 10, 1, 14, 30, 45, 123456)
        result = json.dumps(dt, cls=CustomEncoder)
        assert result == '"2025-10-01T14:30:45.123456"'

    def test_encode_date(self):
        """Test encoding date objects."""
        d = date(2025, 10, 1)
        result = json.dumps(d, cls=CustomEncoder)
        assert result == '"2025-10-01"'

    def test_encode_uuid(self):
        """Test encoding UUID objects."""
        uuid_obj = UUID("550e8400-e29b-41d4-a716-446655440000")
        result = json.dumps(uuid_obj, cls=CustomEncoder)
        assert result == '"550e8400-e29b-41d4-a716-446655440000"'

    def test_encode_path(self):
        """Test encoding Path objects."""
        path = Path("/home/user/file.txt")
        result = json.dumps(path, cls=CustomEncoder)
        assert result == '"/home/user/file.txt"'

    def test_encode_decimal(self):
        """Test encoding Decimal objects."""
        dec = Decimal("123.456")
        result = json.dumps(dec, cls=CustomEncoder)
        assert result == "123.456"

    def test_encode_enum(self):
        """Test encoding Enum objects."""

        class Color(Enum):
            RED = "red"
            GREEN = "green"
            BLUE = "blue"

        result = json.dumps(Color.RED, cls=CustomEncoder)
        assert result == '"red"'

    def test_encode_attrs_class(self):
        """Test encoding attrs-decorated classes."""

        @attrs.define
        class Person:
            name: str
            age: int

        person = Person(name="Alice", age=30)
        result = json.dumps(person, cls=CustomEncoder)
        data = json.loads(result)
        assert data == {"name": "Alice", "age": 30}

    def test_encode_complex_nested_structure(self):
        """Test encoding complex nested structures with multiple special types."""
        data = {
            "timestamp": datetime(2025, 10, 1, 12, 0, 0),
            "id": UUID("550e8400-e29b-41d4-a716-446655440000"),
            "path": Path("/var/log/app.log"),
            "price": Decimal("99.99"),
            "nested": {"date": date(2025, 10, 1), "count": 42},
        }
        result = json.dumps(data, cls=CustomEncoder)
        parsed = json.loads(result)
        assert parsed["timestamp"] == "2025-10-01T12:00:00"
        assert parsed["id"] == "550e8400-e29b-41d4-a716-446655440000"
        assert parsed["path"] == "/var/log/app.log"
        assert parsed["price"] == 99.99
        assert parsed["nested"]["date"] == "2025-10-01"
        assert parsed["nested"]["count"] == 42

    def test_encode_unsupported_type_raises_type_error(self):
        """Test that unsupported types raise TypeError."""

        class CustomClass:
            pass

        obj = CustomClass()
        with pytest.raises(TypeError, match="not JSON serializable"):
            json.dumps(obj, cls=CustomEncoder)


class TestJsonDumps:
    """Tests for json_dumps function."""

    def test_basic_dict(self):
        """Test serializing basic dictionary."""
        data = {"name": "test", "value": 42}
        result = json_dumps(data)
        assert result == '{"name":"test","value":42}'

    def test_with_indent(self):
        """Test serializing with indentation."""
        data = {"a": 1, "b": 2}
        result = json_dumps(data, indent=2)
        assert result == '{\n  "a": 1,\n  "b": 2\n}'

    def test_sorted_keys(self):
        """Test that keys are sorted."""
        data = {"z": 1, "a": 2, "m": 3}
        result = json_dumps(data)
        # Keys should be alphabetically sorted
        assert result == '{"a":2,"m":3,"z":1}'

    def test_ensure_ascii_false(self):
        """Test that non-ASCII characters are preserved."""
        data = {"message": "Hello 世界"}
        result = json_dumps(data)
        assert "世界" in result
        assert result == '{"message":"Hello 世界"}'

    def test_with_datetime(self):
        """Test serializing data containing datetime."""
        data = {"timestamp": datetime(2025, 10, 1, 12, 0, 0)}
        result = json_dumps(data)
        assert result == '{"timestamp":"2025-10-01T12:00:00"}'

    def test_with_multiple_special_types(self):
        """Test serializing data with multiple special types."""
        data = {
            "date": date(2025, 10, 1),
            "uuid": UUID("550e8400-e29b-41d4-a716-446655440000"),
            "path": Path("/tmp/file.txt"),
            "decimal": Decimal("123.45"),
        }
        result = json_dumps(data)
        parsed = json.loads(result)
        assert parsed["date"] == "2025-10-01"
        assert parsed["uuid"] == "550e8400-e29b-41d4-a716-446655440000"
        assert parsed["path"] == "/tmp/file.txt"
        assert parsed["decimal"] == 123.45

    def test_list_of_special_types(self):
        """Test serializing lists containing special types."""
        data = [
            datetime(2025, 10, 1),
            UUID("550e8400-e29b-41d4-a716-446655440000"),
            Decimal("99.99"),
        ]
        result = json_dumps(data)
        parsed = json.loads(result)
        assert parsed == ["2025-10-01T00:00:00", "550e8400-e29b-41d4-a716-446655440000", 99.99]

    def test_custom_encoder_parameter(self):
        """Test using custom encoder class."""

        class MinimalEncoder(json.JSONEncoder):
            def default(self, o):
                if isinstance(o, datetime):
                    return "custom"
                return super().default(o)

        data = {"dt": datetime(2025, 10, 1)}
        result = json_dumps(data, cls=MinimalEncoder)
        assert result == '{"dt":"custom"}'

    def test_attrs_class_serialization(self):
        """Test serializing attrs-decorated classes."""

        @attrs.define
        class Config:
            host: str
            port: int

        data = {"config": Config(host="localhost", port=8080)}
        result = json_dumps(data)
        parsed = json.loads(result)
        assert parsed == {"config": {"host": "localhost", "port": 8080}}

    def test_empty_dict(self):
        """Test serializing empty dictionary."""
        result = json_dumps({})
        assert result == "{}"

    def test_empty_list(self):
        """Test serializing empty list."""
        result = json_dumps([])
        assert result == "[]"

    def test_none_value(self):
        """Test serializing None values."""
        data = {"value": None}
        result = json_dumps(data)
        assert result == '{"value":null}'
