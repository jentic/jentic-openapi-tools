"""
OpenAPI 3.0.4 External Documentation Object model.

Allows referencing an external resource for extended documentation.
"""

from jentic.apitools.openapi.datamodels.low.v30.specification_object import SpecificationObject


__all__ = ["ExternalDocumentation"]


class ExternalDocumentation(SpecificationObject):
    """
    Represents an External Documentation Object from OpenAPI 3.0.4.

    Allows referencing an external resource for extended documentation.

    Supports specification extensions (x-* fields).

    Example:
        >>> # Basic external docs
        >>> docs = ExternalDocumentation({
        ...     "url": "https://example.com/docs"
        ... })
        >>> docs.url
        'https://example.com/docs'

        >>> # With description
        >>> docs = ExternalDocumentation({
        ...     "description": "Find more info here",
        ...     "url": "https://example.com/docs/api"
        ... })
        >>> docs.description
        'Find more info here'
        >>> docs.url
        'https://example.com/docs/api'
    """

    _supports_extensions: bool = True
    _fixed_fields: frozenset[str] = frozenset({"description", "url"})

    @property
    def description(self) -> str | None:
        """
        A description of the target documentation.

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
    def url(self) -> str | None:
        """
        The URL for the target documentation.

        REQUIRED field.

        Returns:
            URL or None if not present
        """
        return self.get("url")

    @url.setter
    def url(self, value: str | None) -> None:
        """Set the URL."""
        if value is None:
            self.pop("url", None)
        else:
            self["url"] = value
