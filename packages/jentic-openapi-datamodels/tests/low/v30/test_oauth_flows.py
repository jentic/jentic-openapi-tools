"""Tests for OAuthFlows low-level datamodel."""

import textwrap

from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap

from jentic.apitools.openapi.datamodels.low.context import Context
from jentic.apitools.openapi.datamodels.low.sources import FieldSource, ValueSource
from jentic.apitools.openapi.datamodels.low.v30 import oauth_flows
from jentic.apitools.openapi.datamodels.low.v30.oauth_flow import OAuthFlow


def test_build_with_implicit_flow(parse_yaml):
    """Test building OAuthFlows with implicit flow configuration."""
    yaml_content = textwrap.dedent(
        """
        implicit:
          authorizationUrl: https://example.com/oauth/authorize
          scopes:
            read:pets: Read your pets
            write:pets: Modify pets in your account
        """
    )
    root = parse_yaml(yaml_content)

    result = oauth_flows.build(root)
    assert isinstance(result, oauth_flows.OAuthFlows)

    assert result.root_node == root

    # Check implicit flow
    assert isinstance(result.implicit, FieldSource)
    assert isinstance(result.implicit.value, OAuthFlow)
    assert result.implicit.key_node is not None
    assert result.implicit.value_node is not None

    # Check nested OAuthFlow properties
    assert result.implicit.value.authorization_url is not None
    assert result.implicit.value.authorization_url.value == "https://example.com/oauth/authorize"
    assert result.implicit.value.scopes is not None

    # Other flows should be None
    assert result.password is None
    assert result.client_credentials is None
    assert result.authorization_code is None


def test_build_with_password_flow(parse_yaml):
    """Test building OAuthFlows with password flow configuration."""
    yaml_content = textwrap.dedent(
        """
        password:
          tokenUrl: https://example.com/oauth/token
          scopes:
            read: Read access
            write: Write access
        """
    )
    root = parse_yaml(yaml_content)

    result = oauth_flows.build(root)
    assert isinstance(result, oauth_flows.OAuthFlows)

    assert isinstance(result.password, FieldSource)
    assert isinstance(result.password.value, OAuthFlow)
    assert result.password.value.token_url is not None
    assert result.password.value.token_url.value == "https://example.com/oauth/token"

    # Other flows should be None
    assert result.implicit is None
    assert result.client_credentials is None
    assert result.authorization_code is None


def test_build_with_client_credentials_flow(parse_yaml):
    """Test building OAuthFlows with clientCredentials flow configuration."""
    yaml_content = textwrap.dedent(
        """
        clientCredentials:
          tokenUrl: https://example.com/oauth/token
          scopes:
            admin: Admin access
        """
    )
    root = parse_yaml(yaml_content)

    result = oauth_flows.build(root)
    assert isinstance(result, oauth_flows.OAuthFlows)

    assert isinstance(result.client_credentials, FieldSource)
    assert isinstance(result.client_credentials.value, OAuthFlow)
    assert result.client_credentials.value.token_url is not None
    assert result.client_credentials.value.token_url.value == "https://example.com/oauth/token"

    # Other flows should be None
    assert result.implicit is None
    assert result.password is None
    assert result.authorization_code is None


def test_build_with_authorization_code_flow(parse_yaml):
    """Test building OAuthFlows with authorizationCode flow configuration."""
    yaml_content = textwrap.dedent(
        """
        authorizationCode:
          authorizationUrl: https://example.com/oauth/authorize
          tokenUrl: https://example.com/oauth/token
          scopes:
            read: Read access
            write: Write access
        """
    )
    root = parse_yaml(yaml_content)

    result = oauth_flows.build(root)
    assert isinstance(result, oauth_flows.OAuthFlows)

    assert isinstance(result.authorization_code, FieldSource)
    assert isinstance(result.authorization_code.value, OAuthFlow)
    assert result.authorization_code.value.authorization_url is not None
    assert result.authorization_code.value.token_url is not None
    assert (
        result.authorization_code.value.authorization_url.value
        == "https://example.com/oauth/authorize"
    )
    assert result.authorization_code.value.token_url.value == "https://example.com/oauth/token"

    # Other flows should be None
    assert result.implicit is None
    assert result.password is None
    assert result.client_credentials is None


