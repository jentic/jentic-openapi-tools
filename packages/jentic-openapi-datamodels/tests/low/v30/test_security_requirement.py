"""Tests for SecurityRequirement low-level datamodel."""

import textwrap

from ruamel.yaml import YAML

from jentic.apitools.openapi.datamodels.low.context import Context
from jentic.apitools.openapi.datamodels.low.sources import ValueSource
from jentic.apitools.openapi.datamodels.low.v30 import security_requirement


def test_build_with_single_scheme_empty_scopes():
    """Test building SecurityRequirement with a single scheme and empty scopes."""
    yaml_content = textwrap.dedent(
        """
        api_key: []
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = security_requirement.build(root)
    assert isinstance(result, security_requirement.SecurityRequirement)

    assert result.root_node == root
    assert isinstance(result.requirements, ValueSource)
    assert isinstance(result.requirements.value, dict)
    assert len(result.requirements.value) == 1

    # Extract the api_key entry
    api_key_entries = [(k.value, v.value) for k, v in result.requirements.value.items()]
    assert len(api_key_entries) == 1
    key, scopes = api_key_entries[0]
    assert key == "api_key"
    assert isinstance(scopes, list)
    assert len(scopes) == 0


def test_build_with_oauth2_scopes():
    """Test building SecurityRequirement with OAuth2 scopes."""
    yaml_content = textwrap.dedent(
        """
        petstore_auth:
          - write:pets
          - read:pets
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = security_requirement.build(root)
    assert isinstance(result, security_requirement.SecurityRequirement)

    assert isinstance(result.requirements, ValueSource)

    # Extract scopes
    requirements_dict = result.requirements.value
    petstore_auth_key = None
    for k in requirements_dict.keys():
        if k.value == "petstore_auth":
            petstore_auth_key = k
            break

    assert petstore_auth_key is not None
    scopes_value_source = requirements_dict[petstore_auth_key]
    assert isinstance(scopes_value_source, ValueSource)

    # Extract individual scope strings
    scopes = [scope.value for scope in scopes_value_source.value]
    assert scopes == ["write:pets", "read:pets"]


def test_build_with_multiple_schemes():
    """Test building SecurityRequirement with multiple security schemes."""
    yaml_content = textwrap.dedent(
        """
        oauth2:
          - read:data
          - write:data
        api_key: []
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = security_requirement.build(root)
    assert isinstance(result, security_requirement.SecurityRequirement)

    assert result.requirements is not None
    assert len(result.requirements.value) == 2

    # Convert to dict for easier testing
    requirements = {}
    for k, v in result.requirements.value.items():
        requirements[k.value] = [scope.value for scope in v.value]

    assert "oauth2" in requirements
    assert "api_key" in requirements
    assert requirements["oauth2"] == ["read:data", "write:data"]
    assert requirements["api_key"] == []


def test_build_with_empty_object():
    """Test building SecurityRequirement with empty object (optional security)."""
    yaml_content = textwrap.dedent(
        """
        {}
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = security_requirement.build(root)
    assert isinstance(result, security_requirement.SecurityRequirement)

    assert result.requirements is None


def test_build_preserves_invalid_types():
    """Test that build preserves values even with 'wrong' types (low-level model principle)."""
    yaml_content = textwrap.dedent(
        """
        api_key: not-an-array
        oauth2: 123
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = security_requirement.build(root)
    assert isinstance(result, security_requirement.SecurityRequirement)

    assert result.requirements is not None

    # Convert to dict for testing
    requirements = {}
    for k, v in result.requirements.value.items():
        requirements[k.value] = v.value

    # Should preserve the actual invalid values
    assert requirements["api_key"] == "not-an-array"
    assert requirements["oauth2"] == 123


def test_build_with_invalid_node_returns_none():
    """Test that build returns None for non-mapping nodes."""
    yaml_parser = YAML()

    # Scalar node
    scalar_root = yaml_parser.compose("just-a-string")
    assert security_requirement.build(scalar_root) is None

    # Sequence node
    sequence_root = yaml_parser.compose("['item1', 'item2']")
    assert security_requirement.build(sequence_root) is None


def test_build_with_custom_context():
    """Test building SecurityRequirement with a custom context."""
    yaml_content = textwrap.dedent(
        """
        custom_auth:
          - scope1
          - scope2
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    custom_context = Context()
    result = security_requirement.build(root, context=custom_context)
    assert isinstance(result, security_requirement.SecurityRequirement)

    assert result.requirements is not None

    # Extract scopes
    requirements = {}
    for k, v in result.requirements.value.items():
        requirements[k.value] = [scope.value for scope in v.value]

    assert requirements["custom_auth"] == ["scope1", "scope2"]


def test_source_tracking():
    """Test that source location information is preserved."""
    yaml_content = textwrap.dedent(
        """
        petstore_auth:
          - write:pets
          - read:pets
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = security_requirement.build(root)
    assert isinstance(result, security_requirement.SecurityRequirement)

    # Check that the entire requirements dict is wrapped
    assert isinstance(result.requirements, ValueSource)
    assert result.requirements.value_node is not None

    # Check that keys are wrapped
    for key in result.requirements.value.keys():
        assert key.key_node is not None
        assert key.value == "petstore_auth"

    # Check that scope arrays are wrapped
    for value in result.requirements.value.values():
        assert isinstance(value, ValueSource)
        assert value.value_node is not None

        # Check that individual scopes are wrapped
        for scope in value.value:
            assert isinstance(scope, ValueSource)
            assert scope.value_node is not None


def test_complex_oauth_scopes():
    """Test SecurityRequirement with complex OAuth scope patterns."""
    yaml_content = textwrap.dedent(
        """
        google_oauth:
          - https://www.googleapis.com/auth/userinfo.email
          - https://www.googleapis.com/auth/userinfo.profile
          - openid
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = security_requirement.build(root)
    assert isinstance(result, security_requirement.SecurityRequirement)

    assert result.requirements is not None

    # Extract scopes
    requirements = {}
    for k, v in result.requirements.value.items():
        requirements[k.value] = [scope.value for scope in v.value]

    assert len(requirements["google_oauth"]) == 3
    assert "https://www.googleapis.com/auth/userinfo.email" in requirements["google_oauth"]
    assert "openid" in requirements["google_oauth"]


def test_multiple_requirements_different_types():
    """Test SecurityRequirement with mixed auth types."""
    yaml_content = textwrap.dedent(
        """
        bearer_token: []
        oauth2:
          - read
          - write
        api_key: []
        basic_auth: []
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = security_requirement.build(root)
    assert isinstance(result, security_requirement.SecurityRequirement)

    assert result.requirements is not None
    assert len(result.requirements.value) == 4

    # Extract all requirements
    requirements = {}
    for k, v in result.requirements.value.items():
        requirements[k.value] = [scope.value for scope in v.value]

    # Check all schemes present
    assert "bearer_token" in requirements
    assert "oauth2" in requirements
    assert "api_key" in requirements
    assert "basic_auth" in requirements

    # Check scopes
    assert requirements["bearer_token"] == []
    assert requirements["oauth2"] == ["read", "write"]
    assert requirements["api_key"] == []
    assert requirements["basic_auth"] == []
