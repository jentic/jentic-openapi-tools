"""Tests for Server low-level datamodel."""

import textwrap

from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap

from jentic.apitools.openapi.datamodels.low.context import Context
from jentic.apitools.openapi.datamodels.low.sources import FieldSource, KeySource, ValueSource
from jentic.apitools.openapi.datamodels.low.v30 import server
from jentic.apitools.openapi.datamodels.low.v30.server_variable import ServerVariable


def test_build_with_url_only():
    """Test building Server with only required url field."""
    yaml_content = textwrap.dedent(
        """
        url: https://api.example.com/v1
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = server.build(root)
    assert isinstance(result, server.Server)

    assert result.root_node == root
    assert isinstance(result.url, FieldSource)
    assert result.url.value == "https://api.example.com/v1"
    assert result.url.key_node is not None
    assert result.url.value_node is not None

    # Optional fields should be None
    assert result.description is None
    assert result.variables is None
    assert result.extensions == {}


def test_build_with_url_and_description():
    """Test building Server with url and description."""
    yaml_content = textwrap.dedent(
        """
        url: https://api.example.com
        description: Production API server
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = server.build(root)
    assert isinstance(result, server.Server)

    assert isinstance(result.url, FieldSource)
    assert result.url.value == "https://api.example.com"

    assert isinstance(result.description, FieldSource)
    assert result.description.value == "Production API server"

    assert result.variables is None


def test_build_with_relative_url():
    """Test building Server with relative URL."""
    yaml_content = textwrap.dedent(
        """
        url: /api/v1
        description: Relative URL to API
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = server.build(root)
    assert isinstance(result, server.Server)

    assert isinstance(result.url, FieldSource)
    assert result.url.value == "/api/v1"
    assert isinstance(result.description, FieldSource)
    assert result.description.value == "Relative URL to API"


def test_build_with_url_variables():
    """Test building Server with URL containing variables."""
    yaml_content = textwrap.dedent(
        """
        url: https://{environment}.example.com/api/{version}
        description: API server with environment and version variables
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = server.build(root)
    assert isinstance(result, server.Server)

    assert isinstance(result.url, FieldSource)
    assert result.url.value == "https://{environment}.example.com/api/{version}"
    assert "{environment}" in result.url.value
    assert "{version}" in result.url.value


def test_build_with_single_variable():
    """Test building Server with a single server variable."""
    yaml_content = textwrap.dedent(
        """
        url: https://{environment}.example.com/api
        description: API with environment variable
        variables:
          environment:
            default: production
            description: The deployment environment
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = server.build(root)
    assert isinstance(result, server.Server)

    assert isinstance(result.url, FieldSource)
    assert result.url.value == "https://{environment}.example.com/api"
    assert result.variables is not None
    assert isinstance(result.variables, FieldSource)
    assert isinstance(result.variables.value, dict)
    assert len(result.variables.value) == 1

    # Check the variable
    var_keys = list(result.variables.value.keys())
    assert len(var_keys) == 1
    assert isinstance(var_keys[0], KeySource)
    assert var_keys[0].value == "environment"

    var_value = result.variables.value[var_keys[0]]
    assert isinstance(var_value, ValueSource)
    assert isinstance(var_value.value, ServerVariable)
    assert var_value.value.default is not None
    assert var_value.value.default.value == "production"
    assert var_value.value.description is not None
    assert var_value.value.description.value == "The deployment environment"


def test_build_with_multiple_variables():
    """Test building Server with multiple server variables."""
    yaml_content = textwrap.dedent(
        """
        url: https://{environment}.example.com:{port}/api/{version}
        variables:
          environment:
            default: production
            enum:
              - production
              - staging
              - development
          port:
            default: "8443"
          version:
            default: v1
            enum:
              - v1
              - v2
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = server.build(root)
    assert isinstance(result, server.Server)

    assert result.variables is not None
    assert len(result.variables.value) == 3

    # Extract variable names
    var_names = {k.value for k in result.variables.value.keys()}
    assert var_names == {"environment", "port", "version"}

    # Check environment variable
    env_key = next(k for k in result.variables.value.keys() if k.value == "environment")
    env_var = result.variables.value[env_key].value
    assert isinstance(env_var, ServerVariable)
    assert env_var.default is not None
    assert env_var.default.value == "production"
    assert env_var.enum is not None
    assert len(env_var.enum.value) == 3

    # Check port variable
    port_key = next(k for k in result.variables.value.keys() if k.value == "port")
    port_var = result.variables.value[port_key].value
    assert isinstance(port_var, ServerVariable)
    assert port_var.default is not None
    assert port_var.default.value == "8443"


def test_build_with_all_fields():
    """Test building Server with all fields including extensions."""
    yaml_content = textwrap.dedent(
        """
        url: https://{environment}.example.com/api/v1
        description: Production API server with variable substitution
        variables:
          environment:
            default: production
            enum:
              - production
              - staging
            description: Deployment environment
        x-internal-id: server-001
        x-region: us-east-1
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = server.build(root)
    assert isinstance(result, server.Server)

    assert isinstance(result.url, FieldSource)
    assert result.url.value == "https://{environment}.example.com/api/v1"
    assert isinstance(result.description, FieldSource)
    assert result.description.value == "Production API server with variable substitution"
    assert result.variables is not None
    assert len(result.variables.value) == 1

    # Check extensions
    assert len(result.extensions) == 2
    ext_dict = {k.value: v.value for k, v in result.extensions.items()}
    assert ext_dict["x-internal-id"] == "server-001"
    assert ext_dict["x-region"] == "us-east-1"


def test_build_with_commonmark_description():
    """Test that Server description can contain CommonMark formatted text."""
    yaml_content = textwrap.dedent(
        """
        url: https://api.example.com
        description: |
          # Production API

          This server hosts the **production** environment.

          - High availability
          - Load balanced
          - Monitored 24/7
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = server.build(root)
    assert isinstance(result, server.Server)

    assert result.description is not None
    assert "# Production API" in result.description.value
    assert "**production**" in result.description.value
    assert "- High availability" in result.description.value


def test_build_with_empty_object():
    """Test building Server from empty YAML object."""
    yaml_content = "{}"
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = server.build(root)
    assert isinstance(result, server.Server)

    assert result.root_node == root
    assert result.url is None
    assert result.description is None
    assert result.variables is None
    assert result.extensions == {}


def test_build_with_invalid_node_returns_value_source():
    """Test that build returns ValueSource for non-mapping nodes."""
    yaml_parser = YAML()

    # Scalar node
    scalar_root = yaml_parser.compose("https://api.example.com")
    result = server.build(scalar_root)
    assert isinstance(result, ValueSource)
    assert result.value == "https://api.example.com"
    assert result.value_node == scalar_root

    # Sequence node
    sequence_root = yaml_parser.compose("['url1', 'url2']")
    result = server.build(sequence_root)
    assert isinstance(result, ValueSource)
    assert result.value == ["url1", "url2"]
    assert result.value_node == sequence_root


def test_build_preserves_invalid_types():
    """Test that build preserves values even with 'wrong' types."""
    yaml_content = textwrap.dedent(
        """
        url: 12345
        description: true
        variables: not-a-mapping
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = server.build(root)
    assert isinstance(result, server.Server)

    # Should preserve the actual values, not convert them
    assert result.url is not None
    assert result.url.value == 12345

    assert result.description is not None
    assert result.description.value is True

    assert result.variables is not None
    assert result.variables.value == "not-a-mapping"


def test_build_with_invalid_variable_data():
    """Test that invalid variable data is preserved."""
    yaml_content = textwrap.dedent(
        """
        url: https://api.example.com
        variables:
          env: invalid-string-not-object
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = server.build(root)
    assert isinstance(result, server.Server)

    assert result.variables is not None
    assert len(result.variables.value) == 1

    var_keys = list(result.variables.value.keys())
    assert var_keys[0].value == "env"
    # The invalid data should be preserved - child builder returns ValueSource for invalid data
    var_value = result.variables.value[var_keys[0]]
    assert isinstance(var_value, ValueSource)
    assert isinstance(var_value.value, ValueSource)
    assert var_value.value.value == "invalid-string-not-object"


def test_build_with_custom_context():
    """Test building Server with a custom context."""
    yaml_content = textwrap.dedent(
        """
        url: https://custom.example.com
        description: Custom context server
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    custom_context = Context()
    result = server.build(root, context=custom_context)
    assert isinstance(result, server.Server)

    assert isinstance(result.url, FieldSource)
    assert result.url.value == "https://custom.example.com"
    assert isinstance(result.description, FieldSource)
    assert result.description.value == "Custom context server"


def test_source_tracking():
    """Test that source location information is preserved."""
    yaml_content = textwrap.dedent(
        """
        url: https://api.example.com
        description: Tracked server
        variables:
          env:
            default: prod
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = server.build(root)
    assert isinstance(result, server.Server)

    # Check url source tracking
    assert isinstance(result.url, FieldSource)
    assert result.url.key_node is not None
    assert result.url.value_node is not None
    assert result.url.key_node.value == "url"
    assert result.url.value_node.value == "https://api.example.com"

    # Check description source tracking
    assert isinstance(result.description, FieldSource)
    assert result.description.key_node is not None
    assert result.description.value_node is not None
    assert result.description.key_node.value == "description"

    # Check variables source tracking
    assert isinstance(result.variables, FieldSource)
    assert result.variables.key_node is not None
    assert result.variables.value_node is not None
    assert result.variables.key_node.value == "variables"

    # Check line numbers are available
    assert hasattr(result.url.key_node.start_mark, "line")
    assert hasattr(result.url.value_node.start_mark, "line")


def test_build_with_null_values():
    """Test that build preserves null values."""
    yaml_content = textwrap.dedent(
        """
        url: https://api.example.com
        description:
        variables:
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = server.build(root)
    assert isinstance(result, server.Server)

    assert result.url is not None
    assert result.description is not None
    assert result.description.value is None

    assert result.variables is not None
    assert result.variables.value is None


def test_build_with_complex_extensions():
    """Test building Server with complex extension objects."""
    yaml_content = textwrap.dedent(
        """
        url: https://api.example.com
        x-load-balancer:
          type: round-robin
          health-check: /health
        x-rate-limit:
          requests: 1000
          window: 60
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = server.build(root)
    assert isinstance(result, server.Server)

    assert len(result.extensions) == 2
    ext_dict = {k.value: v.value for k, v in result.extensions.items()}

    # Check x-load-balancer extension
    load_balancer = ext_dict["x-load-balancer"]
    assert isinstance(load_balancer, CommentedMap)
    assert load_balancer["type"] == "round-robin"
    assert load_balancer["health-check"] == "/health"

    # Check x-rate-limit extension
    rate_limit = ext_dict["x-rate-limit"]
    assert isinstance(rate_limit, CommentedMap)
    assert rate_limit["requests"] == 1000
    assert rate_limit["window"] == 60


def test_build_real_world_example():
    """Test a complete real-world Server object."""
    yaml_content = textwrap.dedent(
        """
        url: https://{username}.gigantic-server.com:{port}/{basePath}
        description: The production API server
        variables:
          username:
            default: demo
            description: this value is assigned by the service provider, in this example `gigantic-server.com`
          port:
            enum:
              - '8443'
              - '443'
            default: '8443'
          basePath:
            default: v2
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = server.build(root)
    assert isinstance(result, server.Server)

    assert isinstance(result.url, FieldSource)
    assert result.url.value == "https://{username}.gigantic-server.com:{port}/{basePath}"
    assert isinstance(result.description, FieldSource)
    assert result.description.value == "The production API server"

    assert result.variables is not None
    assert len(result.variables.value) == 3

    var_names = {k.value for k in result.variables.value.keys()}
    assert var_names == {"username", "port", "basePath"}

    # Check username variable
    username_key = next(k for k in result.variables.value.keys() if k.value == "username")
    username_var = result.variables.value[username_key].value
    assert isinstance(username_var, ServerVariable)
    assert username_var.default is not None
    assert username_var.default.value == "demo"
    assert username_var.description is not None
    assert "gigantic-server.com" in username_var.description.value

    # Check port variable with enum
    port_key = next(k for k in result.variables.value.keys() if k.value == "port")
    port_var = result.variables.value[port_key].value
    assert isinstance(port_var, ServerVariable)
    assert port_var.default is not None
    assert port_var.default.value == "8443"
    assert port_var.enum is not None
    assert len(port_var.enum.value) == 2
    port_enum_values = [v.value for v in port_var.enum.value]
    assert port_enum_values == ["8443", "443"]


def test_variable_source_tracking():
    """Test that variables maintain proper source tracking."""
    yaml_content = textwrap.dedent(
        """
        url: https://api.example.com
        variables:
          env:
            default: production
          region:
            default: us-east-1
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = server.build(root)
    assert isinstance(result, server.Server)

    assert result.variables is not None

    # Check that each variable key has source tracking
    for var_key, var_value in result.variables.value.items():
        assert isinstance(var_key, KeySource)
        assert var_key.key_node is not None
        assert isinstance(var_value, ValueSource)
        assert var_value.value_node is not None

        # Check that the ServerVariable itself has proper root_node
        if isinstance(var_value.value, ServerVariable):
            assert var_value.value.root_node is not None