def test_build_with_multiple_flows(parse_yaml):
    """Test building OAuthFlows with multiple flow configurations."""
    yaml_content = textwrap.dedent(
        """
        implicit:
          authorizationUrl: https://example.com/oauth/authorize
          scopes:
            openid: OpenID scope
        password:
          tokenUrl: https://example.com/oauth/token
          scopes:
            read: Read access
        authorizationCode:
          authorizationUrl: https://example.com/oauth/authorize
          tokenUrl: https://example.com/oauth/token
          scopes:
            full: Full access
        """
    )
    root = parse_yaml(yaml_content)

    result = oauth_flows.build(root)
    assert isinstance(result, oauth_flows.OAuthFlows)

    # Check all three flows are present
    assert result.implicit is not None
    assert result.password is not None
    assert result.authorization_code is not None
    assert result.client_credentials is None

    # Verify each flow is properly constructed
    assert isinstance(result.implicit.value, OAuthFlow)
    assert isinstance(result.password.value, OAuthFlow)
    assert isinstance(result.authorization_code.value, OAuthFlow)


def test_build_with_all_flows(parse_yaml):
    """Test building OAuthFlows with all four flow types."""
    yaml_content = textwrap.dedent(
        """
        implicit:
          authorizationUrl: https://example.com/oauth/authorize
          scopes: {}
        password:
          tokenUrl: https://example.com/oauth/token
          scopes: {}
        clientCredentials:
          tokenUrl: https://example.com/oauth/token
          scopes: {}
        authorizationCode:
          authorizationUrl: https://example.com/oauth/authorize
          tokenUrl: https://example.com/oauth/token
          scopes: {}
        """
    )
    root = parse_yaml(yaml_content)

    result = oauth_flows.build(root)
    assert isinstance(result, oauth_flows.OAuthFlows)

    assert result.implicit is not None
    assert result.password is not None
    assert result.client_credentials is not None
    assert result.authorization_code is not None

    # All should be OAuthFlow objects
    assert isinstance(result.implicit.value, OAuthFlow)
    assert isinstance(result.password.value, OAuthFlow)
    assert isinstance(result.client_credentials.value, OAuthFlow)
    assert isinstance(result.authorization_code.value, OAuthFlow)


def test_build_with_extensions(parse_yaml):
    """Test building OAuthFlows with specification extensions."""
    yaml_content = textwrap.dedent(
        """
        implicit:
          authorizationUrl: https://example.com/oauth/authorize
          scopes: {}
        x-custom-field: custom-value
        x-flow-metadata:
          version: "2.0"
          provider: example
        """
    )
    root = parse_yaml(yaml_content)

    result = oauth_flows.build(root)
    assert isinstance(result, oauth_flows.OAuthFlows)

    assert result.implicit is not None
    assert result.extensions is not None
    assert len(result.extensions) == 2

    # Extract extension values
    extensions = {k.value: v.value for k, v in result.extensions.items()}
    assert extensions["x-custom-field"] == "custom-value"
    # Type narrow to CommentedMap for nested access
    x_flow_metadata = extensions["x-flow-metadata"]
    assert isinstance(x_flow_metadata, CommentedMap)
    assert x_flow_metadata["version"] == "2.0"
    assert x_flow_metadata["provider"] == "example"


def test_build_with_empty_object(parse_yaml):
    """Test building OAuthFlows with empty object (no flows defined)."""
    yaml_content = textwrap.dedent(
        """
        {}
        """
    )
    root = parse_yaml(yaml_content)

    result = oauth_flows.build(root)
    assert isinstance(result, oauth_flows.OAuthFlows)

    assert result.implicit is None
    assert result.password is None
    assert result.client_credentials is None
    assert result.authorization_code is None
    assert result.extensions == {}


def test_build_with_invalid_node_returns_none():
    """Test that build returns ValueSource for non-mapping nodes (preserves invalid data)."""
    yaml_parser = YAML()

    # Scalar node
    scalar_root = yaml_parser.compose("just-a-string")
    result = oauth_flows.build(scalar_root)
    assert isinstance(result, ValueSource)
    assert result.value == "just-a-string"
    assert result.value_node == scalar_root

    # Sequence node
    sequence_root = yaml_parser.compose("['item1', 'item2']")
    result = oauth_flows.build(sequence_root)
    assert isinstance(result, ValueSource)
    assert result.value == ["item1", "item2"]
    assert result.value_node == sequence_root


def test_build_with_custom_context(parse_yaml):
    """Test building OAuthFlows with a custom context."""
    yaml_content = textwrap.dedent(
        """
        implicit:
          authorizationUrl: https://custom.example.com/authorize
          scopes:
            custom: Custom scope
        """
    )
    root = parse_yaml(yaml_content)

    custom_context = Context()
    result = oauth_flows.build(root, context=custom_context)
    assert isinstance(result, oauth_flows.OAuthFlows)

    assert result.implicit is not None
    assert result.implicit.value.authorization_url is not None
    assert result.implicit.value.authorization_url.value == "https://custom.example.com/authorize"


