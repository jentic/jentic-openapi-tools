"""Tests for OAuthFlows model."""

from jentic.apitools.openapi.datamodels.low.v30.oauth_flow import OAuthFlow
from jentic.apitools.openapi.datamodels.low.v30.oauth_flows import OAuthFlows


class TestOAuthFlows:
    """Tests for OAuthFlows model."""

    def test_init_empty(self):
        """Test creating empty OAuth flows."""
        flows = OAuthFlows()
        assert len(flows) == 0

    def test_init_with_implicit(self):
        """Test creating with implicit flow."""
        flows = OAuthFlows(
            {"implicit": {"authorizationUrl": "https://example.com/authorize", "scopes": {}}}
        )
        assert isinstance(flows.implicit, OAuthFlow)
        assert flows.implicit.authorization_url == "https://example.com/authorize"

    def test_init_with_password(self):
        """Test creating with password flow."""
        flows = OAuthFlows({"password": {"tokenUrl": "https://example.com/token", "scopes": {}}})
        assert isinstance(flows.password, OAuthFlow)
        assert flows.password.token_url == "https://example.com/token"

    def test_init_with_client_credentials(self):
        """Test creating with clientCredentials flow."""
        flows = OAuthFlows(
            {"clientCredentials": {"tokenUrl": "https://example.com/token", "scopes": {}}}
        )
        assert isinstance(flows.client_credentials, OAuthFlow)
        assert flows.client_credentials.token_url == "https://example.com/token"

    def test_init_with_authorization_code(self):
        """Test creating with authorizationCode flow."""
        flows = OAuthFlows(
            {
                "authorizationCode": {
                    "authorizationUrl": "https://example.com/authorize",
                    "tokenUrl": "https://example.com/token",
                    "scopes": {},
                }
            }
        )
        assert isinstance(flows.authorization_code, OAuthFlow)
        assert flows.authorization_code.authorization_url == "https://example.com/authorize"
        assert flows.authorization_code.token_url == "https://example.com/token"

    def test_init_with_multiple_flows(self):
        """Test creating with multiple flows."""
        flows = OAuthFlows(
            {
                "implicit": {"authorizationUrl": "https://example.com/authorize", "scopes": {}},
                "authorizationCode": {
                    "authorizationUrl": "https://example.com/authorize",
                    "tokenUrl": "https://example.com/token",
                    "scopes": {},
                },
            }
        )
        assert isinstance(flows.implicit, OAuthFlow)
        assert isinstance(flows.authorization_code, OAuthFlow)

    def test_init_avoids_double_wrapping(self):
        """Test that already-wrapped OAuthFlow instances aren't double-wrapped."""
        flow = OAuthFlow({"tokenUrl": "https://example.com/token", "scopes": {}})
        flows = OAuthFlows({"password": flow})
        assert flows.password is flow

    def test_property_setters(self):
        """Test setting flow properties."""
        flows = OAuthFlows()

        implicit_flow = OAuthFlow(
            {"authorizationUrl": "https://example.com/authorize", "scopes": {}}
        )
        flows.implicit = implicit_flow
        assert flows.implicit is implicit_flow

    def test_property_setters_none(self):
        """Test setting properties to None removes them."""
        flows = OAuthFlows(
            {"implicit": {"authorizationUrl": "https://example.com/authorize", "scopes": {}}}
        )
        flows.implicit = None
        assert "implicit" not in flows

    def test_property_getters_return_none(self):
        """Test property getters return None when not set."""
        flows = OAuthFlows()
        assert flows.implicit is None
        assert flows.password is None
        assert flows.client_credentials is None
        assert flows.authorization_code is None

    def test_supports_extensions(self):
        """Test that OAuthFlows supports specification extensions."""
        flows = OAuthFlows(
            {
                "implicit": {"authorizationUrl": "https://example.com/authorize", "scopes": {}},
                "x-custom": "value",
            }
        )
        extensions = flows.get_extensions()
        assert extensions == {"x-custom": "value"}

    def test_to_mapping(self):
        """Test converting to mapping."""
        flows = OAuthFlows(
            {
                "implicit": {
                    "authorizationUrl": "https://example.com/authorize",
                    "scopes": {"read": "Read access"},
                },
                "password": {"tokenUrl": "https://example.com/token", "scopes": {}},
            }
        )
        result = flows.to_mapping()
        assert "implicit" in result
        assert "password" in result
        assert result["implicit"]["authorizationUrl"] == "https://example.com/authorize"
        assert result["password"]["tokenUrl"] == "https://example.com/token"

    def test_from_mapping(self):
        """Test creating from mapping."""
        data = {
            "authorizationCode": {
                "authorizationUrl": "https://example.com/authorize",
                "tokenUrl": "https://example.com/token",
                "scopes": {},
            }
        }
        flows = OAuthFlows.from_mapping(data)
        assert isinstance(flows.authorization_code, OAuthFlow)
