"""Tests for SecurityScheme low-level datamodel."""

import textwrap

from ruamel.yaml import YAML

from jentic.apitools.openapi.datamodels.low.context import Context
from jentic.apitools.openapi.datamodels.low.sources import FieldSource, ValueSource
from jentic.apitools.openapi.datamodels.low.v30 import security_scheme
from jentic.apitools.openapi.datamodels.low.v30.oauth_flows import OAuthFlows


def test_build_with_api_key_in_header():
    """Test building SecurityScheme with apiKey type in header."""
    yaml_content = textwrap.dedent(
        """
        type: apiKey
        name: X-API-Key
        in: header
        description: API key authentication
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = security_scheme.build(root)
    assert isinstance(result, security_scheme.SecurityScheme)

    assert result.root_node == root

    # Check required fields for apiKey
    assert isinstance(result.type, FieldSource)
    assert result.name is not None
    assert result.in_ is not None
    assert result.description is not None
    assert result.type.value == "apiKey"
    assert result.name.value == "X-API-Key"
    assert result.in_.value == "header"
    assert result.description.value == "API key authentication"

    # Other type-specific fields should be None
    assert result.scheme is None
    assert result.flows is None
    assert result.openid_connect_url is None


def test_build_with_api_key_in_query():
    """Test building SecurityScheme with apiKey type in query parameter."""
    yaml_content = textwrap.dedent(
        """
        type: apiKey
        name: api_key
        in: query
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = security_scheme.build(root)
    assert isinstance(result, security_scheme.SecurityScheme)

    assert result.type is not None
    assert result.name is not None
    assert result.in_ is not None
    assert result.type.value == "apiKey"
    assert result.name.value == "api_key"
    assert result.in_.value == "query"


def test_build_with_api_key_in_cookie():
    """Test building SecurityScheme with apiKey type in cookie."""
    yaml_content = textwrap.dedent(
        """
        type: apiKey
        name: session_token
        in: cookie
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = security_scheme.build(root)
    assert isinstance(result, security_scheme.SecurityScheme)

    assert result.type is not None
    assert result.name is not None
    assert result.in_ is not None
    assert result.type.value == "apiKey"
    assert result.name.value == "session_token"
    assert result.in_.value == "cookie"


def test_build_with_http_basic():
    """Test building SecurityScheme with HTTP Basic authentication."""
    yaml_content = textwrap.dedent(
        """
        type: http
        scheme: basic
        description: HTTP Basic Authentication
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = security_scheme.build(root)
    assert isinstance(result, security_scheme.SecurityScheme)

    assert result.type is not None
    assert result.scheme is not None
    assert result.description is not None
    assert result.type.value == "http"
    assert result.scheme.value == "basic"
    assert result.description.value == "HTTP Basic Authentication"

    # Other fields should be None
    assert result.name is None
    assert result.in_ is None
    assert result.bearer_format is None
    assert result.flows is None
    assert result.openid_connect_url is None


def test_build_with_http_bearer():
    """Test building SecurityScheme with HTTP Bearer token authentication."""
    yaml_content = textwrap.dedent(
        """
        type: http
        scheme: bearer
        bearerFormat: JWT
        description: Bearer token authentication with JWT
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = security_scheme.build(root)
    assert isinstance(result, security_scheme.SecurityScheme)

    assert result.type is not None
    assert result.scheme is not None
    assert result.bearer_format is not None
    assert result.description is not None
    assert result.type.value == "http"
    assert result.scheme.value == "bearer"
    assert result.bearer_format.value == "JWT"
    assert result.description.value == "Bearer token authentication with JWT"


def test_build_with_oauth2():
    """Test building SecurityScheme with OAuth2."""
    yaml_content = textwrap.dedent(
        """
        type: oauth2
        description: OAuth2 authentication
        flows:
          implicit:
            authorizationUrl: https://example.com/oauth/authorize
            scopes:
              read:pets: Read your pets
              write:pets: Modify pets in your account
          authorizationCode:
            authorizationUrl: https://example.com/oauth/authorize
            tokenUrl: https://example.com/oauth/token
            scopes:
              read:pets: Read your pets
              write:pets: Modify pets in your account
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = security_scheme.build(root)
    assert isinstance(result, security_scheme.SecurityScheme)

    assert result.type is not None
    assert result.description is not None
    assert result.type.value == "oauth2"
    assert result.description.value == "OAuth2 authentication"

    # Check flows object
    assert isinstance(result.flows, FieldSource)
    assert isinstance(result.flows.value, OAuthFlows)
    assert result.flows.value.implicit is not None
    assert result.flows.value.authorization_code is not None

    # Other fields should be None
    assert result.name is None
    assert result.in_ is None
    assert result.scheme is None
    assert result.openid_connect_url is None


def test_build_with_openid_connect():
    """Test building SecurityScheme with OpenID Connect."""
    yaml_content = textwrap.dedent(
        """
        type: openIdConnect
        openIdConnectUrl: https://example.com/.well-known/openid-configuration
        description: OpenID Connect authentication
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = security_scheme.build(root)
    assert isinstance(result, security_scheme.SecurityScheme)

    assert result.type is not None
    assert result.openid_connect_url is not None
    assert result.description is not None
    assert result.type.value == "openIdConnect"
    assert result.openid_connect_url.value == "https://example.com/.well-known/openid-configuration"
    assert result.description.value == "OpenID Connect authentication"

    # Other fields should be None
    assert result.name is None
    assert result.in_ is None
    assert result.scheme is None
    assert result.flows is None


def test_build_with_extensions():
    """Test building SecurityScheme with specification extensions."""
    yaml_content = textwrap.dedent(
        """
        type: http
        scheme: bearer
        x-custom-field: custom-value
        x-token-lifetime: 3600
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = security_scheme.build(root)
    assert isinstance(result, security_scheme.SecurityScheme)

    assert result.extensions is not None
    assert len(result.extensions) == 2

    # Extract extension values
    extensions = {k.value: v.value for k, v in result.extensions.items()}
    assert extensions["x-custom-field"] == "custom-value"
    assert extensions["x-token-lifetime"] == 3600


def test_build_preserves_invalid_types():
    """Test that build preserves values even with 'wrong' types (low-level model principle)."""
    yaml_content = textwrap.dedent(
        """
        type: 123
        name: true
        in: ['not', 'a', 'string']
        scheme: null
        flows: not-a-mapping
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = security_scheme.build(root)
    assert isinstance(result, security_scheme.SecurityScheme)

    assert result.type is not None
    assert result.name is not None
    assert result.in_ is not None
    assert result.scheme is not None
    assert result.flows is not None

    # Should preserve the actual invalid values
    assert result.type.value == 123
    assert result.name.value is True
    assert result.in_.value == ["not", "a", "string"]
    assert result.scheme.value is None
    assert result.flows.value == "not-a-mapping"


def test_build_with_invalid_node_returns_none():
    """Test that build returns ValueSource for non-mapping nodes (preserves invalid data)."""
    yaml_parser = YAML()

    # Scalar node
    scalar_root = yaml_parser.compose("just-a-string")
    result = security_scheme.build(scalar_root)
    assert isinstance(result, ValueSource)
    assert result.value == "just-a-string"
    assert result.value_node == scalar_root

    # Sequence node
    sequence_root = yaml_parser.compose("['item1', 'item2']")
    result = security_scheme.build(sequence_root)
    assert isinstance(result, ValueSource)
    assert result.value == ["item1", "item2"]
    assert result.value_node == sequence_root


def test_build_with_custom_context():
    """Test building SecurityScheme with a custom context."""
    yaml_content = textwrap.dedent(
        """
        type: apiKey
        name: custom_key
        in: header
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    custom_context = Context()
    result = security_scheme.build(root, context=custom_context)
    assert isinstance(result, security_scheme.SecurityScheme)

    assert result.type is not None
    assert result.name is not None
    assert result.type.value == "apiKey"
    assert result.name.value == "custom_key"


def test_source_tracking():
    """Test that source location information is preserved."""
    yaml_content = textwrap.dedent(
        """
        type: http
        scheme: bearer
        bearerFormat: JWT
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = security_scheme.build(root)
    assert isinstance(result, security_scheme.SecurityScheme)

    assert result.type is not None
    assert result.scheme is not None
    assert result.bearer_format is not None

    # Check that key_node and value_node are tracked
    assert result.type.key_node is not None
    assert result.type.value_node is not None
    assert result.scheme.key_node is not None
    assert result.scheme.value_node is not None
    assert result.bearer_format.key_node is not None
    assert result.bearer_format.value_node is not None

    # Verify key_node contains correct field name
    assert result.type.key_node.value == "type"
    assert result.scheme.key_node.value == "scheme"


def test_build_with_null_flows():
    """Test building SecurityScheme with null flows value."""
    yaml_content = textwrap.dedent(
        """
        type: oauth2
        flows:
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = security_scheme.build(root)
    assert isinstance(result, security_scheme.SecurityScheme)

    assert result.type is not None
    assert result.type.value == "oauth2"
    assert result.flows is not None
    assert result.flows.value is None


def test_build_with_valid_oauth2_flows():
    """Test building SecurityScheme with complete OAuth2 flows."""
    yaml_content = textwrap.dedent(
        """
        type: oauth2
        flows:
          implicit:
            authorizationUrl: https://example.com/oauth/authorize
            scopes:
              read: Read access
          password:
            tokenUrl: https://example.com/oauth/token
            scopes:
              write: Write access
          clientCredentials:
            tokenUrl: https://example.com/oauth/token
            scopes:
              admin: Admin access
          authorizationCode:
            authorizationUrl: https://example.com/oauth/authorize
            tokenUrl: https://example.com/oauth/token
            scopes:
              full: Full access
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = security_scheme.build(root)
    assert isinstance(result, security_scheme.SecurityScheme)

    assert result.type is not None
    assert result.flows is not None
    assert result.type.value == "oauth2"
    assert isinstance(result.flows.value, OAuthFlows)

    # Verify all flows are present
    flows = result.flows.value
    assert flows.implicit is not None
    assert flows.password is not None
    assert flows.client_credentials is not None
    assert flows.authorization_code is not None


def test_build_with_markdown_description():
    """Test building SecurityScheme with CommonMark description."""
    yaml_content = textwrap.dedent(
        """
        type: http
        scheme: bearer
        description: |
          # Bearer Authentication

          Use a JWT token in the Authorization header:

          ```
          Authorization: Bearer <token>
          ```
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = security_scheme.build(root)
    assert isinstance(result, security_scheme.SecurityScheme)

    assert result.description is not None
    assert "# Bearer Authentication" in result.description.value
    assert "Authorization: Bearer <token>" in result.description.value


def test_build_with_minimal_fields():
    """Test building SecurityScheme with only required type field."""
    yaml_content = textwrap.dedent(
        """
        type: http
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = security_scheme.build(root)
    assert isinstance(result, security_scheme.SecurityScheme)

    assert result.type is not None
    assert result.type.value == "http"
    assert result.description is None
    assert result.scheme is None


def test_build_with_empty_object():
    """Test building SecurityScheme with empty object."""
    yaml_content = textwrap.dedent(
        """
        {}
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = security_scheme.build(root)
    assert isinstance(result, security_scheme.SecurityScheme)

    # All fields should be None
    assert result.type is None
    assert result.description is None
    assert result.name is None
    assert result.in_ is None
    assert result.scheme is None
    assert result.bearer_format is None
    assert result.flows is None
    assert result.openid_connect_url is None


def test_build_with_all_security_types():
    """Test that we can build all four security scheme types correctly."""
    # API Key
    api_key_yaml = "type: apiKey\nname: api_key\nin: header"
    yaml_parser = YAML()
    api_key_result = security_scheme.build(yaml_parser.compose(api_key_yaml))
    assert isinstance(api_key_result, security_scheme.SecurityScheme)
    assert api_key_result.type is not None
    assert api_key_result.type.value == "apiKey"

    # HTTP
    http_yaml = "type: http\nscheme: basic"
    http_result = security_scheme.build(yaml_parser.compose(http_yaml))
    assert isinstance(http_result, security_scheme.SecurityScheme)
    assert http_result.type is not None
    assert http_result.type.value == "http"

    # OAuth2
    oauth2_yaml = "type: oauth2\nflows:\n  implicit:\n    authorizationUrl: https://example.com\n    scopes: {}"
    oauth2_result = security_scheme.build(yaml_parser.compose(oauth2_yaml))
    assert isinstance(oauth2_result, security_scheme.SecurityScheme)
    assert oauth2_result.type is not None
    assert oauth2_result.type.value == "oauth2"

    # OpenID Connect
    oidc_yaml = "type: openIdConnect\nopenIdConnectUrl: https://example.com/.well-known/openid-configuration"
    oidc_result = security_scheme.build(yaml_parser.compose(oidc_yaml))
    assert isinstance(oidc_result, security_scheme.SecurityScheme)
    assert oidc_result.type is not None
    assert oidc_result.type.value == "openIdConnect"
