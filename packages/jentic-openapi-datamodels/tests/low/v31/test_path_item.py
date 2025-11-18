"""Tests for PathItem low-level datamodel."""

import textwrap

from ruamel.yaml import YAML

from jentic.apitools.openapi.datamodels.low.context import Context
from jentic.apitools.openapi.datamodels.low.sources import FieldSource, KeySource, ValueSource
from jentic.apitools.openapi.datamodels.low.v31 import path_item
from jentic.apitools.openapi.datamodels.low.v31.operation import Operation
from jentic.apitools.openapi.datamodels.low.v31.parameter import Parameter
from jentic.apitools.openapi.datamodels.low.v31.reference import Reference
from jentic.apitools.openapi.datamodels.low.v31.server import Server


def test_build_with_empty_object():
    """Test building PathItem from empty YAML object."""
    yaml_content = "{}"
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = path_item.build(root)
    assert isinstance(result, path_item.PathItem)

    assert result.root_node == root
    assert result.get is None
    assert result.post is None
    assert result.extensions == {}


def test_build_with_get_operation():
    """Test building PathItem with GET operation."""
    yaml_content = textwrap.dedent(
        """
        get:
          summary: List items
          responses:
            '200':
              description: successful operation
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = path_item.build(root)
    assert isinstance(result, path_item.PathItem)

    assert result.get is not None
    assert isinstance(result.get.value, Operation)


def test_build_with_post_operation():
    """Test building PathItem with POST operation."""
    yaml_content = textwrap.dedent(
        """
        post:
          summary: Create item
          responses:
            '201':
              description: item created
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = path_item.build(root)
    assert isinstance(result, path_item.PathItem)

    assert result.post is not None
    assert isinstance(result.post.value, Operation)


def test_build_with_all_http_methods():
    """Test building PathItem with all HTTP methods."""
    yaml_content = textwrap.dedent(
        """
        get:
          responses:
            '200':
              description: success
        put:
          responses:
            '200':
              description: success
        post:
          responses:
            '201':
              description: created
        delete:
          responses:
            '204':
              description: deleted
        options:
          responses:
            '200':
              description: success
        head:
          responses:
            '200':
              description: success
        patch:
          responses:
            '200':
              description: success
        trace:
          responses:
            '200':
              description: success
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = path_item.build(root)
    assert isinstance(result, path_item.PathItem)

    assert result.get is not None
    assert result.put is not None
    assert result.post is not None
    assert result.delete is not None
    assert result.options is not None
    assert result.head is not None
    assert result.patch is not None
    assert result.trace is not None


def test_build_with_summary_and_description():
    """Test building PathItem with summary and description."""
    yaml_content = textwrap.dedent(
        """
        summary: User operations
        description: Operations related to user management
        get:
          responses:
            '200':
              description: success
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = path_item.build(root)
    assert isinstance(result, path_item.PathItem)

    assert result.summary is not None
    assert result.summary.value == "User operations"
    assert result.description is not None
    assert result.description.value == "Operations related to user management"


def test_build_with_ref():
    """Test building PathItem with $ref."""
    yaml_content = textwrap.dedent(
        """
        $ref: '#/components/pathItems/UserPath'
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = path_item.build(root)
    assert isinstance(result, path_item.PathItem)

    assert result.ref is not None
    assert result.ref.value == "#/components/pathItems/UserPath"


def test_build_with_servers():
    """Test building PathItem with servers."""
    yaml_content = textwrap.dedent(
        """
        servers:
          - url: https://api.example.com/v1
            description: Production server
          - url: https://staging-api.example.com/v1
            description: Staging server
        get:
          responses:
            '200':
              description: success
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = path_item.build(root)
    assert isinstance(result, path_item.PathItem)

    assert result.servers is not None
    assert len(result.servers.value) == 2
    assert all(isinstance(s, Server) for s in result.servers.value)


def test_build_with_parameters():
    """Test building PathItem with parameters."""
    yaml_content = textwrap.dedent(
        """
        parameters:
          - name: userId
            in: path
            required: true
            schema:
              type: integer
          - name: X-Request-ID
            in: header
            schema:
              type: string
        get:
          responses:
            '200':
              description: success
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = path_item.build(root)
    assert isinstance(result, path_item.PathItem)

    assert result.parameters is not None
    assert len(result.parameters.value) == 2
    assert all(isinstance(p, Parameter) for p in result.parameters.value)


def test_build_with_parameter_references():
    """Test building PathItem with parameter references."""
    yaml_content = textwrap.dedent(
        """
        parameters:
          - $ref: '#/components/parameters/UserId'
          - name: page
            in: query
            schema:
              type: integer
        get:
          responses:
            '200':
              description: success
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = path_item.build(root)
    assert isinstance(result, path_item.PathItem)

    assert result.parameters is not None
    assert len(result.parameters.value) == 2
    assert isinstance(result.parameters.value[0], Reference)
    assert isinstance(result.parameters.value[1], Parameter)


def test_build_with_extensions():
    """Test building PathItem with specification extensions."""
    yaml_content = textwrap.dedent(
        """
        x-internal: true
        x-rate-limit: 100
        get:
          responses:
            '200':
              description: success
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = path_item.build(root)
    assert isinstance(result, path_item.PathItem)

    assert len(result.extensions) == 2
    ext_dict = {k.value: v.value for k, v in result.extensions.items()}
    assert ext_dict["x-internal"] is True
    assert ext_dict["x-rate-limit"] == 100


def test_build_with_all_fields():
    """Test building PathItem with all possible fields."""
    yaml_content = textwrap.dedent(
        """
        summary: User operations
        description: Complete user management
        servers:
          - url: https://api.example.com
        parameters:
          - name: userId
            in: path
            required: true
            schema:
              type: string
        get:
          summary: Get user
          responses:
            '200':
              description: success
        post:
          summary: Create user
          responses:
            '201':
              description: created
        x-internal: true
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = path_item.build(root)
    assert isinstance(result, path_item.PathItem)

    assert result.summary is not None
    assert result.description is not None
    assert result.servers is not None
    assert result.parameters is not None
    assert result.get is not None
    assert result.post is not None
    assert len(result.extensions) == 1


def test_build_with_invalid_node_returns_value_source():
    """Test that build returns ValueSource for non-mapping nodes."""
    yaml_parser = YAML()

    # Scalar node
    scalar_root = yaml_parser.compose("not-a-path-item-object")
    result = path_item.build(scalar_root)
    assert isinstance(result, ValueSource)
    assert result.value == "not-a-path-item-object"
    assert result.value_node == scalar_root

    # Sequence node
    sequence_root = yaml_parser.compose("['get', 'post']")
    result = path_item.build(sequence_root)
    assert isinstance(result, ValueSource)
    assert result.value == ["get", "post"]
    assert result.value_node == sequence_root


def test_build_with_custom_context():
    """Test building PathItem with a custom context."""
    yaml_content = textwrap.dedent(
        """
        get:
          responses:
            '200':
              description: success
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    custom_context = Context()
    result = path_item.build(root, context=custom_context)
    assert isinstance(result, path_item.PathItem)

    assert result.get is not None


def test_source_tracking():
    """Test that source location information is preserved."""
    yaml_content = textwrap.dedent(
        """
        summary: Test path
        get:
          responses:
            '200':
              description: success
        x-custom: value
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = path_item.build(root)
    assert isinstance(result, path_item.PathItem)

    # Check field source tracking
    assert isinstance(result.summary, FieldSource)
    assert result.summary.key_node is not None
    assert result.summary.value_node is not None
    assert result.summary.key_node.value == "summary"

    # Check extension source tracking
    for key_source, value_source in result.extensions.items():
        assert isinstance(key_source, KeySource)
        assert key_source.key_node is not None
        assert isinstance(value_source, ValueSource)
        assert value_source.value_node is not None

    # Check line numbers are available
    assert hasattr(result.summary.key_node.start_mark, "line")
    assert hasattr(result.summary.value_node.start_mark, "line")


def test_build_with_invalid_servers_data():
    """Test that invalid servers data is preserved."""
    yaml_content = textwrap.dedent(
        """
        servers: not-an-array
        get:
          responses:
            '200':
              description: success
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = path_item.build(root)
    assert isinstance(result, path_item.PathItem)

    # Invalid servers should be preserved as-is
    assert result.servers is not None
    assert result.servers.value == "not-an-array"


def test_build_with_invalid_parameters_data():
    """Test that invalid parameters data is preserved."""
    yaml_content = textwrap.dedent(
        """
        parameters: not-an-array
        get:
          responses:
            '200':
              description: success
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = path_item.build(root)
    assert isinstance(result, path_item.PathItem)

    # Invalid parameters should be preserved as-is
    assert result.parameters is not None
    assert result.parameters.value == "not-an-array"


def test_build_with_null_values():
    """Test that build preserves null values."""
    yaml_content = textwrap.dedent(
        """
        summary:
        description:
        get:
          responses:
            '200':
              description: success
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = path_item.build(root)
    assert isinstance(result, path_item.PathItem)

    assert result.summary is not None
    assert result.summary.value is None
    assert result.description is not None
    assert result.description.value is None


def test_build_real_world_rest_endpoint():
    """Test a complete real-world REST endpoint."""
    yaml_content = textwrap.dedent(
        """
        summary: User resource
        parameters:
          - name: userId
            in: path
            required: true
            schema:
              type: integer
              format: int64
        get:
          summary: Get user by ID
          operationId: getUserById
          responses:
            '200':
              description: successful operation
            '404':
              description: user not found
        put:
          summary: Update user
          operationId: updateUser
          requestBody:
            required: true
            content:
              application/json:
                schema:
                  type: object
          responses:
            '200':
              description: user updated
            '404':
              description: user not found
        delete:
          summary: Delete user
          operationId: deleteUser
          responses:
            '204':
              description: user deleted
            '404':
              description: user not found
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = path_item.build(root)
    assert isinstance(result, path_item.PathItem)

    assert result.summary is not None
    assert result.summary.value == "User resource"
    assert result.parameters is not None
    assert len(result.parameters.value) == 1
    assert result.get is not None
    assert result.put is not None
    assert result.delete is not None


def test_build_with_common_parameters():
    """Test PathItem with parameters shared across operations."""
    yaml_content = textwrap.dedent(
        """
        parameters:
          - name: Accept-Language
            in: header
            schema:
              type: string
          - name: X-Request-ID
            in: header
            schema:
              type: string
        get:
          summary: Get resource
          responses:
            '200':
              description: success
        post:
          summary: Create resource
          responses:
            '201':
              description: created
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = path_item.build(root)
    assert isinstance(result, path_item.PathItem)

    assert result.parameters is not None
    assert len(result.parameters.value) == 2
    assert result.get is not None
    assert result.post is not None


def test_build_with_alternative_servers():
    """Test PathItem with alternative servers for specific path."""
    yaml_content = textwrap.dedent(
        """
        servers:
          - url: https://legacy-api.example.com/v1
            description: Legacy API server for this endpoint
        get:
          summary: Legacy endpoint
          responses:
            '200':
              description: success
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = path_item.build(root)
    assert isinstance(result, path_item.PathItem)

    assert result.servers is not None
    assert len(result.servers.value) == 1
    server = result.servers.value[0]
    assert isinstance(server, Server)
