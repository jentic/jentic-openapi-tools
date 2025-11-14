"""Tests for Link low-level datamodel."""

import textwrap

from ruamel.yaml import YAML

from jentic.apitools.openapi.datamodels.low.context import Context
from jentic.apitools.openapi.datamodels.low.sources import FieldSource, ValueSource
from jentic.apitools.openapi.datamodels.low.v30 import link
from jentic.apitools.openapi.datamodels.low.v30.server import Server


def test_build_with_operation_ref_only():
    """Test building Link with only operationRef field."""
    yaml_content = textwrap.dedent(
        """
        operationRef: '#/paths/~12.0~1repositories~1{username}/get'
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = link.build(root)
    assert isinstance(result, link.Link)

    assert result.root_node == root
    assert isinstance(result.operation_ref, FieldSource)
    assert result.operation_ref.value == "#/paths/~12.0~1repositories~1{username}/get"

    # Optional fields should be None
    assert result.operation_id is None
    assert result.parameters is None
    assert result.request_body is None
    assert result.description is None
    assert result.server is None
    assert result.extensions == {}


def test_build_with_operation_id_only():
    """Test building Link with only operationId field."""
    yaml_content = textwrap.dedent(
        """
        operationId: getUserById
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = link.build(root)
    assert isinstance(result, link.Link)

    assert isinstance(result.operation_id, FieldSource)
    assert result.operation_id.value == "getUserById"

    assert result.operation_ref is None
    assert result.parameters is None


def test_build_with_parameters():
    """Test building Link with parameters map."""
    yaml_content = textwrap.dedent(
        """
        operationId: getUserById
        parameters:
          userId: $response.body#/id
          format: json
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = link.build(root)
    assert isinstance(result, link.Link)

    assert isinstance(result.operation_id, FieldSource)
    assert result.operation_id.value == "getUserById"

    assert isinstance(result.parameters, FieldSource)
    assert isinstance(result.parameters.value, dict)
    assert len(result.parameters.value) == 2

    # Check parameter keys and values
    params = {k.value: v.value for k, v in result.parameters.value.items()}
    assert params["userId"] == "$response.body#/id"
    assert params["format"] == "json"


def test_build_with_request_body():
    """Test building Link with requestBody field."""
    yaml_content = textwrap.dedent(
        """
        operationId: createUser
        requestBody:
          name: $response.body#/name
          email: $response.body#/email
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = link.build(root)
    assert isinstance(result, link.Link)

    assert isinstance(result.request_body, FieldSource)
    assert isinstance(result.request_body.value, dict)
    assert result.request_body.value["name"] == "$response.body#/name"
    assert result.request_body.value["email"] == "$response.body#/email"


def test_build_with_description():
    """Test building Link with description field."""
    yaml_content = textwrap.dedent(
        """
        operationId: getUserById
        description: Get the user details by their ID
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = link.build(root)
    assert isinstance(result, link.Link)

    assert isinstance(result.description, FieldSource)
    assert result.description.value == "Get the user details by their ID"


def test_build_with_server():
    """Test building Link with nested Server object."""
    yaml_content = textwrap.dedent(
        """
        operationId: getUserById
        server:
          url: https://api.example.com/v2
          description: Version 2 API server
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = link.build(root)
    assert isinstance(result, link.Link)

    assert isinstance(result.server, FieldSource)
    assert isinstance(result.server.value, Server)
    assert isinstance(result.server.value.url, FieldSource)
    assert result.server.value.url.value == "https://api.example.com/v2"
    assert isinstance(result.server.value.description, FieldSource)
    assert result.server.value.description.value == "Version 2 API server"


def test_build_with_all_fields():
    """Test building Link with all fields including extensions."""
    yaml_content = textwrap.dedent(
        """
        operationRef: '#/paths/~1users~1{userId}/get'
        description: Link to user details
        parameters:
          userId: $response.body#/id
        server:
          url: https://api.example.com
        x-link-type: user-details
        x-internal-id: link-001
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = link.build(root)
    assert isinstance(result, link.Link)

    assert isinstance(result.operation_ref, FieldSource)
    assert result.operation_ref.value == "#/paths/~1users~1{userId}/get"
    assert isinstance(result.description, FieldSource)
    assert result.description.value == "Link to user details"
    assert isinstance(result.parameters, FieldSource)
    assert len(result.parameters.value) == 1
    assert isinstance(result.server, FieldSource)
    assert isinstance(result.server.value, Server)

    # Check extensions
    assert len(result.extensions) == 2
    ext_dict = {k.value: v.value for k, v in result.extensions.items()}
    assert ext_dict["x-link-type"] == "user-details"
    assert ext_dict["x-internal-id"] == "link-001"


def test_build_with_commonmark_description():
    """Test that Link description can contain CommonMark formatted text."""
    yaml_content = textwrap.dedent(
        """
        operationId: getUserById
        description: |
          # User Details Link

          This link retrieves the **full user profile** including:
          - Personal information
          - Contact details
          - Preferences
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = link.build(root)
    assert isinstance(result, link.Link)

    assert isinstance(result.description, FieldSource)
    assert "# User Details Link" in result.description.value
    assert "**full user profile**" in result.description.value
    assert "- Personal information" in result.description.value


def test_build_with_empty_object():
    """Test building Link from empty YAML object."""
    yaml_content = "{}"
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = link.build(root)
    assert isinstance(result, link.Link)

    assert result.root_node == root
    assert result.operation_ref is None
    assert result.operation_id is None
    assert result.parameters is None
    assert result.request_body is None
    assert result.description is None
    assert result.server is None
    assert result.extensions == {}


def test_build_with_invalid_node_returns_value_source():
    """Test that build returns ValueSource for non-mapping nodes."""
    yaml_parser = YAML()

    # Scalar node
    scalar_root = yaml_parser.compose("just-a-string")
    result = link.build(scalar_root)
    assert isinstance(result, ValueSource)
    assert result.value == "just-a-string"
    assert result.value_node == scalar_root

    # Sequence node
    sequence_root = yaml_parser.compose("['item1', 'item2']")
    result = link.build(sequence_root)
    assert isinstance(result, ValueSource)
    assert result.value == ["item1", "item2"]
    assert result.value_node == sequence_root


def test_build_preserves_invalid_types():
    """Test that build preserves values even with 'wrong' types."""
    yaml_content = textwrap.dedent(
        """
        operationRef: 12345
        operationId: true
        parameters: not-a-map
        description: 999
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = link.build(root)
    assert isinstance(result, link.Link)

    # Should preserve the actual values, not convert them
    assert isinstance(result.operation_ref, FieldSource)
    assert result.operation_ref.value == 12345

    assert isinstance(result.operation_id, FieldSource)
    assert result.operation_id.value is True

    assert isinstance(result.parameters, FieldSource)
    assert result.parameters.value == "not-a-map"

    assert isinstance(result.description, FieldSource)
    assert result.description.value == 999


def test_build_with_custom_context():
    """Test building Link with a custom context."""
    yaml_content = textwrap.dedent(
        """
        operationId: customOperation
        description: Custom context link
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    custom_context = Context()
    result = link.build(root, context=custom_context)
    assert isinstance(result, link.Link)

    assert isinstance(result.operation_id, FieldSource)
    assert result.operation_id.value == "customOperation"
    assert isinstance(result.description, FieldSource)
    assert result.description.value == "Custom context link"


def test_source_tracking():
    """Test that source location information is preserved."""
    yaml_content = textwrap.dedent(
        """
        operationId: getUserById
        description: Get user details
        parameters:
          userId: $response.body#/id
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = link.build(root)
    assert isinstance(result, link.Link)

    # Check operationId source tracking
    assert isinstance(result.operation_id, FieldSource)
    assert result.operation_id.key_node is not None
    assert result.operation_id.value_node is not None
    assert result.operation_id.key_node.value == "operationId"

    # Check description source tracking
    assert isinstance(result.description, FieldSource)
    assert result.description.key_node is not None
    assert result.description.value_node is not None
    assert result.description.key_node.value == "description"

    # Check parameters source tracking
    assert isinstance(result.parameters, FieldSource)
    assert result.parameters.key_node is not None
    assert result.parameters.value_node is not None
    assert result.parameters.key_node.value == "parameters"

    # Check line numbers are available
    assert hasattr(result.operation_id.key_node.start_mark, "line")
    assert hasattr(result.operation_id.value_node.start_mark, "line")


def test_build_with_runtime_expressions():
    """Test building Link with runtime expressions in parameters."""
    yaml_content = textwrap.dedent(
        """
        operationId: getUserRepositories
        parameters:
          username: $response.body#/username
          page: $request.query.page
          token: $request.header.authorization
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = link.build(root)
    assert isinstance(result, link.Link)

    assert isinstance(result.parameters, FieldSource)
    params = {k.value: v.value for k, v in result.parameters.value.items()}
    assert params["username"] == "$response.body#/username"
    assert params["page"] == "$request.query.page"
    assert params["token"] == "$request.header.authorization"


def test_build_real_world_example():
    """Test a complete real-world Link object."""
    yaml_content = textwrap.dedent(
        """
        operationRef: '#/paths/~12.0~1repositories~1{username}/get'
        description: The repositories owned by {username}
        parameters:
          username: $response.body#/username
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = link.build(root)
    assert isinstance(result, link.Link)

    assert isinstance(result.operation_ref, FieldSource)
    assert result.operation_ref.value == "#/paths/~12.0~1repositories~1{username}/get"
    assert isinstance(result.description, FieldSource)
    assert result.description.value == "The repositories owned by {username}"
    assert isinstance(result.parameters, FieldSource)
    assert len(result.parameters.value) == 1

    params = {k.value: v.value for k, v in result.parameters.value.items()}
    assert params["username"] == "$response.body#/username"


def test_build_with_invalid_server():
    """Test that invalid server data is preserved."""
    yaml_content = textwrap.dedent(
        """
        operationId: getUserById
        server: invalid-string-not-object
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = link.build(root)
    assert isinstance(result, link.Link)

    assert isinstance(result.server, FieldSource)
    # The invalid data should be preserved
    assert result.server.value == "invalid-string-not-object"


def test_parameters_source_tracking():
    """Test that parameters maintain proper source tracking."""
    yaml_content = textwrap.dedent(
        """
        operationId: getUserById
        parameters:
          userId: $response.body#/id
          include: profile
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = link.build(root)
    assert isinstance(result, link.Link)

    assert isinstance(result.parameters, FieldSource)

    # Check that each parameter key has source tracking
    for param_key, param_value in result.parameters.value.items():
        assert param_key.key_node is not None
        assert isinstance(param_value, ValueSource)
        assert param_value.value_node is not None
