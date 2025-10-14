"""
OpenAPI 3.0.4 Security Requirement Object model.

The Security Requirement Object defines which security mechanisms can be used for a
particular operation. Each named security scheme is mapped to a list of scope names
required for execution (for OAuth2/OIDC) or an empty list (for other schemes).
"""

from jentic.apitools.openapi.datamodels.low.v30.specification_object import SpecificationObject


__all__ = ["SecurityRequirement"]


class SecurityRequirement(SpecificationObject):
    """
    Represents a Security Requirement Object from OpenAPI 3.0.4.

    This IS a mapping. Keys are security scheme names, values are lists of scope strings.

    Lists the required security schemes to execute an operation. For each security
    scheme, a list of scope names is provided. When multiple Security Requirement
    Objects are defined, only ONE needs to be satisfied to authorize the request.

    IMPORTANT: Security Requirement Objects do NOT support specification extensions.
    Any key starting with "x-" is treated as a security scheme name, not an extension.

    Example:
        >>> # Non-OAuth2 requirement
        >>> req = SecurityRequirement({"api_key": []})
        >>> req["api_key"]
        []

        >>> # OAuth2 requirement with scopes
        >>> req = SecurityRequirement({"petstore_auth": ["write:pets", "read:pets"]})
        >>> req["petstore_auth"]
        ['write:pets', 'read:pets']

        >>> # Empty requirement (makes security optional)
        >>> req = SecurityRequirement({})

        >>> # Security scheme named "x-custom" (NOT an extension)
        >>> req = SecurityRequirement({"x-custom": []})
        >>> "x-custom" in req
        True
    """

    _supports_extensions: bool = False

    def __getitem__(self, key: str) -> list[str]:
        """Get scopes for a security scheme (dict-style access)."""
        return super().__getitem__(key)  # type: ignore

    def __getattr__(self, name: str) -> list[str]:
        """Get scopes for a security scheme (attribute-style access)."""
        return super().__getattr__(name)  # type: ignore

    def get_schemes(self) -> list[str]:
        """
        Get the list of security scheme names referenced.

        Returns:
            List of security scheme names
        """
        return list(self.keys())

    def get_scopes(self, scheme_name: str) -> list[str]:
        """
        Get the scopes required for a specific security scheme.

        Args:
            scheme_name: Name of the security scheme

        Returns:
            List of scope names (empty for non-OAuth2/OIDC schemes)

        Raises:
            KeyError: If scheme_name is not in this requirement
        """
        return self[scheme_name]

    def is_empty(self) -> bool:
        """
        Check if this is an empty security requirement.

        Empty requirements ({}) make security optional for an operation.

        Returns:
            True if requirements mapping is empty
        """
        return len(self) == 0
