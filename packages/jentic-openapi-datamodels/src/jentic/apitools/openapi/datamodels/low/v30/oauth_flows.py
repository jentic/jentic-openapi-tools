"""
OpenAPI 3.0.4 OAuth Flows Object model.

Allows configuration of the supported OAuth Flows.
"""

from collections.abc import Mapping
from typing import Any

from jentic.apitools.openapi.datamodels.low.v30.oauth_flow import OAuthFlow
from jentic.apitools.openapi.datamodels.low.v30.specification_object import SpecificationObject


__all__ = ["OAuthFlows"]


class OAuthFlows(SpecificationObject):
    """
    Represents an OAuth Flows Object from OpenAPI 3.0.4.

    Allows configuration of the supported OAuth Flows. Each property corresponds
    to a different OAuth 2.0 flow type as defined in RFC 6749.

    Supports specification extensions (x-* fields).

    Example:
        >>> # Multiple flows
        >>> flows = OAuthFlows({
        ...     "implicit": {
        ...         "authorizationUrl": "https://example.com/oauth/authorize",
        ...         "scopes": {"read": "Read access", "write": "Write access"}
        ...     },
        ...     "authorizationCode": {
        ...         "authorizationUrl": "https://example.com/oauth/authorize",
        ...         "tokenUrl": "https://example.com/oauth/token",
        ...         "scopes": {"read": "Read access", "write": "Write access"}
        ...     }
        ... })
        >>> flows.implicit.authorization_url
        'https://example.com/oauth/authorize'
        >>> flows.authorization_code.token_url
        'https://example.com/oauth/token'

        >>> # Single flow
        >>> flows = OAuthFlows({
        ...     "clientCredentials": {
        ...         "tokenUrl": "https://example.com/oauth/token",
        ...         "scopes": {"api": "API access"}
        ...     }
        ... })
        >>> flows.client_credentials.scopes
        {'api': 'API access'}
        >>> print(flows.implicit)
        None

        >>> # With extensions
        >>> flows = OAuthFlows({
        ...     "password": {
        ...         "tokenUrl": "https://example.com/oauth/token",
        ...         "scopes": {}
        ...     },
        ...     "x-flow-timeout": 3600
        ... })
        >>> flows.get_extensions()
        {'x-flow-timeout': 3600}
    """

    _supports_extensions: bool = True
    _fixed_fields: frozenset[str] = frozenset(
        {"implicit", "password", "clientCredentials", "authorizationCode"}
    )

    def __init__(self, data: Mapping[str, Any] | None = None):
        """
        Initialize an OAuthFlows object.

        Automatically marshals nested flow data (Mappings) into OAuthFlow instances.

        Args:
            data: Optional mapping to initialize the object with
        """
        super().__init__()
        if data:
            for key, value in data.items():
                if (
                    key in self._fixed_fields
                    and isinstance(value, Mapping)
                    and not isinstance(value, OAuthFlow)
                ):
                    self[key] = OAuthFlow(value)
                else:
                    # Store as-is (already OAuthFlow, extension, or other)
                    self[key] = self._copy_value(value)

    @property
    def implicit(self) -> OAuthFlow | None:
        """
        Configuration for the OAuth Implicit flow.

        Returns:
            OAuthFlow instance or None if not configured
        """
        return self.get("implicit")

    @implicit.setter
    def implicit(self, value: OAuthFlow | None) -> None:
        """Set the implicit flow configuration."""
        if value is None:
            self.pop("implicit", None)
        else:
            self["implicit"] = value

    @property
    def password(self) -> OAuthFlow | None:
        """
        Configuration for the OAuth Resource Owner Password flow.

        Returns:
            OAuthFlow instance or None if not configured
        """
        return self.get("password")

    @password.setter
    def password(self, value: OAuthFlow | None) -> None:
        """Set the password flow configuration."""
        if value is None:
            self.pop("password", None)
        else:
            self["password"] = value

    @property
    def client_credentials(self) -> OAuthFlow | None:
        """
        Configuration for the OAuth Client Credentials flow.

        Returns:
            OAuthFlow instance or None if not configured
        """
        return self.get("clientCredentials")

    @client_credentials.setter
    def client_credentials(self, value: OAuthFlow | None) -> None:
        """Set the client credentials flow configuration."""
        if value is None:
            self.pop("clientCredentials", None)
        else:
            self["clientCredentials"] = value

    @property
    def authorization_code(self) -> OAuthFlow | None:
        """
        Configuration for the OAuth Authorization Code flow.

        Returns:
            OAuthFlow instance or None if not configured
        """
        return self.get("authorizationCode")

    @authorization_code.setter
    def authorization_code(self, value: OAuthFlow | None) -> None:
        """Set the authorization code flow configuration."""
        if value is None:
            self.pop("authorizationCode", None)
        else:
            self["authorizationCode"] = value
