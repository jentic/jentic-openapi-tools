"""
OpenAPI 3.0.4 XML Object model.

Metadata object for XML representation of properties.
"""

from jentic.apitools.openapi.datamodels.low.v30.specification_object import SpecificationObject


__all__ = ["XML"]


class XML(SpecificationObject):
    """
    Represents an XML Object from OpenAPI 3.0.4.

    A metadata object that allows for more fine-tuned XML model definitions.

    Supports specification extensions (x-* fields).

    Example:
        >>> # Basic XML element name override
        >>> xml = XML({"name": "animal"})
        >>> xml.name
        'animal'

        >>> # XML namespace
        >>> xml = XML({
        ...     "name": "Person",
        ...     "namespace": "http://example.com/schema/person",
        ...     "prefix": "sample"
        ... })
        >>> xml.namespace
        'http://example.com/schema/person'
    """

    _supports_extensions: bool = True
    _fixed_fields: frozenset[str] = frozenset(
        {"name", "namespace", "prefix", "attribute", "wrapped"}
    )

    @property
    def name(self) -> str | None:
        """
        Replaces the name of the element/attribute.

        Returns:
            Element/attribute name or None if not present
        """
        return self.get("name")

    @name.setter
    def name(self, value: str | None) -> None:
        """Set the element/attribute name."""
        if value is None:
            self.pop("name", None)
        else:
            self["name"] = value

    @property
    def namespace(self) -> str | None:
        """
        The URI of the namespace definition.

        Returns:
            Namespace URI or None if not present
        """
        return self.get("namespace")

    @namespace.setter
    def namespace(self, value: str | None) -> None:
        """Set the namespace URI."""
        if value is None:
            self.pop("namespace", None)
        else:
            self["namespace"] = value

    @property
    def prefix(self) -> str | None:
        """
        The prefix to be used for the name.

        Returns:
            Prefix or None if not present
        """
        return self.get("prefix")

    @prefix.setter
    def prefix(self, value: str | None) -> None:
        """Set the prefix."""
        if value is None:
            self.pop("prefix", None)
        else:
            self["prefix"] = value

    @property
    def attribute(self) -> bool | None:
        """
        Declares whether the property is an XML attribute.

        Returns:
            True if the property is an XML attribute,
            False if present and set to false,
            or None if not present.
        """
        return self.get("attribute")

    @attribute.setter
    def attribute(self, value: bool | None) -> None:
        """Set the attribute flag."""
        if value is None:
            self.pop("attribute", None)
        else:
            self["attribute"] = value

    @property
    def wrapped(self) -> bool | None:
        """
        For arrays, wraps the array in a containing element.

        Only affects arrays. Returns None when not set.

        Returns:
            True if wrapped, None if not set or not wrapped
        """
        return self.get("wrapped")

    @wrapped.setter
    def wrapped(self, value: bool | None) -> None:
        """Set the wrapped flag."""
        if value is None:
            self.pop("wrapped", None)
        else:
            self["wrapped"] = value
