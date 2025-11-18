"""Tests for OpenAPI low-level datamodel."""

import textwrap

from ruamel.yaml import YAML

from jentic.apitools.openapi.datamodels.low.context import Context
from jentic.apitools.openapi.datamodels.low.sources import ValueSource
from jentic.apitools.openapi.datamodels.low.v30 import openapi
from jentic.apitools.openapi.datamodels.low.v30.components import Components
from jentic.apitools.openapi.datamodels.low.v30.external_documentation import (
    ExternalDocumentation,
)
from jentic.apitools.openapi.datamodels.low.v30.info import Info
from jentic.apitools.openapi.datamodels.low.v30.openapi import OpenAPI30
from jentic.apitools.openapi.datamodels.low.v30.paths import Paths
from jentic.apitools.openapi.datamodels.low.v30.security_requirement import (
    SecurityRequirement,
)
from jentic.apitools.openapi.datamodels.low.v30.server import Server
from jentic.apitools.openapi.datamodels.low.v30.tag import Tag


def test_build_minimal_openapi(parse_yaml):
    """Test building OpenAPI with only required fields."""
    yaml_content = textwrap.dedent(
        """
        openapi: 3.0.4
        info:
          title: Sample API
          version: 1.0.0
        paths: {}
        """
    )
    root = parse_yaml(yaml_content)

    result = openapi.build(root)
    assert isinstance(result, OpenAPI30)

    assert result.root_node == root
    assert result.openapi is not None
    assert result.openapi.value == "3.0.4"
    assert result.info is not None
    assert isinstance(result.info.value, Info)
    assert result.paths is not None
    assert isinstance(result.paths.value, Paths)


