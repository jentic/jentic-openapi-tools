"""Tests for SecurityScheme model."""

from jentic.apitools.openapi.datamodels.low.v30.oauth_flows import OAuthFlows
from jentic.apitools.openapi.datamodels.low.v30.security_scheme import SecurityScheme


class TestSecurityScheme:
    """Tests for SecurityScheme model."""

    def test_init_empty(self):
        """Test creating empty security scheme."""
        scheme = SecurityScheme()
        assert len(scheme) == 0

    def test_init_api_key(self):
        """Test creating API key security scheme."""
        scheme = SecurityScheme({"type": "apiKey", "name": "api_key", "in": "header"})
        assert scheme.type == "apiKey"
        assert scheme.name == "api_key"
        assert scheme.in_ == "header"

    def test_init_http_basic(self):
        """Test creating HTTP basic auth scheme."""
        scheme = SecurityScheme({"type": "http", "scheme": "basic"})
        assert scheme.type == "http"
        assert scheme.scheme == "basic"

    def test_init_http_bearer(self):
        """Test creating HTTP bearer token scheme."""
        scheme = SecurityScheme({"type": "http", "scheme": "bearer", "bearerFormat": "JWT"})
        assert scheme.type == "http"
        assert scheme.scheme == "bearer"
        assert scheme.bearer_format == "JWT"

    def test_init_oauth2(self):
        """Test creating OAuth2 security scheme."""
        scheme = SecurityScheme(
            {
                "type": "oauth2",
                "flows": {
                    "implicit": {
                        "authorizationUrl": "https://example.com/authorize",
                        "scopes": {"read": "Read access"},
                    }
                },
            }
        )
        assert scheme.type == "oauth2"
        assert isinstance(scheme.flows, OAuthFlows)
        assert scheme.flows.implicit is not None

    def test_init_openid_connect(self):
        """Test creating OpenID Connect security scheme."""
        scheme = SecurityScheme(
            {
                "type": "openIdConnect",
                "openIdConnectUrl": "https://example.com/.well-known/openid-configuration",
            }
        )
        assert scheme.type == "openIdConnect"
        assert scheme.open_id_connect_url == "https://example.com/.well-known/openid-configuration"

    def test_in_property(self):
        """Test 'in' property (uses in_ due to Python keyword)."""
        scheme = SecurityScheme({"type": "apiKey", "name": "X-API-Key", "in": "header"})
        # Property uses in_ but dict uses "in"
        assert scheme.in_ == "header"
        assert scheme["in"] == "header"

    def test_flows_marshaling(self):
        """Test that flows are marshaled to OAuthFlows."""
        scheme = SecurityScheme(
            {
                "type": "oauth2",
                "flows": {
                    "authorizationCode": {
                        "authorizationUrl": "https://example.com/authorize",
                        "tokenUrl": "https://example.com/token",
                        "scopes": {},
                    }
                },
            }
        )
        assert isinstance(scheme.flows, OAuthFlows)
        assert scheme.flows.authorization_code is not None

    def test_flows_no_double_wrapping(self):
        """Test that OAuthFlows instances aren't double-wrapped."""
        flows = OAuthFlows(
            {"implicit": {"authorizationUrl": "https://example.com/authorize", "scopes": {}}}
        )
        scheme = SecurityScheme({"type": "oauth2", "flows": flows})
        assert scheme.flows is flows

    def test_property_setters(self):
        """Test property setters."""
        scheme = SecurityScheme()
        scheme.type = "apiKey"
        scheme.name = "api_key"
        scheme.in_ = "query"
        scheme.description = "API Key Authentication"

        assert scheme.type == "apiKey"
        assert scheme.name == "api_key"
        assert scheme.in_ == "query"
        assert scheme.description == "API Key Authentication"

    def test_property_setters_none(self):
        """Test setting properties to None removes them."""
        scheme = SecurityScheme(
            {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
                "description": "Bearer token",
            }
        )

        scheme.bearer_format = None
        assert "bearerFormat" not in scheme

        scheme.description = None
        assert "description" not in scheme

    def test_supports_extensions(self):
        """Test that SecurityScheme supports specification extensions."""
        scheme = SecurityScheme(
            {"type": "apiKey", "name": "api_key", "in": "header", "x-custom": "value"}
        )
        extensions = scheme.get_extensions()
        assert extensions == {"x-custom": "value"}

    def test_to_mapping(self):
        """Test converting to mapping."""
        scheme = SecurityScheme({"type": "http", "scheme": "bearer", "bearerFormat": "JWT"})
        result = scheme.to_mapping()
        assert result == {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"}

    def test_to_mapping_with_flows(self):
        """Test converting to mapping with OAuth flows."""
        scheme = SecurityScheme(
            {
                "type": "oauth2",
                "flows": {
                    "implicit": {"authorizationUrl": "https://example.com/authorize", "scopes": {}}
                },
            }
        )
        result = scheme.to_mapping()
        assert result["type"] == "oauth2"
        assert "flows" in result
        assert "implicit" in result["flows"]

    def test_from_mapping(self):
        """Test creating from mapping."""
        data = {"type": "apiKey", "name": "X-API-Key", "in": "header"}
        scheme = SecurityScheme.from_mapping(data)
        assert scheme.type == "apiKey"
        assert scheme.name == "X-API-Key"
        assert scheme.in_ == "header"
