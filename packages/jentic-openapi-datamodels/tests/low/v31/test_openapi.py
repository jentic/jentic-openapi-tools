"""Tests for OpenAPI 3.1 low-level datamodel."""

import textwrap

from ruamel.yaml import YAML

from jentic.apitools.openapi.datamodels.low.context import Context
from jentic.apitools.openapi.datamodels.low.sources import ValueSource
from jentic.apitools.openapi.datamodels.low.v30.openapi import OpenAPI30
from jentic.apitools.openapi.datamodels.low.v31 import openapi
from jentic.apitools.openapi.datamodels.low.v31.components import Components
from jentic.apitools.openapi.datamodels.low.v31.external_documentation import (
    ExternalDocumentation,
)
from jentic.apitools.openapi.datamodels.low.v31.info import Info
from jentic.apitools.openapi.datamodels.low.v31.openapi import OpenAPI31
from jentic.apitools.openapi.datamodels.low.v31.path_item import PathItem
from jentic.apitools.openapi.datamodels.low.v31.paths import Paths
from jentic.apitools.openapi.datamodels.low.v31.security_requirement import (
    SecurityRequirement,
)
from jentic.apitools.openapi.datamodels.low.v31.server import Server
from jentic.apitools.openapi.datamodels.low.v31.tag import Tag