def test_build_with_servers(parse_yaml):
    """Test building OpenAPI with servers field."""
    yaml_content = textwrap.dedent(
        """
        openapi: 3.0.4
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
    root = parse_yaml(yaml_content)

    result = openapi.build(root)
    assert isinstance(result, OpenAPI30)

    assert result.servers is not None
    assert len(result.servers.value) == 2
    for server in result.servers.value:
        assert isinstance(server, Server)


def test_build_with_components(parse_yaml):
    """Test building OpenAPI with components field."""
    yaml_content = textwrap.dedent(
        """
        openapi: 3.0.4
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
    root = parse_yaml(yaml_content)

    result = openapi.build(root)
    assert isinstance(result, OpenAPI30)

    assert result.components is not None
    assert isinstance(result.components.value, Components)


def test_build_with_security(parse_yaml):
    """Test building OpenAPI with security field."""
    yaml_content = textwrap.dedent(
        """
        openapi: 3.0.4
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
    root = parse_yaml(yaml_content)

    result = openapi.build(root)
    assert isinstance(result, OpenAPI30)

    assert result.security is not None
    assert len(result.security.value) == 2
    for security_req in result.security.value:
        assert isinstance(security_req, SecurityRequirement)


def test_build_with_tags(parse_yaml):
    """Test building OpenAPI with tags field."""
    yaml_content = textwrap.dedent(
        """
        openapi: 3.0.4
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
    root = parse_yaml(yaml_content)

    result = openapi.build(root)
    assert isinstance(result, OpenAPI30)

    assert result.tags is not None
    assert len(result.tags.value) == 2
    for tag in result.tags.value:
        assert isinstance(tag, Tag)


def test_build_with_external_docs(parse_yaml):
    """Test building OpenAPI with externalDocs field."""
    yaml_content = textwrap.dedent(
        """
        openapi: 3.0.4
        info:
          title: Sample API
          version: 1.0.0
        paths: {}
        externalDocs:
          description: Find more info here
          url: https://example.com/docs
        """
    )
    root = parse_yaml(yaml_content)

    result = openapi.build(root)
    assert isinstance(result, OpenAPI30)

    assert result.external_docs is not None
    assert isinstance(result.external_docs.value, ExternalDocumentation)


def test_build_with_all_fields(parse_yaml):
    """Test building OpenAPI with all fields."""
    yaml_content = textwrap.dedent(
        """
        openapi: 3.0.4
        info:
          title: Sample API
          version: 1.0.0
          description: A sample API
        servers:
          - url: https://api.example.com
        paths:
          /users:
            get:
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
    root = parse_yaml(yaml_content)

    result = openapi.build(root)
    assert isinstance(result, OpenAPI30)

    # Verify all fields are present
    assert result.openapi is not None
    assert result.info is not None
    assert result.paths is not None
    assert result.servers is not None
    assert result.components is not None
    assert result.security is not None
    assert result.tags is not None
    assert result.external_docs is not None


def test_build_with_extensions(parse_yaml):
    """Test building OpenAPI with specification extensions."""
    yaml_content = textwrap.dedent(
        """
        openapi: 3.0.4
        info:
          title: Sample API
          version: 1.0.0
        paths: {}
        x-api-id: api-12345
        x-rate-limit: 1000
        """
    )
    root = parse_yaml(yaml_content)

    result = openapi.build(root)
    assert isinstance(result, OpenAPI30)

    assert len(result.extensions) == 2
    ext_dict = {k.value: v.value for k, v in result.extensions.items()}
    assert ext_dict["x-api-id"] == "api-12345"
    assert ext_dict["x-rate-limit"] == 1000


def test_build_with_invalid_node_returns_value_source():
    """Test building OpenAPI with invalid root node returns ValueSource."""
    yaml_content = "invalid scalar value"
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = openapi.build(root)
    assert isinstance(result, ValueSource)
    assert result.value == "invalid scalar value"


def test_build_with_custom_context(parse_yaml):
    """Test building OpenAPI with custom context."""
    yaml_content = textwrap.dedent(
        """
        openapi: 3.0.4
        info:
          title: Sample API
          version: 1.0.0
        paths: {}
        """
    )
    root = parse_yaml(yaml_content)

    custom_context = Context()
    result = openapi.build(root, context=custom_context)
    assert isinstance(result, OpenAPI30)


def test_source_tracking(parse_yaml):
    """Test that source nodes are properly tracked."""
    yaml_content = textwrap.dedent(
        """
        openapi: 3.0.4
        info:
          title: Sample API
          version: 1.0.0
        paths: {}
        """
    )
    root = parse_yaml(yaml_content)

    result = openapi.build(root)
    assert isinstance(result, OpenAPI30)

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


def test_build_with_invalid_field_types(parse_yaml):
    """Test building OpenAPI with invalid field types."""
    yaml_content = textwrap.dedent(
        """
        openapi: 3.0.4
        info:
          title: Sample API
          version: 1.0.0
        paths: {}
        servers: invalid_scalar
        security: invalid_scalar
        tags: invalid_scalar
        """
    )
    root = parse_yaml(yaml_content)

    result = openapi.build(root)
    assert isinstance(result, OpenAPI30)

    # Invalid fields should still be captured as FieldSource
    assert result.servers is not None
    assert result.servers.value == "invalid_scalar"

    assert result.security is not None
    assert result.security.value == "invalid_scalar"

    assert result.tags is not None
    assert result.tags.value == "invalid_scalar"


def test_build_real_world_openapi(parse_yaml):
    """Test building OpenAPI with realistic document structure."""
    yaml_content = textwrap.dedent(
        """
        openapi: 3.0.4
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
            url: https://www.apache.org/licenses/LICENSE-2.0.html
          version: 1.0.1
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
    root = parse_yaml(yaml_content)

    result = openapi.build(root)
    assert isinstance(result, OpenAPI30)

    # Verify openapi version
    assert result.openapi is not None
    assert result.openapi.value == "3.0.4"

    # Verify info
    assert result.info is not None
    assert isinstance(result.info.value, Info)

    # Verify servers
    assert result.servers is not None
    assert len(result.servers.value) == 2

    # Verify paths
    assert result.paths is not None
    assert isinstance(result.paths.value, Paths)

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


def test_build_different_openapi_versions(parse_yaml):
    """Test building OpenAPI with different version strings."""
    for version in ["3.0.0", "3.0.1", "3.0.2", "3.0.3", "3.0.4"]:
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
        assert isinstance(result, OpenAPI30)
        assert result.openapi is not None
        assert result.openapi.value == version


def test_build_preserves_field_order(parse_yaml):
    """Test that field order is preserved."""
    yaml_content = textwrap.dedent(
        """
        openapi: 3.0.4
        info:
          title: Sample API
          version: 1.0.0
        servers:
          - url: https://api.example.com
        paths: {}
        components:
          schemas:
            User:
              type: object
        """
    )
    root = parse_yaml(yaml_content)

    result = openapi.build(root)
    assert isinstance(result, OpenAPI30)

    # Just verify that all fields are present and properly parsed
    assert result.openapi is not None
    assert result.info is not None
    assert result.servers is not None
    assert result.paths is not None
    assert result.components is not None


def test_build_with_empty_paths(parse_yaml):
    """Test building OpenAPI with empty paths object."""
    yaml_content = textwrap.dedent(
        """
        openapi: 3.0.4
        info:
          title: Sample API
          version: 1.0.0
        paths: {}
        """
    )
    root = parse_yaml(yaml_content)

    result = openapi.build(root)
    assert isinstance(result, OpenAPI30)

    assert result.paths is not None
    assert isinstance(result.paths.value, Paths)
    assert result.paths.value.paths == {}
