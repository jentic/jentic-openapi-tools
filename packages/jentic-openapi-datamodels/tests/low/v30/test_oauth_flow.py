"""Tests for OAuthFlow model."""

from jentic.apitools.openapi.datamodels.low.v30.oauth_flow import OAuthFlow


class TestOAuthFlow:
    """Tests for OAuthFlow model."""

    def test_init_empty(self):
        """Test creating empty OAuth flow."""
        flow = OAuthFlow()
        assert len(flow) == 0

    def test_init_implicit_flow(self):
        """Test creating implicit flow."""
        flow = OAuthFlow(
            {
                "authorizationUrl": "https://example.com/authorize",
                "scopes": {"read": "Read access", "write": "Write access"},
            }
        )
        assert flow.authorization_url == "https://example.com/authorize"
        assert flow.scopes == {"read": "Read access", "write": "Write access"}

    def test_init_authorization_code_flow(self):
        """Test creating authorization code flow."""
        flow = OAuthFlow(
            {
                "authorizationUrl": "https://example.com/authorize",
                "tokenUrl": "https://example.com/token",
                "scopes": {},
            }
        )
        assert flow.authorization_url == "https://example.com/authorize"
        assert flow.token_url == "https://example.com/token"
        assert flow.scopes == {}

    def test_init_with_refresh_url(self):
        """Test creating flow with refresh URL."""
        flow = OAuthFlow(
            {
                "tokenUrl": "https://example.com/token",
                "refreshUrl": "https://example.com/refresh",
                "scopes": {},
            }
        )
        assert flow.token_url == "https://example.com/token"
        assert flow.refresh_url == "https://example.com/refresh"

    def test_authorization_url_setter(self):
        """Test setting authorization URL."""
        flow = OAuthFlow()
        flow.authorization_url = "https://example.com/oauth/authorize"
        assert flow.authorization_url == "https://example.com/oauth/authorize"
        assert flow["authorizationUrl"] == "https://example.com/oauth/authorize"

    def test_token_url_setter(self):
        """Test setting token URL."""
        flow = OAuthFlow()
        flow.token_url = "https://example.com/oauth/token"
        assert flow.token_url == "https://example.com/oauth/token"

    def test_refresh_url_setter(self):
        """Test setting refresh URL."""
        flow = OAuthFlow()
        flow.refresh_url = "https://example.com/oauth/refresh"
        assert flow.refresh_url == "https://example.com/oauth/refresh"

    def test_scopes_setter(self):
        """Test setting scopes."""
        flow = OAuthFlow()
        flow.scopes = {"admin": "Admin access"}
        assert flow.scopes == {"admin": "Admin access"}

    def test_scopes_default_empty_dict(self):
        """Test scopes returns empty dict when not set."""
        flow = OAuthFlow()
        assert flow.scopes == {}

    def test_setters_with_none(self):
        """Test setting properties to None removes them."""
        flow = OAuthFlow(
            {
                "authorizationUrl": "https://example.com/authorize",
                "tokenUrl": "https://example.com/token",
                "refreshUrl": "https://example.com/refresh",
                "scopes": {},
            }
        )

        flow.authorization_url = None
        assert "authorizationUrl" not in flow

        flow.token_url = None
        assert "tokenUrl" not in flow

        flow.refresh_url = None
        assert "refreshUrl" not in flow

        flow.scopes = None
        assert "scopes" not in flow

    def test_supports_extensions(self):
        """Test that OAuthFlow supports specification extensions."""
        flow = OAuthFlow(
            {"tokenUrl": "https://example.com/token", "scopes": {}, "x-custom": "value"}
        )
        extensions = flow.get_extensions()
        assert extensions == {"x-custom": "value"}

    def test_to_mapping(self):
        """Test converting to mapping."""
        flow = OAuthFlow(
            {
                "authorizationUrl": "https://example.com/authorize",
                "tokenUrl": "https://example.com/token",
                "scopes": {"read": "Read access"},
            }
        )
        result = flow.to_mapping()
        assert result == {
            "authorizationUrl": "https://example.com/authorize",
            "tokenUrl": "https://example.com/token",
            "scopes": {"read": "Read access"},
        }

    def test_from_mapping(self):
        """Test creating from mapping."""
        data = {"tokenUrl": "https://example.com/token", "scopes": {"write": "Write access"}}
        flow = OAuthFlow.from_mapping(data)
        assert flow.token_url == "https://example.com/token"
        assert flow.scopes == {"write": "Write access"}
