"""Tests for Operation low-level datamodel."""

import textwrap

from ruamel.yaml import YAML

from jentic.apitools.openapi.datamodels.low.context import Context
from jentic.apitools.openapi.datamodels.low.sources import FieldSource, KeySource, ValueSource
from jentic.apitools.openapi.datamodels.low.v30 import operation
from jentic.apitools.openapi.datamodels.low.v30.callback import Callback
from jentic.apitools.openapi.datamodels.low.v30.external_documentation import ExternalDocumentation
from jentic.apitools.openapi.datamodels.low.v30.parameter import Parameter
from jentic.apitools.openapi.datamodels.low.v30.reference import Reference
from jentic.apitools.openapi.datamodels.low.v30.request_body import RequestBody
from jentic.apitools.openapi.datamodels.low.v30.responses import Responses
from jentic.apitools.openapi.datamodels.low.v30.security_requirement import SecurityRequirement
from jentic.apitools.openapi.datamodels.low.v30.server import Server


def test_build_with_minimal_fields():
    """Test building Operation with only required field (responses)."""
    yaml_content = textwrap.dedent(
        """
        responses:
          '200':
            description: successful operation
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = operation.build(root)
    assert isinstance(result, operation.Operation)

    assert result.responses is not None
    assert isinstance(result.responses.value, Responses)


def test_build_with_summary_and_description():
    """Test building Operation with summary and description."""
    yaml_content = textwrap.dedent(
        """
        summary: List all users
        description: Returns a list of all users in the system
        responses:
          '200':
            description: successful operation
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = operation.build(root)
    assert isinstance(result, operation.Operation)

    assert result.summary is not None
    assert result.summary.value == "List all users"
    assert result.description is not None
    assert result.description.value == "Returns a list of all users in the system"


def test_build_with_operation_id():
    """Test building Operation with operationId."""
    yaml_content = textwrap.dedent(
        """
        operationId: listUsers
        responses:
          '200':
            description: successful operation
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = operation.build(root)
    assert isinstance(result, operation.Operation)

    assert result.operation_id is not None
    assert result.operation_id.value == "listUsers"


def test_build_with_tags():
    """Test building Operation with tags."""
    yaml_content = textwrap.dedent(
        """
        tags:
          - users
          - admin
        responses:
          '200':
            description: successful operation
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = operation.build(root)
    assert isinstance(result, operation.Operation)

    assert result.tags is not None
    assert len(result.tags.value) == 2
    tag_values = [t.value for t in result.tags.value]
    assert tag_values == ["users", "admin"]


def test_build_with_external_docs():
    """Test building Operation with externalDocs."""
    yaml_content = textwrap.dedent(
        """
        externalDocs:
          description: Find more info here
          url: https://example.com/docs
        responses:
          '200':
            description: successful operation
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = operation.build(root)
    assert isinstance(result, operation.Operation)

    assert result.external_docs is not None
    assert isinstance(result.external_docs.value, ExternalDocumentation)


def test_build_with_parameters():
    """Test building Operation with parameters."""
    yaml_content = textwrap.dedent(
        """
        parameters:
          - name: userId
            in: path
            required: true
            schema:
              type: integer
          - name: page
            in: query
            schema:
              type: integer
        responses:
          '200':
            description: successful operation
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = operation.build(root)
    assert isinstance(result, operation.Operation)

    assert result.parameters is not None
    assert len(result.parameters.value) == 2
    assert all(isinstance(p, Parameter) for p in result.parameters.value)


def test_build_with_parameter_references():
    """Test building Operation with parameter references."""
    yaml_content = textwrap.dedent(
        """
        parameters:
          - $ref: '#/components/parameters/UserId'
          - name: page
            in: query
            schema:
              type: integer
        responses:
          '200':
            description: successful operation
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = operation.build(root)
    assert isinstance(result, operation.Operation)

    assert result.parameters is not None
    assert len(result.parameters.value) == 2
    assert isinstance(result.parameters.value[0], Reference)
    assert isinstance(result.parameters.value[1], Parameter)


def test_build_with_request_body():
    """Test building Operation with requestBody."""
    yaml_content = textwrap.dedent(
        """
        requestBody:
          required: true
          content:
            application/json:
              schema:
                type: object
        responses:
          '200':
            description: successful operation
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = operation.build(root)
    assert isinstance(result, operation.Operation)

    assert result.request_body is not None
    assert isinstance(result.request_body.value, RequestBody)


def test_build_with_request_body_reference():
    """Test building Operation with requestBody as reference."""
    yaml_content = textwrap.dedent(
        """
        requestBody:
          $ref: '#/components/requestBodies/UserBody'
        responses:
          '200':
            description: successful operation
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = operation.build(root)
    assert isinstance(result, operation.Operation)

    assert result.request_body is not None
    assert isinstance(result.request_body.value, Reference)


def test_build_with_callbacks():
    """Test building Operation with callbacks."""
    yaml_content = textwrap.dedent(
        """
        callbacks:
          onData:
            '{$request.body#/callbackUrl}':
              post:
                responses:
                  '200':
                    description: callback received
        responses:
          '200':
            description: successful operation
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = operation.build(root)
    assert isinstance(result, operation.Operation)

    assert result.callbacks is not None
    assert len(result.callbacks.value) == 1
    callback_keys = {k.value for k in result.callbacks.value.keys()}
    assert "onData" in callback_keys
    assert isinstance(result.callbacks.value[next(iter(result.callbacks.value.keys()))], Callback)


def test_build_with_callback_references():
    """Test building Operation with callback references."""
    yaml_content = textwrap.dedent(
        """
        callbacks:
          onData:
            $ref: '#/components/callbacks/DataCallback'
        responses:
          '200':
            description: successful operation
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = operation.build(root)
    assert isinstance(result, operation.Operation)

    assert result.callbacks is not None
    assert len(result.callbacks.value) == 1
    assert isinstance(result.callbacks.value[next(iter(result.callbacks.value.keys()))], Reference)


def test_build_with_deprecated():
    """Test building Operation with deprecated flag."""
    yaml_content = textwrap.dedent(
        """
        deprecated: true
        responses:
          '200':
            description: successful operation
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = operation.build(root)
    assert isinstance(result, operation.Operation)

    assert result.deprecated is not None
    assert result.deprecated.value is True


def test_build_with_security():
    """Test building Operation with security requirements."""
    yaml_content = textwrap.dedent(
        """
        security:
          - api_key: []
          - oauth2:
              - read:users
              - write:users
        responses:
          '200':
            description: successful operation
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = operation.build(root)
    assert isinstance(result, operation.Operation)

    assert result.security is not None
    assert len(result.security.value) == 2
    assert all(isinstance(s, SecurityRequirement) for s in result.security.value)


def test_build_with_servers():
    """Test building Operation with servers."""
    yaml_content = textwrap.dedent(
        """
        servers:
          - url: https://api.example.com/v1
            description: Production server
          - url: https://staging-api.example.com/v1
            description: Staging server
        responses:
          '200':
            description: successful operation
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = operation.build(root)
    assert isinstance(result, operation.Operation)

    assert result.servers is not None
    assert len(result.servers.value) == 2
    assert all(isinstance(s, Server) for s in result.servers.value)


def test_build_with_extensions():
    """Test building Operation with specification extensions."""
    yaml_content = textwrap.dedent(
        """
        x-internal: true
        x-rate-limit: 100
        responses:
          '200':
            description: successful operation
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = operation.build(root)
    assert isinstance(result, operation.Operation)

    assert len(result.extensions) == 2
    ext_dict = {k.value: v.value for k, v in result.extensions.items()}
    assert ext_dict["x-internal"] is True
    assert ext_dict["x-rate-limit"] == 100


def test_build_with_all_fields():
    """Test building Operation with all possible fields."""
    yaml_content = textwrap.dedent(
        """
        tags:
          - users
        summary: Create user
        description: Creates a new user in the system
        externalDocs:
          url: https://example.com/docs
        operationId: createUser
        parameters:
          - name: X-Request-ID
            in: header
            schema:
              type: string
        requestBody:
          required: true
          content:
            application/json:
              schema:
                type: object
        responses:
          '201':
            description: user created
          '400':
            description: invalid input
        callbacks:
          onCreate:
            '{$request.body#/callbackUrl}':
              post:
                responses:
                  '200':
                    description: callback received
        deprecated: false
        security:
          - api_key: []
        servers:
          - url: https://api.example.com
        x-code-samples: []
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = operation.build(root)
    assert isinstance(result, operation.Operation)

    assert result.tags is not None
    assert result.summary is not None
    assert result.description is not None
    assert result.external_docs is not None
    assert result.operation_id is not None
    assert result.parameters is not None
    assert result.request_body is not None
    assert result.responses is not None
    assert result.callbacks is not None
    assert result.deprecated is not None
    assert result.security is not None
    assert result.servers is not None
    assert len(result.extensions) == 1


def test_build_with_empty_object():
    """Test building Operation from empty YAML object."""
    yaml_content = "{}"
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = operation.build(root)
    assert isinstance(result, operation.Operation)

    assert result.root_node == root
    assert result.responses is None
    assert result.extensions == {}


def test_build_with_invalid_node_returns_value_source():
    """Test that build returns ValueSource for non-mapping nodes."""
    yaml_parser = YAML()

    # Scalar node
    scalar_root = yaml_parser.compose("not-an-operation-object")
    result = operation.build(scalar_root)
    assert isinstance(result, ValueSource)
    assert result.value == "not-an-operation-object"
    assert result.value_node == scalar_root

    # Sequence node
    sequence_root = yaml_parser.compose("['get', 'post']")
    result = operation.build(sequence_root)
    assert isinstance(result, ValueSource)
    assert result.value == ["get", "post"]
    assert result.value_node == sequence_root


def test_build_with_custom_context():
    """Test building Operation with a custom context."""
    yaml_content = textwrap.dedent(
        """
        operationId: testOp
        responses:
          '200':
            description: success
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    custom_context = Context()
    result = operation.build(root, context=custom_context)
    assert isinstance(result, operation.Operation)

    assert result.operation_id is not None
    assert result.operation_id.value == "testOp"


def test_source_tracking():
    """Test that source location information is preserved."""
    yaml_content = textwrap.dedent(
        """
        summary: Test operation
        operationId: testOp
        tags:
          - test
        responses:
          '200':
            description: success
        x-custom: value
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = operation.build(root)
    assert isinstance(result, operation.Operation)

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


def test_build_with_invalid_tags_data():
    """Test that invalid tags data is preserved."""
    yaml_content = textwrap.dedent(
        """
        tags: not-an-array
        responses:
          '200':
            description: success
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = operation.build(root)
    assert isinstance(result, operation.Operation)

    # Invalid tags should be preserved as-is
    assert result.tags is not None
    assert result.tags.value == "not-an-array"


def test_build_with_invalid_parameters_data():
    """Test that invalid parameters data is preserved."""
    yaml_content = textwrap.dedent(
        """
        parameters: not-an-array
        responses:
          '200':
            description: success
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = operation.build(root)
    assert isinstance(result, operation.Operation)

    # Invalid parameters should be preserved as-is
    assert result.parameters is not None
    assert result.parameters.value == "not-an-array"


def test_build_with_null_values():
    """Test that build preserves null values."""
    yaml_content = textwrap.dedent(
        """
        summary:
        description:
        responses:
          '200':
            description: success
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = operation.build(root)
    assert isinstance(result, operation.Operation)

    assert result.summary is not None
    assert result.summary.value is None
    assert result.description is not None
    assert result.description.value is None


def test_build_real_world_get_operation():
    """Test a complete real-world GET operation."""
    yaml_content = textwrap.dedent(
        """
        tags:
          - users
        summary: Get user by ID
        description: Returns a single user
        operationId: getUserById
        parameters:
          - name: userId
            in: path
            description: ID of user to return
            required: true
            schema:
              type: integer
              format: int64
        responses:
          '200':
            description: successful operation
            content:
              application/json:
                schema:
                  type: object
          '400':
            description: invalid ID supplied
          '404':
            description: user not found
        security:
          - api_key: []
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = operation.build(root)
    assert isinstance(result, operation.Operation)

    assert result.tags is not None
    assert result.summary is not None
    assert result.operation_id is not None
    assert result.operation_id.value == "getUserById"
    assert result.parameters is not None
    assert len(result.parameters.value) == 1
    assert result.security is not None


def test_build_real_world_post_operation():
    """Test a complete real-world POST operation."""
    yaml_content = textwrap.dedent(
        """
        tags:
          - users
        summary: Create a new user
        operationId: createUser
        requestBody:
          description: User object to be created
          required: true
          content:
            application/json:
              schema:
                type: object
                properties:
                  name:
                    type: string
                  email:
                    type: string
        responses:
          '201':
            description: user created successfully
          '400':
            description: invalid input
        callbacks:
          userCreated:
            '{$request.body#/webhookUrl}':
              post:
                requestBody:
                  content:
                    application/json:
                      schema:
                        type: object
                responses:
                  '200':
                    description: webhook received
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = operation.build(root)
    assert isinstance(result, operation.Operation)

    assert result.operation_id is not None
    assert result.operation_id.value == "createUser"
    assert result.request_body is not None
    assert isinstance(result.request_body.value, RequestBody)
    assert result.callbacks is not None
    assert len(result.callbacks.value) == 1