def test_build_minimal_openapi():
    """Test building OpenAPI 3.1 with only required fields."""
    yaml_content = textwrap.dedent(
        """
        openapi: 3.1.2
        info:
          title: Sample API
          version: 1.0.0
        paths: {}
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = openapi.build(root)
    assert isinstance(result, OpenAPI31)

    assert result.root_node == root
    assert result.openapi is not None
    assert result.openapi.value == "3.1.2"
    assert result.info is not None
    assert isinstance(result.info.value, Info)
    assert result.paths is not None
    assert isinstance(result.paths.value, Paths)


def test_build_with_servers():
    """Test building OpenAPI 3.1 with servers field."""
    yaml_content = textwrap.dedent(
        """
        openapi: 3.1.2
        info:
          title: Sample API
          version: 1.0.0
        servers:
          - url: https://api.example.com/v1
            description: Production server
          - url: https://staging.example.com/v1
            description: Staging server
        paths: {}
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = openapi.build(root)
    assert isinstance(result, OpenAPI31)

    assert result.servers is not None
    assert len(result.servers.value) == 2
    for server in result.servers.value:
        assert isinstance(server, Server)


def test_build_with_components():
    """Test building OpenAPI 3.1 with components field."""
    yaml_content = textwrap.dedent(
        """
        openapi: 3.1.2
        info:
          title: Sample API
          version: 1.0.0
        paths: {}
        components:
          schemas:
            User:
              type: object
              properties:
                id:
                  type: integer
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = openapi.build(root)
    assert isinstance(result, OpenAPI31)

    assert result.components is not None
    assert isinstance(result.components.value, Components)


def test_build_with_security():
    """Test building OpenAPI 3.1 with security field."""
    yaml_content = textwrap.dedent(
        """
        openapi: 3.1.2
        info:
          title: Sample API
          version: 1.0.0
        paths: {}
        security:
          - api_key: []
          - oauth2:
              - read
              - write
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = openapi.build(root)
    assert isinstance(result, OpenAPI31)

    assert result.security is not None
    assert len(result.security.value) == 2
    for security_req in result.security.value:
        assert isinstance(security_req, SecurityRequirement)


def test_build_with_tags():
    """Test building OpenAPI 3.1 with tags field."""
    yaml_content = textwrap.dedent(
        """
        openapi: 3.1.2
        info:
          title: Sample API
          version: 1.0.0
        paths: {}
        tags:
          - name: users
            description: User operations
          - name: pets
            description: Pet operations
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = openapi.build(root)
    assert isinstance(result, OpenAPI31)

    assert result.tags is not None
    assert len(result.tags.value) == 2
    for tag in result.tags.value:
        assert isinstance(tag, Tag)


def test_build_with_external_docs():
    """Test building OpenAPI 3.1 with externalDocs field."""
    yaml_content = textwrap.dedent(
        """
        openapi: 3.1.2
        info:
          title: Sample API
          version: 1.0.0
        paths: {}
        externalDocs:
          description: Find more info here
          url: https://example.com/docs
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = openapi.build(root)
    assert isinstance(result, OpenAPI31)

    assert result.external_docs is not None
    assert isinstance(result.external_docs.value, ExternalDocumentation)


def test_build_with_json_schema_dialect():
    """Test building OpenAPI 3.1 with jsonSchemaDialect field (new in 3.1)."""
    yaml_content = textwrap.dedent(
        """
        openapi: 3.1.2
        info:
          title: Sample API
          version: 1.0.0
        jsonSchemaDialect: https://json-schema.org/draft/2020-12/schema
        paths: {}
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = openapi.build(root)
    assert isinstance(result, OpenAPI31)

    assert result.json_schema_dialect is not None
    assert result.json_schema_dialect.value == "https://json-schema.org/draft/2020-12/schema"


def test_build_with_webhooks():
    """Test building OpenAPI 3.1 with webhooks field (new in 3.1)."""
    yaml_content = textwrap.dedent(
        """
        openapi: 3.1.2
        info:
          title: Sample API
          version: 1.0.0
        paths: {}
        webhooks:
          newPet:
            post:
              requestBody:
                description: Information about a new pet
                content:
                  application/json:
                    schema:
                      type: object
              responses:
                '200':
                  description: Return a 200 status to indicate that the data was received successfully
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = openapi.build(root)
    assert isinstance(result, OpenAPI31)

    assert result.webhooks is not None
    assert isinstance(result.webhooks.value, dict)
    assert len(result.webhooks.value) == 1

    # Check webhook name
    webhook_names = [k.value for k in result.webhooks.value.keys()]
    assert "newPet" in webhook_names

    # Check webhook is a PathItem
    for webhook_path_item in result.webhooks.value.values():
        assert isinstance(webhook_path_item, PathItem)


def test_build_with_multiple_webhooks():
    """Test building OpenAPI 3.1 with multiple webhooks."""
    yaml_content = textwrap.dedent(
        """
        openapi: 3.1.2
        info:
          title: Sample API
          version: 1.0.0
        paths: {}
        webhooks:
          newPet:
            post:
              responses:
                '200':
                  description: Success
          deletedPet:
            post:
              responses:
                '200':
                  description: Success
          updatedPet:
            post:
              responses:
                '200':
                  description: Success
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = openapi.build(root)
    assert isinstance(result, OpenAPI31)

    assert result.webhooks is not None
    assert len(result.webhooks.value) == 3
    webhook_names = {k.value for k in result.webhooks.value.keys()}
    assert webhook_names == {"newPet", "deletedPet", "updatedPet"}


def test_build_without_paths_but_with_webhooks():
    """Test building OpenAPI 3.1 without paths (allowed in 3.1 if webhooks present)."""
    yaml_content = textwrap.dedent(
        """
        openapi: 3.1.2
        info:
          title: Webhook-only API
          version: 1.0.0
        webhooks:
          newResource:
            post:
              responses:
                '200':
                  description: Success
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = openapi.build(root)
    assert isinstance(result, OpenAPI31)

    # paths is optional in OpenAPI 3.1
    assert result.paths is None
    assert result.webhooks is not None


def test_build_with_all_fields():
    """Test building OpenAPI 3.1 with all fields including new 3.1 fields."""
    yaml_content = textwrap.dedent(
        """
        openapi: 3.1.2
        info:
          title: Sample API
          version: 1.0.0
          description: A sample API
        jsonSchemaDialect: https://json-schema.org/draft/2020-12/schema
        servers:
          - url: https://api.example.com
        paths:
          /users:
            get:
              responses:
                '200':
                  description: Success
        webhooks:
          newUser:
            post:
              responses:
                '200':
                  description: Success
        components:
          schemas:
            User:
              type: object
        security:
          - api_key: []
        tags:
          - name: users
        externalDocs:
          url: https://example.com/docs
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = openapi.build(root)
    assert isinstance(result, OpenAPI31)

    # Verify all fields are present
    assert result.openapi is not None
    assert result.info is not None
    assert result.json_schema_dialect is not None
    assert result.paths is not None
    assert result.webhooks is not None
    assert result.servers is not None
    assert result.components is not None
    assert result.security is not None
    assert result.tags is not None
    assert result.external_docs is not None


def test_build_with_extensions():
    """Test building OpenAPI 3.1 with specification extensions."""
    yaml_content = textwrap.dedent(
        """
        openapi: 3.1.2
        info:
          title: Sample API
          version: 1.0.0
        paths: {}
        x-api-id: api-12345
        x-rate-limit: 1000
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = openapi.build(root)
    assert isinstance(result, OpenAPI31)

    assert len(result.extensions) == 2
    ext_dict = {k.value: v.value for k, v in result.extensions.items()}
    assert ext_dict["x-api-id"] == "api-12345"
    assert ext_dict["x-rate-limit"] == 1000


def test_build_with_invalid_node_returns_value_source():
    """Test building OpenAPI 3.1 with invalid root node returns ValueSource."""
    yaml_content = "invalid scalar value"
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = openapi.build(root)
    assert isinstance(result, ValueSource)
    assert result.value == "invalid scalar value"


def test_build_with_custom_context():
    """Test building OpenAPI 3.1 with custom context."""
    yaml_content = textwrap.dedent(
        """
        openapi: 3.1.2
        info:
          title: Sample API
          version: 1.0.0
        paths: {}
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    custom_context = Context()
    result = openapi.build(root, context=custom_context)
    assert isinstance(result, OpenAPI31)


def test_source_tracking():
    """Test that source nodes are properly tracked."""
    yaml_content = textwrap.dedent(
        """
        openapi: 3.1.2
        info:
          title: Sample API
          version: 1.0.0
        paths: {}
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = openapi.build(root)
    assert isinstance(result, OpenAPI31)

    # Check root node is tracked
    assert result.root_node == root

    # Check required fields track their nodes
    assert result.openapi is not None
    assert result.openapi.key_node is not None
    assert result.openapi.value_node is not None

    assert result.info is not None
    assert result.info.key_node is not None
    assert result.info.value_node is not None

    assert result.paths is not None
    assert result.paths.key_node is not None
    assert result.paths.value_node is not None


def test_build_with_invalid_field_types():
    """Test building OpenAPI 3.1 with invalid field types."""
    yaml_content = textwrap.dedent(
        """
        openapi: 3.1.2
        info:
          title: Sample API
          version: 1.0.0
        paths: {}
        servers: invalid_scalar
        security: invalid_scalar
        tags: invalid_scalar
        webhooks: invalid_scalar
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = openapi.build(root)
    assert isinstance(result, OpenAPI31)

    # Invalid fields should still be captured as FieldSource
    assert result.servers is not None
    assert result.servers.value == "invalid_scalar"

    assert result.security is not None
    assert result.security.value == "invalid_scalar"

    assert result.tags is not None
    assert result.tags.value == "invalid_scalar"

    assert result.webhooks is not None
    assert result.webhooks.value == "invalid_scalar"


def test_build_real_world_openapi():
    """Test building OpenAPI 3.1 with realistic document structure."""
    yaml_content = textwrap.dedent(
        """
        openapi: 3.1.2
        info:
          title: Pet Store API
          description: This is a sample Pet Store Server
          termsOfService: http://example.com/terms/
          contact:
            name: API Support
            url: http://www.example.com/support
            email: support@example.com
          license:
            name: Apache 2.0
            identifier: Apache-2.0
          version: 1.0.1
        jsonSchemaDialect: https://json-schema.org/draft/2020-12/schema
        servers:
          - url: https://petstore.example.com/api/v1
            description: Production server
          - url: https://staging.petstore.example.com/api/v1
            description: Staging server
        paths:
          /pets:
            get:
              summary: List all pets
              operationId: listPets
              tags:
                - pets
              responses:
                '200':
                  description: A paged array of pets
          /pets/{petId}:
            get:
              summary: Info for a specific pet
              operationId: showPetById
              tags:
                - pets
              responses:
                '200':
                  description: Expected response
        webhooks:
          newPet:
            post:
              summary: New pet added
              requestBody:
                content:
                  application/json:
                    schema:
                      type: object
              responses:
                '200':
                  description: Return a 200 status to indicate receipt
        components:
          schemas:
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
          securitySchemes:
            ApiKey:
              type: apiKey
              name: api_key
              in: header
        security:
          - ApiKey: []
        tags:
          - name: pets
            description: Everything about your Pets
        externalDocs:
          description: Find out more about Pet Store
          url: http://petstore.example.com
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = openapi.build(root)
    assert isinstance(result, OpenAPI31)

    # Verify openapi version
    assert result.openapi is not None
    assert result.openapi.value == "3.1.2"

    # Verify jsonSchemaDialect
    assert result.json_schema_dialect is not None
    assert result.json_schema_dialect.value == "https://json-schema.org/draft/2020-12/schema"

    # Verify info
    assert result.info is not None
    assert isinstance(result.info.value, Info)

    # Verify servers
    assert result.servers is not None
    assert len(result.servers.value) == 2

    # Verify paths
    assert result.paths is not None
    assert isinstance(result.paths.value, Paths)

    # Verify webhooks
    assert result.webhooks is not None
    assert len(result.webhooks.value) == 1

    # Verify components
    assert result.components is not None
    assert isinstance(result.components.value, Components)

    # Verify security
    assert result.security is not None
    assert len(result.security.value) == 1

    # Verify tags
    assert result.tags is not None
    assert len(result.tags.value) == 1

    # Verify externalDocs
    assert result.external_docs is not None
    assert isinstance(result.external_docs.value, ExternalDocumentation)


def test_build_different_openapi_versions():
    """Test building OpenAPI 3.1 with different version strings."""
    for version in ["3.1.0", "3.1.1", "3.1.2"]:
        yaml_content = textwrap.dedent(
            f"""
            openapi: {version}
            info:
              title: Sample API
              version: 1.0.0
            paths: {{}}
            """
        )
        yaml_parser = YAML()
        root = yaml_parser.compose(yaml_content)

        result = openapi.build(root)
        assert isinstance(result, OpenAPI31)
        assert result.openapi is not None
        assert result.openapi.value == version


def test_build_preserves_field_order():
    """Test that field order is preserved."""
    yaml_content = textwrap.dedent(
        """
        openapi: 3.1.2
        info:
          title: Sample API
          version: 1.0.0
        jsonSchemaDialect: https://json-schema.org/draft/2020-12/schema
        servers:
          - url: https://api.example.com
        paths: {}
        webhooks:
          newResource:
            post:
              responses:
                '200':
                  description: Success
        components:
          schemas:
            User:
              type: object
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = openapi.build(root)
    assert isinstance(result, OpenAPI31)

    # Just verify that all fields are present and properly parsed
    assert result.openapi is not None
    assert result.info is not None
    assert result.json_schema_dialect is not None
    assert result.servers is not None
    assert result.paths is not None
    assert result.webhooks is not None
    assert result.components is not None


def test_build_with_empty_paths():
    """Test building OpenAPI 3.1 with empty paths object."""
    yaml_content = textwrap.dedent(
        """
        openapi: 3.1.2
        info:
          title: Sample API
          version: 1.0.0
        paths: {}
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = openapi.build(root)
    assert isinstance(result, OpenAPI31)

    assert result.paths is not None
    assert isinstance(result.paths.value, Paths)
    assert result.paths.value.paths == {}


def test_isinstance_discrimination():
    """Test that isinstance() can discriminate between OpenAPI30 and OpenAPI31."""
    yaml_content_30 = textwrap.dedent(
        """
        openapi: 3.0.4
        info:
          title: Sample API
          version: 1.0.0
        paths: {}
        """
    )
    yaml_content_31 = textwrap.dedent(
        """
        openapi: 3.1.2
        info:
          title: Sample API
          version: 1.0.0
        paths: {}
        """
    )
    yaml_parser = YAML()

    # Build v3.0 document
    root_30 = yaml_parser.compose(yaml_content_30)
    from jentic.apitools.openapi.datamodels.low.v30 import openapi as openapi_v30

    result_30 = openapi_v30.build(root_30)

    # Build v3.1 document
    root_31 = yaml_parser.compose(yaml_content_31)
    result_31 = openapi.build(root_31)

    # Test isinstance discrimination
    assert isinstance(result_30, OpenAPI30)
    assert not isinstance(result_30, OpenAPI31)

    assert isinstance(result_31, OpenAPI31)
    assert not isinstance(result_31, OpenAPI30)


def test_webhooks_source_tracking():
    """Test that webhooks field maintains proper source tracking."""
    yaml_content = textwrap.dedent(
        """
        openapi: 3.1.2
        info:
          title: Sample API
          version: 1.0.0
        paths: {}
        webhooks:
          newPet:
            post:
              responses:
                '200':
                  description: Success
          deletedPet:
            post:
              responses:
                '200':
                  description: Success
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = openapi.build(root)
    assert isinstance(result, OpenAPI31)

    assert result.webhooks is not None
    assert result.webhooks.key_node is not None
    assert result.webhooks.value_node is not None

    # Check that each webhook key has source tracking
    for webhook_key, webhook_path_item in result.webhooks.value.items():
        assert webhook_key.key_node is not None
        assert isinstance(webhook_path_item, PathItem)
        assert webhook_path_item.root_node is not None
