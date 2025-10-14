"""
OpenAPI 3.0.4 Reference Object model.

A simple object to allow referencing other components in the OpenAPI document.
"""

from jentic.apitools.openapi.datamodels.low.v30.specification_object import SpecificationObject


__all__ = ["Reference"]


class Reference(SpecificationObject):
    """
    Represents a Reference Object from OpenAPI 3.0.4.

    A simple object to allow referencing other components in the OpenAPI document,
    internally and externally.

    IMPORTANT: Reference Objects in OpenAPI 3.0.x do NOT support specification extensions.

    Example:
        >>> # Internal reference
        >>> ref = Reference({"$ref": "#/components/schemas/Pet"})
        >>> ref.ref
        '#/components/schemas/Pet'
        >>> ref["$ref"]
        '#/components/schemas/Pet'

        >>> # External reference
        >>> ref = Reference({"$ref": "https://example.com/schemas/Pet.json"})
        >>> ref.ref
        'https://example.com/schemas/Pet.json'
    """

    _supports_extensions: bool = False
    _fixed_fields: frozenset[str] = frozenset({"$ref"})

    @property
    def ref(self) -> str | None:
        """
        The reference string identifying the location of the referenced object.

        Maps to the "$ref" field in OpenAPI.

        Can be:
        - Internal: "#/components/schemas/Pet"
        - External URL: "https://example.com/schemas/Pet.json"
        - Relative file: "./schemas/Pet.yaml#/Pet"

        REQUIRED field.

        Returns:
            Reference string or None if not present
        """
        return self.get("$ref")

    @ref.setter
    def ref(self, value: str | None) -> None:
        """Set the reference string."""
        if value is None:
            self.pop("$ref", None)
        else:
            self["$ref"] = value
