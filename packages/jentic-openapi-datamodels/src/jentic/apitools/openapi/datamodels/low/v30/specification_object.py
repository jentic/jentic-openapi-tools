"""Base class for OpenAPI specification objects."""

from abc import ABC
from collections.abc import Mapping, MutableMapping, Sequence
from copy import copy
from typing import Any, Iterator, TypeVar


__all__ = ["SpecificationObject"]


T = TypeVar("T", bound="SpecificationObject")


class SpecificationObject(ABC, MutableMapping[str, Any]):
    """
    Base class for OpenAPI specification objects.

    Implements a MutableMapping interface with data stored in __dict__.
    Subclasses become dict-like objects where all attributes are accessible
    via both attribute access (obj.foo) and item access (obj["foo"]).

    Class Attributes:
        _supports_extensions: Whether this object type supports x-* specification extensions.
                             Default is True. Set to False for objects like Security Requirement
                             that are pure maps where x-* are regular keys.
    """

    _supports_extensions: bool = False

    def __init__(
        self, data: Mapping[str, Any] | None = None, *, meta: Mapping[str, Any] | None = None
    ):
        """
        Initialize a SpecificationObject.

        Args:
            data: Optional mapping to initialize the object with
            meta: Optional mapping of metadata to initialize with
        """
        # Initialize metadata storage (bypasses custom __setattr__)
        object.__setattr__(self, "_meta", dict(meta) if meta else {})

        if data:
            for key, value in data.items():
                self[key] = self._copy_value(value)

    # MutableMapping abstract methods
    def __getitem__(self, key: str) -> Any:
        """Get an item."""
        if key == "_meta":
            raise KeyError(key)
        return self.__dict__[key]

    def __setitem__(self, key: str, value: Any) -> None:
        """Set an item."""
        if key == "_meta":
            raise KeyError(
                "Cannot set '_meta' as OpenAPI data - it's reserved for internal metadata"
            )
        self.__dict__[key] = value

    def __delitem__(self, key: str) -> None:
        """Delete an item."""
        if key == "_meta":
            raise KeyError("Cannot delete internal '_meta' attribute")
        del self.__dict__[key]

    def __iter__(self) -> Iterator[str]:
        """Iterate over keys, excluding internal _meta."""
        return (k for k in self.__dict__ if k != "_meta")

    def __len__(self) -> int:
        """Return the number of items, excluding internal _meta."""
        return sum(1 for k in self.__dict__ if k != "_meta")

    def __getattr__(self, name: str) -> Any:
        """
        Get an attribute via attribute access.

        This allows both dict-style (obj["key"]) and attribute-style (obj.key) access.
        Called only when the attribute is not found through normal lookup.
        """
        # Special handling for internal metadata attribute
        if name == "_meta":
            # This should rarely be hit since _meta is set in __init__,
            # but handle it defensively
            try:
                return object.__getattribute__(self, "_meta")
            except AttributeError:
                # Initialize if somehow missing
                object.__setattr__(self, "_meta", {})
                return object.__getattribute__(self, "_meta")

        try:
            return self[name]
        except KeyError:
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

    def __setattr__(self, name: str, value: Any) -> None:
        """
        Set an attribute via attribute access.

        This allows both dict-style (obj["key"] = val) and attribute-style (obj.key = val).
        For properties and other descriptors, delegates to the descriptor.
        """
        # Special handling for internal metadata attribute
        if name == "_meta":
            object.__setattr__(self, name, value)
            return

        # Check if this is a data descriptor (property, etc.) on the class
        cls = type(self)
        if hasattr(cls, name):
            attr = getattr(cls, name)
            # If it's a data descriptor (has __set__), use normal attribute setting
            if hasattr(attr, "__set__"):
                object.__setattr__(self, name, value)
                return
        # Otherwise, store in the dict
        self[name] = value

    def get_extensions(self) -> Mapping[str, Any]:
        """
        Get specification extensions (x-* fields).

        Returns a filtered view of fields starting with 'x-'.
        If this object type doesn't support extensions (_supports_extensions=False),
        returns an empty mapping.

        Returns:
            Mapping of extension fields (keys starting with 'x-')
        """
        if not type(self)._supports_extensions:
            return {}
        return {k: v for k, v in self.items() if isinstance(k, str) and k.startswith("x-")}

    def get_fields(self) -> Mapping[str, Any]:
        """
        Get regular fields (non-extension fields).

        Returns a filtered view excluding fields starting with 'x-'.
        If this object type doesn't support extensions (_supports_extensions=False),
        returns all fields (x-* are treated as regular fields).

        Returns:
            Mapping of regular fields (excluding x-* if extensions are supported)
        """
        if not type(self)._supports_extensions:
            return dict(self)
        return {k: v for k, v in self.items() if isinstance(k, str) and not k.startswith("x-")}

    def get_meta(self, key: str, default: Any = None) -> Any:
        """
        Get a metadata value.

        Metadata is stored separately from OpenAPI specification data and is not
        serialized by to_mapping().

        Args:
            key: Metadata key to retrieve
            default: Default value if key not found

        Returns:
            Metadata value or default if not found
        """
        return self._meta.get(key, default)

    def set_meta(self, key: str, value: Any) -> None:
        """
        Set a metadata value.

        Metadata is stored separately from OpenAPI specification data and is not
        serialized by to_mapping().

        Args:
            key: Metadata key to set
            value: Metadata value to store
        """
        self._meta[key] = value

    def clear_meta(self) -> None:
        """
        Clear all metadata.

        This removes all metadata entries but does not affect OpenAPI specification data.
        """
        self._meta.clear()

    @classmethod
    def from_mapping(cls: type[T], data: Mapping[str, Any]) -> T:
        """
        Create an instance from a mapping.

        This method does not validate the structure. Use a separate
        validator to ensure the data conforms to the OpenAPI specification.

        Args:
            data: Mapping to create the object from

        Returns:
            Instance of the class

        Raises:
            TypeError: If data is not a Mapping
        """
        if not isinstance(data, Mapping):
            raise TypeError(f"Expected Mapping, got {type(data).__name__}")
        return cls(data=data)

    def to_mapping(self) -> dict[str, Any]:
        """
        Convert to a plain dictionary representation.

        Recursively converts nested SpecificationObject instances to plain dicts.
        Useful for serialization to JSON/YAML.

        Returns:
            Plain dictionary with all nested objects converted
        """
        return {key: self._marshal_value(value) for key, value in MutableMapping.items(self)}

    @classmethod
    def _marshal_value(cls, value: Any) -> Any:
        """
        Helper to recursively marshal values to plain types.

        Uses the actual class (or subclass) to support custom marshaling behavior.
        """
        if isinstance(value, SpecificationObject):
            return value.to_mapping()
        elif isinstance(value, (list, tuple)):
            return type(value)(cls._marshal_value(item) for item in value)
        elif isinstance(value, dict):
            return {k: cls._marshal_value(v) for k, v in value.items()}
        else:
            return value

    @staticmethod
    def _copy_value(value: Any) -> Any:
        """
        Defensive shallow copy for mutable collections.

        Copies mutable types (list, dict, etc.) to prevent unintended mutation
        of input data. Does not copy SpecificationObjects (already defensive).

        Args:
            value: Value to potentially copy

        Returns:
            Copy of value if mutable collection, otherwise value itself
        """

        # Don't copy SpecificationObjects (already create new instances)
        if isinstance(value, SpecificationObject):
            return value

        # Copy mutable collections (dict, list, etc.)
        # Exclude strings (they're Sequence but immutable)
        if isinstance(value, (Mapping, Sequence)) and not isinstance(value, str):
            return copy(value)

        # Primitives and immutables - no copy needed
        return value

    def __repr__(self) -> str:
        """Return a developer-friendly string representation."""
        class_name = self.__class__.__name__

        # Count regular fields and extensions separately
        extensions = self.get_extensions()
        ext_count = len(extensions)
        field_count = len(self) - ext_count

        # Build field part
        field_word = "field" if field_count == 1 else "fields"
        parts = [f"{field_count} {field_word}"]

        # Add extensions part if any
        if ext_count > 0:
            ext_word = "specification extension" if ext_count == 1 else "specification extensions"
            parts.append(f"{ext_count} {ext_word}")

        return f"<{class_name} {', '.join(parts)}>"
