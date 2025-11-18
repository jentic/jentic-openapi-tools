"""Tests for Components low-level datamodel."""

import textwrap

from ruamel.yaml import YAML

from jentic.apitools.openapi.datamodels.low.context import Context
from jentic.apitools.openapi.datamodels.low.sources import ValueSource
from jentic.apitools.openapi.datamodels.low.v31 import components
from jentic.apitools.openapi.datamodels.low.v31.callback import Callback
from jentic.apitools.openapi.datamodels.low.v31.example import Example
from jentic.apitools.openapi.datamodels.low.v31.header import Header
from jentic.apitools.openapi.datamodels.low.v31.link import Link
from jentic.apitools.openapi.datamodels.low.v31.parameter import Parameter
from jentic.apitools.openapi.datamodels.low.v31.path_item import PathItem
from jentic.apitools.openapi.datamodels.low.v31.reference import Reference
from jentic.apitools.openapi.datamodels.low.v31.request_body import RequestBody
from jentic.apitools.openapi.datamodels.low.v31.response import Response
from jentic.apitools.openapi.datamodels.low.v31.schema import Schema
from jentic.apitools.openapi.datamodels.low.v31.security_scheme import SecurityScheme


def test_build_with_schemas():
    """Test building Components with schemas field."""
    yaml_content = textwrap.dedent(
        """
        schemas:
          User:
            type: object
            properties:
              id:
                type: integer
              name:
                type: string
          Product:
            type: object
            properties:
              id:
                type: integer
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = components.build(root)
    assert isinstance(result, components.Components)

    assert result.root_node == root
    assert result.schemas is not None
    schema_keys = {k.value for k in result.schemas.value.keys()}
    assert schema_keys == {"User", "Product"}

    # Verify schema objects are built
    for schema_obj in result.schemas.value.values():
        assert isinstance(schema_obj, Schema)


def test_build_with_responses():
    """Test building Components with responses field."""
    yaml_content = textwrap.dedent(
        """
        responses:
          NotFound:
            description: Entity not found
          Unauthorized:
            description: Unauthorized access
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = components.build(root)
    assert isinstance(result, components.Components)

    assert result.responses is not None
    response_keys = {k.value for k in result.responses.value.keys()}
    assert response_keys == {"NotFound", "Unauthorized"}

    # Verify response objects are built
    for response_obj in result.responses.value.values():
        assert isinstance(response_obj, Response)


def test_build_with_parameters():
    """Test building Components with parameters field."""
    yaml_content = textwrap.dedent(
        """
        parameters:
          PageLimit:
            name: limit
            in: query
            description: Page size
            schema:
              type: integer
          UserId:
            name: id
            in: path
            required: true
            schema:
              type: integer
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = components.build(root)
    assert isinstance(result, components.Components)

    assert result.parameters is not None
    param_keys = {k.value for k in result.parameters.value.keys()}
    assert param_keys == {"PageLimit", "UserId"}

    # Verify parameter objects are built
    for param_obj in result.parameters.value.values():
        assert isinstance(param_obj, Parameter)


def test_build_with_examples():
    """Test building Components with examples field."""
    yaml_content = textwrap.dedent(
        """
        examples:
          UserExample:
            summary: A user example
            value:
              id: 1
              name: John Doe
          ProductExample:
            summary: A product example
            value:
              id: 100
              name: Widget
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = components.build(root)
    assert isinstance(result, components.Components)

    assert result.examples is not None
    example_keys = {k.value for k in result.examples.value.keys()}
    assert example_keys == {"UserExample", "ProductExample"}

    # Verify example objects are built
    for example_obj in result.examples.value.values():
        assert isinstance(example_obj, Example)


def test_build_with_request_bodies():
    """Test building Components with requestBodies field."""
    yaml_content = textwrap.dedent(
        """
        requestBodies:
          UserBody:
            description: User request body
            required: true
            content:
              application/json:
                schema:
                  type: object
          ProductBody:
            description: Product request body
            content:
              application/json:
                schema:
                  type: object
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = components.build(root)
    assert isinstance(result, components.Components)

    assert result.request_bodies is not None
    rb_keys = {k.value for k in result.request_bodies.value.keys()}
    assert rb_keys == {"UserBody", "ProductBody"}

    # Verify request body objects are built
    for rb_obj in result.request_bodies.value.values():
        assert isinstance(rb_obj, RequestBody)


def test_build_with_headers():
    """Test building Components with headers field."""
    yaml_content = textwrap.dedent(
        """
        headers:
          RateLimit:
            description: Rate limit header
            schema:
              type: integer
          ApiVersion:
            description: API version header
            schema:
              type: string
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = components.build(root)
    assert isinstance(result, components.Components)

    assert result.headers is not None
    header_keys = {k.value for k in result.headers.value.keys()}
    assert header_keys == {"RateLimit", "ApiVersion"}

    # Verify header objects are built
    for header_obj in result.headers.value.values():
        assert isinstance(header_obj, Header)


def test_build_with_security_schemes():
    """Test building Components with securitySchemes field."""
    yaml_content = textwrap.dedent(
        """
        securitySchemes:
          ApiKey:
            type: apiKey
            name: api_key
            in: header
          OAuth2:
            type: oauth2
            flows:
              implicit:
                authorizationUrl: https://example.com/oauth/authorize
                scopes:
                  read: Read access
                  write: Write access
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = components.build(root)
    assert isinstance(result, components.Components)

    assert result.security_schemes is not None
    ss_keys = {k.value for k in result.security_schemes.value.keys()}
    assert ss_keys == {"ApiKey", "OAuth2"}

    # Verify security scheme objects are built
    for ss_obj in result.security_schemes.value.values():
        assert isinstance(ss_obj, SecurityScheme)


def test_build_with_links():
    """Test building Components with links field."""
    yaml_content = textwrap.dedent(
        """
        links:
          GetUserById:
            operationId: getUserById
            parameters:
              userId: $response.body#/id
          GetUserOrders:
            operationRef: '#/paths/~1users~1{id}~1orders/get'
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = components.build(root)
    assert isinstance(result, components.Components)

    assert result.links is not None
    link_keys = {k.value for k in result.links.value.keys()}
    assert link_keys == {"GetUserById", "GetUserOrders"}

    # Verify link objects are built
    for link_obj in result.links.value.values():
        assert isinstance(link_obj, Link)


def test_build_with_callbacks():
    """Test building Components with callbacks field."""
    yaml_content = textwrap.dedent(
        """
        callbacks:
          WebhookCallback:
            '{$request.body#/callbackUrl}':
              post:
                requestBody:
                  content:
                    application/json:
                      schema:
                        type: object
                responses:
                  '200':
                    description: Success
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = components.build(root)
    assert isinstance(result, components.Components)

    assert result.callbacks is not None
    callback_keys = {k.value for k in result.callbacks.value.keys()}
    assert callback_keys == {"WebhookCallback"}

    # Verify callback objects are built
    for callback_obj in result.callbacks.value.values():
        assert isinstance(callback_obj, Callback)


def test_build_with_all_fields():
    """Test building Components with all component types."""
    yaml_content = textwrap.dedent(
        """
        schemas:
          User:
            type: object
        responses:
          NotFound:
            description: Not found
        parameters:
          PageLimit:
            name: limit
            in: query
            schema:
              type: integer
        examples:
          UserExample:
            value:
              id: 1
        requestBodies:
          UserBody:
            content:
              application/json:
                schema:
                  type: object
        headers:
          RateLimit:
            schema:
              type: integer
        securitySchemes:
          ApiKey:
            type: apiKey
            name: api_key
            in: header
        links:
          GetUser:
            operationId: getUser
        callbacks:
          Webhook:
            '{$request.body#/url}':
              post:
                responses:
                  '200':
                    description: Success
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = components.build(root)
    assert isinstance(result, components.Components)

    # Verify all fields are present
    assert result.schemas is not None
    assert result.responses is not None
    assert result.parameters is not None
    assert result.examples is not None
    assert result.request_bodies is not None
    assert result.headers is not None
    assert result.security_schemes is not None
    assert result.links is not None
    assert result.callbacks is not None


def test_build_with_references():
    """Test building Components with references."""
    yaml_content = textwrap.dedent(
        """
        schemas:
          User:
            type: object
          UserRef:
            $ref: '#/components/schemas/User'
        responses:
          NotFoundRef:
            $ref: '#/components/responses/NotFound'
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = components.build(root)
    assert isinstance(result, components.Components)

    # Check schemas
    assert result.schemas is not None
    schema_keys = {k.value for k in result.schemas.value.keys()}
    assert schema_keys == {"User", "UserRef"}

    # In OpenAPI 3.1, both are Schema objects (schemas can have $ref directly)
    user_schema = result.schemas.value[
        next(k for k in result.schemas.value.keys() if k.value == "User")
    ]
    user_ref = result.schemas.value[
        next(k for k in result.schemas.value.keys() if k.value == "UserRef")
    ]
    assert isinstance(user_schema, Schema)
    assert isinstance(user_ref, Schema)  # In 3.1, this is a Schema with $ref, not a Reference

    # Check responses reference
    assert result.responses is not None
    response_obj = list(result.responses.value.values())[0]
    assert isinstance(response_obj, Reference)


def test_build_with_extensions():
    """Test building Components with specification extensions."""
    yaml_content = textwrap.dedent(
        """
        schemas:
          User:
            type: object
        x-internal-id: comp-001
        x-version: 1.0
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = components.build(root)
    assert isinstance(result, components.Components)

    assert len(result.extensions) == 2
    ext_dict = {k.value: v.value for k, v in result.extensions.items()}
    assert ext_dict["x-internal-id"] == "comp-001"
    assert ext_dict["x-version"] == 1.0


def test_build_with_empty_object():
    """Test building Components from empty YAML object."""
    yaml_content = "{}"
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = components.build(root)
    assert isinstance(result, components.Components)

    # All component fields should be None
    assert result.schemas is None
    assert result.responses is None
    assert result.parameters is None
    assert result.examples is None
    assert result.request_bodies is None
    assert result.headers is None
    assert result.security_schemes is None
    assert result.links is None
    assert result.callbacks is None
    assert result.extensions == {}


def test_build_with_invalid_node_returns_value_source():
    """Test building Components with invalid root node returns ValueSource."""
    yaml_content = "invalid scalar value"
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = components.build(root)
    assert isinstance(result, ValueSource)
    assert result.value == "invalid scalar value"


def test_build_with_custom_context():
    """Test building Components with custom context."""
    yaml_content = textwrap.dedent(
        """
        schemas:
          User:
            type: object
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    custom_context = Context()
    result = components.build(root, context=custom_context)
    assert isinstance(result, components.Components)
    assert result.schemas is not None


def test_source_tracking():
    """Test that source nodes are properly tracked."""
    yaml_content = textwrap.dedent(
        """
        schemas:
          User:
            type: object
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = components.build(root)
    assert isinstance(result, components.Components)

    # Check root node is tracked
    assert result.root_node == root

    # Check schemas field tracking
    assert result.schemas is not None
    assert result.schemas.key_node is not None
    assert result.schemas.value_node is not None

    # Check schema keys track their nodes
    for key_source in result.schemas.value.keys():
        assert key_source.key_node is not None


def test_build_with_invalid_field_types():
    """Test building Components with invalid field types (non-mappings)."""
    yaml_content = textwrap.dedent(
        """
        schemas: invalid_scalar
        responses:
          - array_instead_of_map
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = components.build(root)
    assert isinstance(result, components.Components)

    # Invalid fields should still be captured as FieldSource
    assert result.schemas is not None
    assert result.schemas.value == "invalid_scalar"

    assert result.responses is not None
    assert isinstance(result.responses.value, list)


def test_build_real_world_components():
    """Test building Components with realistic OpenAPI structure."""
    yaml_content = textwrap.dedent(
        """
        schemas:
          Error:
            type: object
            required:
              - code
              - message
            properties:
              code:
                type: integer
                format: int32
              message:
                type: string
          Pet:
            type: object
            required:
              - id
              - name
            properties:
              id:
                type: integer
                format: int64
              name:
                type: string
              tag:
                type: string
        responses:
          NotFound:
            description: The specified resource was not found
            content:
              application/json:
                schema:
                  $ref: '#/components/schemas/Error'
          Unauthorized:
            description: Unauthorized
        parameters:
          limitParam:
            name: limit
            in: query
            description: How many items to return
            required: false
            schema:
              type: integer
              format: int32
        securitySchemes:
          bearerAuth:
            type: http
            scheme: bearer
            bearerFormat: JWT
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = components.build(root)
    assert isinstance(result, components.Components)

    # Verify schemas
    assert result.schemas is not None
    schema_keys = {k.value for k in result.schemas.value.keys()}
    assert schema_keys == {"Error", "Pet"}

    # Verify responses
    assert result.responses is not None
    response_keys = {k.value for k in result.responses.value.keys()}
    assert response_keys == {"NotFound", "Unauthorized"}

    # Verify parameters
    assert result.parameters is not None
    param_keys = {k.value for k in result.parameters.value.keys()}
    assert param_keys == {"limitParam"}

    # Verify security schemes
    assert result.security_schemes is not None
    ss_keys = {k.value for k in result.security_schemes.value.keys()}
    assert ss_keys == {"bearerAuth"}


def test_build_preserves_order():
    """Test that component order is preserved."""
    yaml_content = textwrap.dedent(
        """
        schemas:
          Alpha:
            type: object
          Beta:
            type: object
          Gamma:
            type: object
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = components.build(root)
    assert isinstance(result, components.Components)

    assert result.schemas is not None
    schema_keys = [k.value for k in result.schemas.value.keys()]
    assert schema_keys == ["Alpha", "Beta", "Gamma"]


def test_build_with_path_items():
    """Test building Components with pathItems field (new in OpenAPI 3.1)."""
    yaml_content = textwrap.dedent(
        """
        pathItems:
          /users:
            get:
              summary: List users
              responses:
                '200':
                  description: Success
          /products:
            post:
              summary: Create product
              responses:
                '201':
                  description: Created
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = components.build(root)
    assert isinstance(result, components.Components)

    assert result.path_items is not None
    path_item_keys = {k.value for k in result.path_items.value.keys()}
    assert path_item_keys == {"/users", "/products"}

    # Verify path item objects are built
    for path_item_obj in result.path_items.value.values():
        assert isinstance(path_item_obj, PathItem)


def test_build_with_mixed_components_including_path_items():
    """Test building Components with multiple fields including pathItems."""
    yaml_content = textwrap.dedent(
        """
        schemas:
          User:
            type: object
        pathItems:
          /users:
            get:
              summary: List users
              responses:
                '200':
                  description: Success
        responses:
          NotFound:
            description: Not found
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = components.build(root)
    assert isinstance(result, components.Components)

    assert result.schemas is not None
    assert result.path_items is not None
    assert result.responses is not None

    schema_keys = {k.value for k in result.schemas.value.keys()}
    assert schema_keys == {"User"}

    path_item_keys = {k.value for k in result.path_items.value.keys()}
    assert path_item_keys == {"/users"}

    response_keys = {k.value for k in result.responses.value.keys()}
    assert response_keys == {"NotFound"}


def test_build_with_path_items_empty_object():
    """Test building Components with empty pathItems object."""
    yaml_content = textwrap.dedent(
        """
        pathItems: {}
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = components.build(root)
    assert isinstance(result, components.Components)

    assert result.path_items is not None
    assert len(result.path_items.value) == 0


def test_build_with_path_items_preserves_order():
    """Test that pathItems preserve order."""
    yaml_content = textwrap.dedent(
        """
        pathItems:
          /alpha:
            get:
              responses:
                '200':
                  description: OK
          /beta:
            get:
              responses:
                '200':
                  description: OK
          /gamma:
            get:
              responses:
                '200':
                  description: OK
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = components.build(root)
    assert isinstance(result, components.Components)

    assert result.path_items is not None
    path_item_keys = [k.value for k in result.path_items.value.keys()]
    assert path_item_keys == ["/alpha", "/beta", "/gamma"]


def test_build_with_path_items_invalid_type():
    """Test building Components with pathItems as invalid type (preserves data)."""
    yaml_content = textwrap.dedent(
        """
        pathItems: "not a mapping"
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = components.build(root)
    assert isinstance(result, components.Components)

    # Should preserve the invalid value
    assert result.path_items is not None
    assert result.path_items.value == "not a mapping"