def test_source_tracking(parse_yaml):
    """Test that source location information is preserved."""
    yaml_content = textwrap.dedent(
        """
        implicit:
          authorizationUrl: https://example.com/authorize
          scopes: {}
        password:
          tokenUrl: https://example.com/token
          scopes: {}
        """
    )
    root = parse_yaml(yaml_content)

    result = oauth_flows.build(root)
    assert isinstance(result, oauth_flows.OAuthFlows)

    assert result.implicit is not None
    assert result.password is not None

    # Check implicit flow source tracking
    assert result.implicit.key_node is not None
    assert result.implicit.value_node is not None
    assert result.implicit.key_node.value == "implicit"

    # Check password flow source tracking
    assert result.password.key_node is not None
    assert result.password.value_node is not None
    assert result.password.key_node.value == "password"

    # Check nested OAuthFlow objects have source tracking
    assert result.implicit.value.root_node is not None
    assert result.password.value.root_node is not None


def test_build_with_complex_flows(parse_yaml):
    """Test building OAuthFlows with complex flow configurations including refreshUrl."""
    yaml_content = textwrap.dedent(
        """
        authorizationCode:
          authorizationUrl: https://example.com/oauth/authorize
          tokenUrl: https://example.com/oauth/token
          refreshUrl: https://example.com/oauth/refresh
          scopes:
            read:user: Read user information
            write:user: Modify user information
            admin: Administrative access
        password:
          tokenUrl: https://example.com/oauth/token
          refreshUrl: https://example.com/oauth/refresh
          scopes:
            read: Read access
            write: Write access
        x-oauth-provider: example-oauth
        """
    )
    root = parse_yaml(yaml_content)

    result = oauth_flows.build(root)
    assert isinstance(result, oauth_flows.OAuthFlows)

    assert result.authorization_code is not None
    assert result.password is not None

    # Check authorizationCode flow
    auth_code_flow = result.authorization_code.value
    assert auth_code_flow.authorization_url is not None
    assert auth_code_flow.token_url is not None
    assert auth_code_flow.refresh_url is not None
    assert auth_code_flow.scopes is not None
    assert auth_code_flow.authorization_url.value == "https://example.com/oauth/authorize"
    assert auth_code_flow.token_url.value == "https://example.com/oauth/token"
    assert auth_code_flow.refresh_url.value == "https://example.com/oauth/refresh"

    scopes_dict = {k.value: v.value for k, v in auth_code_flow.scopes.value.items()}
    assert len(scopes_dict) == 3
    assert scopes_dict["admin"] == "Administrative access"

    # Check password flow
    password_flow = result.password.value
    assert password_flow.token_url is not None
    assert password_flow.refresh_url is not None
    assert password_flow.token_url.value == "https://example.com/oauth/token"
    assert password_flow.refresh_url.value == "https://example.com/oauth/refresh"

    # Check extensions
    assert result.extensions is not None
    extensions = {k.value: v.value for k, v in result.extensions.items()}
    assert extensions["x-oauth-provider"] == "example-oauth"


def test_build_preserves_invalid_flow_data(parse_yaml):
    """Test that build preserves invalid flow data (low-level model principle)."""
    yaml_content = textwrap.dedent(
        """
        implicit: not-a-mapping
        password:
          tokenUrl: 123
          scopes: invalid
        """
    )
    root = parse_yaml(yaml_content)

    result = oauth_flows.build(root)
    assert isinstance(result, oauth_flows.OAuthFlows)

    # Invalid implicit flow should preserve the raw value (low-level model principle)
    assert result.implicit is not None
    assert result.implicit.value == "not-a-mapping"

    # Password flow should be built but with invalid internal data preserved
    assert result.password is not None
    assert result.password.value.token_url is not None
    assert result.password.value.scopes is not None
    assert result.password.value.token_url.value == 123
    assert result.password.value.scopes.value == "invalid"


def test_build_with_null_flow_values(parse_yaml):
    """Test that build preserves null values for flows (key without value)."""
    yaml_content = textwrap.dedent(
        """
        implicit:
        password:
        authorizationCode:
          authorizationUrl: https://example.com/authorize
          tokenUrl: https://example.com/token
          scopes: {}
        """
    )
    root = parse_yaml(yaml_content)

    result = oauth_flows.build(root)
    assert isinstance(result, oauth_flows.OAuthFlows)

    # Null values should be preserved (low-level model principle)
    assert result.implicit is not None
    assert result.implicit.value is None

    assert result.password is not None
    assert result.password.value is None

    # authorizationCode should be properly built
    assert result.authorization_code is not None
    assert isinstance(result.authorization_code.value, OAuthFlow)
    assert result.authorization_code.value.authorization_url is not None
    assert (
        result.authorization_code.value.authorization_url.value == "https://example.com/authorize"
    )
