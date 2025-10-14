"""
OpenAPI 3.0.4 Discriminator Object model.

When request bodies or response payloads may be one of a number of different schemas,
a discriminator object gives a hint about the expected schema.
"""

from collections.abc import Mapping

from jentic.apitools.openapi.datamodels.low.v30.specification_object import SpecificationObject


__all__ = ["Discriminator"]


class Discriminator(SpecificationObject):
    """
    Represents a Discriminator Object from OpenAPI 3.0.4.

    Used to support polymorphism by indicating which property in a payload
    is used to differentiate between schemas.

    Supports specification extensions (x-* fields).

    Example:
        >>> # Basic discriminator
        >>> disc = Discriminator({
        ...     "propertyName": "petType"
        ... })
        >>> disc.property_name
        'petType'

        >>> # With mapping
        >>> disc = Discriminator({
        ...     "propertyName": "petType",
        ...     "mapping": {
        ...         "dog": "#/components/schemas/Dog",
        ...         "cat": "#/components/schemas/Cat",
        ...         "lizard": "https://example.com/schemas/Lizard.json"
        ...     }
        ... })
        >>> disc.property_name
        'petType'
        >>> disc.mapping["dog"]
        '#/components/schemas/Dog'
    """

    _supports_extensions: bool = True
    _fixed_fields: frozenset[str] = frozenset({"propertyName", "mapping"})

    @property
    def property_name(self) -> str | None:
        """
        The name of the property in the payload to discriminate schemas.

        REQUIRED field.

        Returns:
            Property name or None if not present
        """
        return self.get("propertyName")

    @property_name.setter
    def property_name(self, value: str | None) -> None:
        """Set the property name."""
        if value is None:
            self.pop("propertyName", None)
        else:
            self["propertyName"] = value

    @property
    def mapping(self) -> dict[str, str]:
        """
        Mapping between payload values and schema names/references.

        Maps discriminator property values to schema names or references.
        When absent, the value is expected to match a schema name.

        Returns:
            Dictionary mapping values to schema references (empty dict if not present)
        """
        return self.get("mapping", {})

    @mapping.setter
    def mapping(self, value: Mapping[str, str] | None) -> None:
        """Set the mapping."""
        if value is None:
            self.pop("mapping", None)
        else:
            # Convert to plain dict once at storage time
            self["mapping"] = dict(value) if isinstance(value, Mapping) else value
