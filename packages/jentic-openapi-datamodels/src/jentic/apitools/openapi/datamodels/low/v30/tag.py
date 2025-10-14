"""
OpenAPI 3.0.4 Tag Object model.

Adds metadata to a single tag that is used by operations.
"""

from collections.abc import Mapping
from typing import Any

from jentic.apitools.openapi.datamodels.low.v30.external_documentation import (
    ExternalDocumentation,
)
from jentic.apitools.openapi.datamodels.low.v30.specification_object import SpecificationObject


__all__ = ["Tag"]


class Tag(SpecificationObject):
    """
    Represents a Tag Object from OpenAPI 3.0.4.

    Adds metadata to a single tag that is used by the Operation Object.
    It is not mandatory to have a Tag Object per tag defined in the Operation Object instances.

    Supports specification extensions (x-* fields).

    Example:
        >>> # Basic tag
        >>> tag = Tag({
        ...     "name": "pet",
        ...     "description": "Everything about your Pets"
        ... })
        >>> tag.name
        'pet'
        >>> tag.description
        'Everything about your Pets'

        >>> # Tag with external docs
        >>> tag = Tag({
        ...     "name": "store",
        ...     "description": "Access to Petstore orders",
        ...     "externalDocs": {
        ...         "description": "Find out more",
        ...         "url": "http://example.com"
        ...     }
        ... })
        >>> tag.external_docs.url
        'http://example.com'
    """

    _supports_extensions: bool = True
    _fixed_fields: frozenset[str] = frozenset({"name", "description", "externalDocs"})

    def __init__(self, data: Mapping[str, Any] | None = None):
        """
        Initialize a Tag object.

        Automatically marshals nested externalDocs data (Mapping) into ExternalDocumentation instance.

        Args:
            data: Optional mapping to initialize the object with
        """
        super().__init__()
        if data:
            for key, value in data.items():
                # Marshal externalDocs field specifically if it's a raw Mapping
                if (
                    key == "externalDocs"
                    and isinstance(value, Mapping)
                    and not isinstance(value, ExternalDocumentation)
                ):
                    self[key] = ExternalDocumentation(value)
                else:
                    # Store as-is (already ExternalDocumentation, extension, or other)
                    self[key] = self._copy_value(value)

    @property
    def name(self) -> str | None:
        """
        The name of the tag.

        REQUIRED field.

        Returns:
            Tag name or None if not present
        """
        return self.get("name")

    @name.setter
    def name(self, value: str | None) -> None:
        """Set the tag name."""
        if value is None:
            self.pop("name", None)
        else:
            self["name"] = value

    @property
    def description(self) -> str | None:
        """
        A description for the tag.

        Returns:
            Description or None if not present
        """
        return self.get("description")

    @description.setter
    def description(self, value: str | None) -> None:
        """Set the description."""
        if value is None:
            self.pop("description", None)
        else:
            self["description"] = value

    @property
    def external_docs(self) -> ExternalDocumentation | None:
        """
        Additional external documentation for this tag.

        Returns:
            ExternalDocumentation instance or None if not present
        """
        return self.get("externalDocs")

    @external_docs.setter
    def external_docs(self, value: ExternalDocumentation | None) -> None:
        """Set the external documentation."""
        if value is None:
            self.pop("externalDocs", None)
        else:
            self["externalDocs"] = value
