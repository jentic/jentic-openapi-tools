"""
OpenAPI 3.0.4 OAuth Flow Object model.

Configuration details for a supported OAuth Flow as defined in RFC 6749.
Different OAuth flows use different combinations of the fields.
"""

from collections.abc import Mapping

from jentic.apitools.openapi.datamodels.low.v30.specification_object import SpecificationObject


__all__ = ["OAuthFlow"]


class OAuthFlow(SpecificationObject):
    """
    Represents an OAuth Flow Object from OpenAPI 3.0.4.

    Configuration details for a supported OAuth Flow. Different flow types
    (authorization code, implicit, password, client credentials) use different
    combinations of these fields.

    Supports specification extensions (x-* fields).

    Example:
        >>> # Authorization Code flow
        >>> flow = OAuthFlow({
        ...     "authorizationUrl": "https://example.com/oauth/authorize",
        ...     "tokenUrl": "https://example.com/oauth/token",
        ...     "scopes": {
        ...         "read:pets": "Read access to pets",
        ...         "write:pets": "Write access to pets"
        ...     }
        ... })
        >>> flow.authorization_url
        'https://example.com/oauth/authorize'
        >>> flow.scopes
        {'read:pets': 'Read access to pets', 'write:pets': 'Write access to pets'}

        >>> # Implicit flow
        >>> flow = OAuthFlow({
        ...     "authorizationUrl": "https://example.com/oauth/authorize",
        ...     "scopes": {"read": "Read access"}
        ... })
        >>> print(flow.token_url)
        None

        >>> # With extensions
        >>> flow = OAuthFlow({
        ...     "tokenUrl": "https://example.com/oauth/token",
        ...     "scopes": {},
        ...     "x-token-ttl": 3600
        ... })
        >>> flow.get_extensions()
        {'x-token-ttl': 3600}
    """

    _supports_extensions: bool = True

    @property
    def authorization_url(self) -> str | None:
        """
        OAuth authorization endpoint URL.

        REQUIRED for: authorizationCode, implicit flows.

        Returns:
            Authorization URL or None if not present
        """
        return self.get("authorizationUrl")

    @authorization_url.setter
    def authorization_url(self, value: str | None) -> None:
        """Set the authorization URL."""
        if value is None:
            self.pop("authorizationUrl", None)
        else:
            self["authorizationUrl"] = value

    @property
    def token_url(self) -> str | None:
        """
        OAuth token endpoint URL.

        REQUIRED for: authorizationCode, password, clientCredentials flows.

        Returns:
            Token URL or None if not present
        """
        return self.get("tokenUrl")

    @token_url.setter
    def token_url(self, value: str | None) -> None:
        """Set the token URL."""
        if value is None:
            self.pop("tokenUrl", None)
        else:
            self["tokenUrl"] = value

    @property
    def refresh_url(self) -> str | None:
        """
        OAuth refresh token endpoint URL (optional for all flows).

        Returns:
            Refresh URL or None if not present
        """
        return self.get("refreshUrl")

    @refresh_url.setter
    def refresh_url(self, value: str | None) -> None:
        """Set the refresh URL."""
        if value is None:
            self.pop("refreshUrl", None)
        else:
            self["refreshUrl"] = value

    @property
    def scopes(self) -> dict[str, str]:
        """
        Available scopes for the OAuth2 security scheme.

        Maps scope names to their descriptions. REQUIRED for all flows.

        Returns:
            Dictionary mapping scope names to descriptions (empty dict if not present)
        """
        scopes = self.get("scopes")
        if scopes is None:
            return {}
        return dict(scopes) if isinstance(scopes, Mapping) else {}

    @scopes.setter
    def scopes(self, value: dict[str, str] | Mapping[str, str] | None) -> None:
        """Set the scopes mapping."""
        if value is None:
            self.pop("scopes", None)
        else:
            self["scopes"] = dict(value) if isinstance(value, Mapping) else value
