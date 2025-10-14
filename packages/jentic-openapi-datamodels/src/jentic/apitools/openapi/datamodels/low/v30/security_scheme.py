"""
OpenAPI 3.0.4 Security Scheme Object model.

Defines a security scheme that can be used by the operations.
"""

from collections.abc import Mapping
from typing import Any

from jentic.apitools.openapi.datamodels.low.v30.oauth_flows import OAuthFlows
from jentic.apitools.openapi.datamodels.low.v30.specification_object import SpecificationObject


__all__ = ["SecurityScheme"]


class SecurityScheme(SpecificationObject):
    """
    Represents a Security Scheme Object from OpenAPI 3.0.4.

    Defines a security scheme that can be used by the operations. Different
    scheme types require different combinations of fields.

    Supports specification extensions (x-* fields).

    Example:
        >>> # API Key scheme
        >>> scheme = SecurityScheme({
        ...     "type": "apiKey",
        ...     "name": "api_key",
        ...     "in": "header"
        ... })
        >>> scheme.type
        'apiKey'
        >>> scheme.in_
        'header'

        >>> # HTTP Bearer scheme
        >>> scheme = SecurityScheme({
        ...     "type": "http",
        ...     "scheme": "bearer",
        ...     "bearerFormat": "JWT"
        ... })
        >>> scheme.is_http()
        True
        >>> scheme.bearer_format
        'JWT'

        >>> # OAuth2 scheme with flows
        >>> scheme = SecurityScheme({
        ...     "type": "oauth2",
        ...     "flows": {
        ...         "implicit": {
        ...             "authorizationUrl": "https://example.com/oauth/authorize",
        ...             "scopes": {"read": "Read access"}
        ...         }
        ...     }
        ... })
        >>> scheme.is_oauth2()
        True
        >>> scheme.flows.implicit.authorization_url
        'https://example.com/oauth/authorize'

        >>> # OpenID Connect scheme
        >>> scheme = SecurityScheme({
        ...     "type": "openIdConnect",
        ...     "openIdConnectUrl": "https://example.com/.well-known/openid-configuration"
        ... })
        >>> scheme.is_openid_connect()
        True
    """

    _supports_extensions: bool = True
    _fixed_fields: frozenset[str] = frozenset(
        {"type", "description", "name", "in", "scheme", "bearerFormat", "flows", "openIdConnectUrl"}
    )

    def __init__(self, data: Mapping[str, Any] | None = None):
        """
        Initialize a SecurityScheme object.

        Automatically marshals nested flows data (Mapping) into OAuthFlows instance.

        Args:
            data: Optional mapping to initialize the object with
        """
        super().__init__()
        if data:
            for key, value in data.items():
                # Marshal flows field specifically if it's a raw Mapping (not already OAuthFlows)
                if (
                    key == "flows"
                    and isinstance(value, Mapping)
                    and not isinstance(value, OAuthFlows)
                ):
                    self[key] = OAuthFlows(value)
                else:
                    # Store as-is (already OAuthFlows, extension, or other)
                    self[key] = self._copy_value(value)

    @property
    def type(self) -> str | None:
        """
        The type of the security scheme.

        Valid values: "apiKey", "http", "oauth2", "openIdConnect", "mutualTLS"

        REQUIRED field.

        Returns:
            Security scheme type or None if not present
        """
        return self.get("type")

    @type.setter
    def type(self, value: str | None) -> None:
        """Set the security scheme type."""
        if value is None:
            self.pop("type", None)
        else:
            self["type"] = value

    @property
    def description(self) -> str | None:
        """
        A description for security scheme.

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
    def name(self) -> str | None:
        """
        The name of the header, query or cookie parameter.

        REQUIRED for apiKey type.

        Returns:
            Parameter name or None if not present
        """
        return self.get("name")

    @name.setter
    def name(self, value: str | None) -> None:
        """Set the parameter name."""
        if value is None:
            self.pop("name", None)
        else:
            self["name"] = value

    @property
    def in_(self) -> str | None:
        """
        The location of the API key.

        Valid values: "query", "header", "cookie"

        REQUIRED for apiKey type.

        Note: Uses 'in_' to avoid Python keyword collision.

        Returns:
            Location or None if not present
        """
        return self.get("in")

    @in_.setter
    def in_(self, value: str | None) -> None:
        """Set the API key location."""
        if value is None:
            self.pop("in", None)
        else:
            self["in"] = value

    @property
    def scheme(self) -> str | None:
        """
        The name of the HTTP Authorization scheme.

        Examples: "bearer", "basic", "digest"

        REQUIRED for http type.

        Returns:
            Scheme name or None if not present
        """
        return self.get("scheme")

    @scheme.setter
    def scheme(self, value: str | None) -> None:
        """Set the HTTP scheme."""
        if value is None:
            self.pop("scheme", None)
        else:
            self["scheme"] = value

    @property
    def bearer_format(self) -> str | None:
        """
        A hint to the client to identify how the bearer token is formatted.

        Examples: "JWT", "opaque"

        Returns:
            Bearer format or None if not present
        """
        return self.get("bearerFormat")

    @bearer_format.setter
    def bearer_format(self, value: str | None) -> None:
        """Set the bearer format."""
        if value is None:
            self.pop("bearerFormat", None)
        else:
            self["bearerFormat"] = value

    @property
    def flows(self) -> OAuthFlows | None:
        """
        Configuration information for the OAuth flows.

        REQUIRED for oauth2 type.

        Returns:
            OAuthFlows instance or None if not present
        """
        return self.get("flows")

    @flows.setter
    def flows(self, value: OAuthFlows | None) -> None:
        """Set the OAuth flows configuration."""
        if value is None:
            self.pop("flows", None)
        else:
            self["flows"] = value

    @property
    def open_id_connect_url(self) -> str | None:
        """
        OpenID Connect URL to discover OAuth2 configuration values.

        REQUIRED for openIdConnect type.

        Returns:
            OpenID Connect URL or None if not present
        """
        return self.get("openIdConnectUrl")

    @open_id_connect_url.setter
    def open_id_connect_url(self, value: str | None) -> None:
        """Set the OpenID Connect URL."""
        if value is None:
            self.pop("openIdConnectUrl", None)
        else:
            self["openIdConnectUrl"] = value

    def is_api_key(self) -> bool:
        """
        Check if this is an API Key security scheme.

        Returns:
            True if type is "apiKey"
        """
        return self.type == "apiKey"

    def is_http(self) -> bool:
        """
        Check if this is an HTTP security scheme.

        Returns:
            True if type is "http"
        """
        return self.type == "http"

    def is_oauth2(self) -> bool:
        """
        Check if this is an OAuth2 security scheme.

        Returns:
            True if type is "oauth2"
        """
        return self.type == "oauth2"

    def is_openid_connect(self) -> bool:
        """
        Check if this is an OpenID Connect security scheme.

        Returns:
            True if type is "openIdConnect"
        """
        return self.type == "openIdConnect"
