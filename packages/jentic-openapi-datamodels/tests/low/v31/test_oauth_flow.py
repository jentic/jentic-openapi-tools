"""Tests for OAuthFlow low-level datamodel."""

import textwrap

from ruamel.yaml import YAML

from jentic.apitools.openapi.datamodels.low.context import Context
from jentic.apitools.openapi.datamodels.low.sources import FieldSource, ValueSource
from jentic.apitools.openapi.datamodels.low.v31 import oauth_flow


def test_build_with_authorization_code_flow():
    """Test building OAuthFlow with authorizationCode flow fields."""
    yaml_content = textwrap.dedent(
        """
        authorizationUrl: https://example.com/oauth/authorize
        tokenUrl: https://example.com/oauth/token
        scopes:
          read:pets: Read your pets
          write:pets: Modify pets in your account
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = oauth_flow.build(root)
    assert isinstance(result, oauth_flow.OAuthFlow)

    assert result.root_node == root

    # Check authorizationUrl
    assert isinstance(result.authorization_url, FieldSource)
    assert result.authorization_url.value == "https://example.com/oauth/authorize"
    assert result.authorization_url.key_node is not None
    assert result.authorization_url.value_node is not None

    # Check tokenUrl
    assert isinstance(result.token_url, FieldSource)
    assert result.token_url.value == "https://example.com/oauth/token"

    # Check scopes
    assert isinstance(result.scopes, FieldSource)
    assert isinstance(result.scopes.value, dict)

    # Extract scopes from KeySource/ValueSource wrappers
    scopes_dict = {k.value: v.value for k, v in result.scopes.value.items()}
    assert scopes_dict["read:pets"] == "Read your pets"
    assert scopes_dict["write:pets"] == "Modify pets in your account"


def test_build_with_implicit_flow():
    """Test building OAuthFlow with implicit flow fields."""
    yaml_content = textwrap.dedent(
        """
        authorizationUrl: https://example.com/oauth/authorize
        scopes:
          openid: OpenID scope
          profile: Access profile information
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = oauth_flow.build(root)
    assert isinstance(result, oauth_flow.OAuthFlow)

    assert result.authorization_url is not None
    assert result.authorization_url.value == "https://example.com/oauth/authorize"
    assert result.token_url is None
    assert result.scopes is not None


def test_build_with_password_flow():
    """Test building OAuthFlow with password flow fields."""
    yaml_content = textwrap.dedent(
        """
        tokenUrl: https://example.com/oauth/token
        scopes:
          read: Read access
          write: Write access
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = oauth_flow.build(root)
    assert isinstance(result, oauth_flow.OAuthFlow)

    assert result.authorization_url is None
    assert result.token_url is not None
    assert result.token_url.value == "https://example.com/oauth/token"
    assert result.scopes is not None


def test_build_with_client_credentials_flow():
    """Test building OAuthFlow with clientCredentials flow fields."""
    yaml_content = textwrap.dedent(
        """
        tokenUrl: https://example.com/oauth/token
        scopes:
          admin: Admin access
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = oauth_flow.build(root)
    assert isinstance(result, oauth_flow.OAuthFlow)

    assert result.token_url is not None
    assert result.token_url.value == "https://example.com/oauth/token"
    assert result.scopes is not None


def test_build_with_refresh_url():
    """Test building OAuthFlow with refreshUrl field."""
    yaml_content = textwrap.dedent(
        """
        tokenUrl: https://example.com/oauth/token
        refreshUrl: https://example.com/oauth/refresh
        scopes:
          read: Read access
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = oauth_flow.build(root)
    assert isinstance(result, oauth_flow.OAuthFlow)

    assert result.token_url is not None
    assert result.token_url.value == "https://example.com/oauth/token"
    assert isinstance(result.refresh_url, FieldSource)
    assert result.refresh_url.value == "https://example.com/oauth/refresh"


def test_build_with_empty_scopes():
    """Test building OAuthFlow with empty scopes."""
    yaml_content = textwrap.dedent(
        """
        tokenUrl: https://example.com/oauth/token
        scopes: {}
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = oauth_flow.build(root)
    assert isinstance(result, oauth_flow.OAuthFlow)

    assert result.scopes is not None
    assert isinstance(result.scopes, FieldSource)
    assert result.scopes.value == {}


def test_build_with_extensions():
    """Test building OAuthFlow with specification extensions."""
    yaml_content = textwrap.dedent(
        """
        tokenUrl: https://example.com/oauth/token
        scopes:
          read: Read access
        x-custom-field: custom-value
        x-token-expiry: 3600
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = oauth_flow.build(root)
    assert isinstance(result, oauth_flow.OAuthFlow)

    assert result.extensions is not None
    assert len(result.extensions) == 2

    # Extract extension values
    extensions = {k.value: v.value for k, v in result.extensions.items()}
    assert extensions["x-custom-field"] == "custom-value"
    assert extensions["x-token-expiry"] == 3600


def test_build_preserves_invalid_types():
    """Test that build preserves values even with 'wrong' types (low-level model principle)."""
    yaml_content = textwrap.dedent(
        """
        authorizationUrl: 123
        tokenUrl: true
        refreshUrl: ['not', 'a', 'url']
        scopes: not-a-mapping
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = oauth_flow.build(root)
    assert isinstance(result, oauth_flow.OAuthFlow)

    assert result.authorization_url is not None
    assert result.token_url is not None
    assert result.refresh_url is not None
    assert result.scopes is not None

    # Should preserve the actual invalid values
    assert result.authorization_url.value == 123
    assert result.token_url.value is True
    assert result.refresh_url.value == ["not", "a", "url"]
    assert result.scopes.value == "not-a-mapping"


def test_build_with_invalid_node_returns_none():
    """Test that build returns ValueSource for non-mapping nodes (preserves invalid data)."""
    yaml_parser = YAML()

    # Scalar node
    scalar_root = yaml_parser.compose("just-a-string")
    result = oauth_flow.build(scalar_root)
    assert isinstance(result, ValueSource)
    assert result.value == "just-a-string"
    assert result.value_node == scalar_root

    # Sequence node
    sequence_root = yaml_parser.compose("['item1', 'item2']")
    result = oauth_flow.build(sequence_root)
    assert isinstance(result, ValueSource)
    assert result.value == ["item1", "item2"]
    assert result.value_node == sequence_root


def test_build_with_custom_context():
    """Test building OAuthFlow with a custom context."""
    yaml_content = textwrap.dedent(
        """
        tokenUrl: https://custom.example.com/token
        scopes:
          custom: Custom scope
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    custom_context = Context()
    result = oauth_flow.build(root, context=custom_context)
    assert isinstance(result, oauth_flow.OAuthFlow)

    assert result.token_url is not None
    assert result.token_url.value == "https://custom.example.com/token"


def test_source_tracking():
    """Test that source location information is preserved."""
    yaml_content = textwrap.dedent(
        """
        authorizationUrl: https://example.com/authorize
        tokenUrl: https://example.com/token
        scopes:
          read: Read access
          write: Write access
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = oauth_flow.build(root)
    assert isinstance(result, oauth_flow.OAuthFlow)

    assert result.authorization_url is not None
    assert result.token_url is not None
    assert result.scopes is not None

    # Check URL fields have source tracking
    assert result.authorization_url.key_node is not None
    assert result.authorization_url.value_node is not None
    assert result.token_url.key_node is not None
    assert result.token_url.value_node is not None

    # Check scopes have source tracking
    assert result.scopes.key_node is not None
    assert result.scopes.value_node is not None

    # Check individual scopes have source tracking
    for key, value in result.scopes.value.items():
        assert key.key_node is not None
        assert value.value_node is not None


def test_build_with_all_fields():
    """Test building OAuthFlow with all possible fields."""
    yaml_content = textwrap.dedent(
        """
        authorizationUrl: https://example.com/oauth/authorize
        tokenUrl: https://example.com/oauth/token
        refreshUrl: https://example.com/oauth/refresh
        scopes:
          read: Read access
          write: Write access
          admin: Admin access
        x-internal-id: flow-123
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = oauth_flow.build(root)
    assert isinstance(result, oauth_flow.OAuthFlow)

    assert result.authorization_url is not None
    assert result.token_url is not None
    assert result.refresh_url is not None
    assert result.scopes is not None
    assert result.extensions is not None

    # Verify all values
    assert result.authorization_url.value == "https://example.com/oauth/authorize"
    assert result.token_url.value == "https://example.com/oauth/token"
    assert result.refresh_url.value == "https://example.com/oauth/refresh"

    scopes_dict = {k.value: v.value for k, v in result.scopes.value.items()}
    assert len(scopes_dict) == 3

    extensions = {k.value: v.value for k, v in result.extensions.items()}
    assert extensions["x-internal-id"] == "flow-123"


def test_complex_scope_descriptions():
    """Test OAuthFlow with complex multi-line scope descriptions."""
    yaml_content = textwrap.dedent(
        """
        tokenUrl: https://example.com/token
        scopes:
          'https://www.googleapis.com/auth/drive': Access Google Drive
          'https://www.googleapis.com/auth/gmail.readonly': Read Gmail messages
          custom:scope:pattern: Custom scope with colons
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = oauth_flow.build(root)
    assert isinstance(result, oauth_flow.OAuthFlow)

    assert result.scopes is not None

    scopes_dict = {k.value: v.value for k, v in result.scopes.value.items()}
    assert "https://www.googleapis.com/auth/drive" in scopes_dict
    assert "https://www.googleapis.com/auth/gmail.readonly" in scopes_dict
    assert "custom:scope:pattern" in scopes_dict
