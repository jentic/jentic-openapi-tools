"""Tests for Paths low-level datamodel."""

import textwrap

from ruamel.yaml import YAML

from jentic.apitools.openapi.datamodels.low.context import Context
from jentic.apitools.openapi.datamodels.low.sources import KeySource, ValueSource
from jentic.apitools.openapi.datamodels.low.v31 import paths
from jentic.apitools.openapi.datamodels.low.v31.path_item import PathItem


def test_build_with_single_path():
    """Test building Paths with single path."""
    yaml_content = textwrap.dedent(
        """
        /users:
          get:
            summary: Get all users
            responses:
              '200':
                description: Success
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = paths.build(root)
    assert isinstance(result, paths.Paths)

    assert result.root_node == root
    assert len(result.paths) == 1
    assert result.extensions == {}

    # Check the path key
    path_keys = {k.value for k in result.paths.keys()}
    assert "/users" in path_keys


def test_build_with_multiple_paths():
    """Test building Paths with multiple path entries."""
    yaml_content = textwrap.dedent(
        """
        /users:
          get:
            summary: Get all users
            responses:
              '200':
                description: Success
        /users/{id}:
          get:
            summary: Get user by ID
            responses:
              '200':
                description: Success
        /products:
          get:
            summary: Get all products
            responses:
              '200':
                description: Success
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = paths.build(root)
    assert isinstance(result, paths.Paths)

    assert len(result.paths) == 3
    path_keys = {k.value for k in result.paths.keys()}
    assert path_keys == {"/users", "/users/{id}", "/products"}


def test_build_with_path_parameters():
    """Test building Paths with path parameters (templating)."""
    yaml_content = textwrap.dedent(
        """
        /users/{userId}/posts/{postId}:
          get:
            summary: Get user post
            parameters:
              - name: userId
                in: path
                required: true
                schema:
                  type: integer
              - name: postId
                in: path
                required: true
                schema:
                  type: integer
            responses:
              '200':
                description: Success
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = paths.build(root)
    assert isinstance(result, paths.Paths)

    assert len(result.paths) == 1
    path_keys = {k.value for k in result.paths.keys()}
    assert "/users/{userId}/posts/{postId}" in path_keys


def test_build_with_extensions():
    """Test building Paths with specification extensions."""
    yaml_content = textwrap.dedent(
        """
        /users:
          get:
            summary: Get all users
            responses:
              '200':
                description: Success
        x-api-version: v1
        x-rate-limit: 1000
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = paths.build(root)
    assert isinstance(result, paths.Paths)

    assert len(result.paths) == 1
    assert len(result.extensions) == 2
    ext_dict = {k.value: v.value for k, v in result.extensions.items()}
    assert ext_dict["x-api-version"] == "v1"
    assert ext_dict["x-rate-limit"] == 1000


def test_build_with_all_http_methods():
    """Test building Paths with multiple HTTP methods on same path."""
    yaml_content = textwrap.dedent(
        """
        /users:
          get:
            summary: Get users
            responses:
              '200':
                description: Success
          post:
            summary: Create user
            responses:
              '201':
                description: Created
          put:
            summary: Update users
            responses:
              '200':
                description: Success
          delete:
            summary: Delete users
            responses:
              '204':
                description: No content
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = paths.build(root)
    assert isinstance(result, paths.Paths)

    assert len(result.paths) == 1
    path_item = list(result.paths.values())[0]
    assert isinstance(path_item, PathItem)


def test_build_with_empty_object():
    """Test building Paths from empty YAML object."""
    yaml_content = "{}"
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = paths.build(root)
    assert isinstance(result, paths.Paths)

    assert result.paths == {}
    assert result.extensions == {}


def test_build_with_invalid_node_returns_value_source():
    """Test building Paths with invalid root node returns ValueSource."""
    yaml_content = "invalid scalar value"
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = paths.build(root)
    assert isinstance(result, ValueSource)
    assert result.value == "invalid scalar value"


def test_build_with_custom_context():
    """Test building Paths with custom context."""
    yaml_content = textwrap.dedent(
        """
        /users:
          get:
            responses:
              '200':
                description: Success
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    custom_context = Context()
    result = paths.build(root, context=custom_context)
    assert isinstance(result, paths.Paths)
    assert len(result.paths) == 1


def test_source_tracking():
    """Test that source nodes are properly tracked."""
    yaml_content = textwrap.dedent(
        """
        /users:
          get:
            responses:
              '200':
                description: Success
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = paths.build(root)
    assert isinstance(result, paths.Paths)

    # Check root node is tracked
    assert result.root_node == root

    # Check path keys track their nodes
    for key_source in result.paths.keys():
        assert isinstance(key_source, KeySource)
        assert key_source.key_node is not None


def test_build_with_nested_paths():
    """Test building Paths with nested path hierarchy."""
    yaml_content = textwrap.dedent(
        """
        /api:
          get:
            summary: API root
            responses:
              '200':
                description: Success
        /api/v1:
          get:
            summary: API v1
            responses:
              '200':
                description: Success
        /api/v1/users:
          get:
            summary: Get users
            responses:
              '200':
                description: Success
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = paths.build(root)
    assert isinstance(result, paths.Paths)

    assert len(result.paths) == 3
    path_keys = {k.value for k in result.paths.keys()}
    assert path_keys == {"/api", "/api/v1", "/api/v1/users"}


def test_build_with_path_having_parameters_object():
    """Test building Paths with path having common parameters."""
    yaml_content = textwrap.dedent(
        """
        /users/{id}:
          parameters:
            - name: id
              in: path
              required: true
              schema:
                type: integer
          get:
            summary: Get user
            responses:
              '200':
                description: Success
          put:
            summary: Update user
            responses:
              '200':
                description: Success
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = paths.build(root)
    assert isinstance(result, paths.Paths)

    assert len(result.paths) == 1
    path_item = list(result.paths.values())[0]
    assert isinstance(path_item, PathItem)


def test_build_real_world_rest_api():
    """Test building Paths with realistic REST API structure."""
    yaml_content = textwrap.dedent(
        """
        /pets:
          get:
            summary: List all pets
            operationId: listPets
            tags:
              - pets
            parameters:
              - name: limit
                in: query
                schema:
                  type: integer
            responses:
              '200':
                description: A paged array of pets
        /pets/{petId}:
          get:
            summary: Info for a specific pet
            operationId: showPetById
            tags:
              - pets
            parameters:
              - name: petId
                in: path
                required: true
                schema:
                  type: string
            responses:
              '200':
                description: Expected response to a valid request
        x-api-id: pet-store-api
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = paths.build(root)
    assert isinstance(result, paths.Paths)

    assert len(result.paths) == 2
    path_keys = {k.value for k in result.paths.keys()}
    assert path_keys == {"/pets", "/pets/{petId}"}
    assert len(result.extensions) == 1
    ext_dict = {k.value: v.value for k, v in result.extensions.items()}
    assert ext_dict["x-api-id"] == "pet-store-api"


def test_build_preserves_order():
    """Test that path order is preserved."""
    yaml_content = textwrap.dedent(
        """
        /alpha:
          get:
            responses:
              '200':
                description: Success
        /beta:
          get:
            responses:
              '200':
                description: Success
        /gamma:
          get:
            responses:
              '200':
                description: Success
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = paths.build(root)
    assert isinstance(result, paths.Paths)

    path_keys = [k.value for k in result.paths.keys()]
    assert path_keys == ["/alpha", "/beta", "/gamma"]


def test_build_requires_forward_slash_prefix():
    """Test that path keys must begin with forward slash (/)."""
    yaml_content = textwrap.dedent(
        """
        /users:
          get:
            responses:
              '200':
                description: Success
        invalid-path-no-slash:
          get:
            responses:
              '200':
                description: Success
        another_invalid:
          post:
            responses:
              '201':
                description: Created
        x-custom-extension: value
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = paths.build(root)
    assert isinstance(result, paths.Paths)

    # Only paths starting with "/" should be included
    path_keys = {k.value for k in result.paths.keys()}
    assert path_keys == {"/users"}

    # Invalid paths (without /) should be ignored, not added to paths
    assert "invalid-path-no-slash" not in path_keys
    assert "another_invalid" not in path_keys

    # Extensions should still be extracted
    assert len(result.extensions) == 1
    ext_dict = {k.value: v.value for k, v in result.extensions.items()}
    assert ext_dict["x-custom-extension"] == "value"


def test_build_with_only_invalid_paths():
    """Test that Paths with only invalid path keys (no /) results in empty paths."""
    yaml_content = textwrap.dedent(
        """
        invalid-path:
          get:
            responses:
              '200':
                description: Success
        another-invalid:
          post:
            responses:
              '201':
                description: Created
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = paths.build(root)
    assert isinstance(result, paths.Paths)

    # No valid paths should be extracted
    assert result.paths == {}
    assert result.extensions == {}


def test_build_with_numeric_keys():
    """Test that numeric keys are ignored (don't cause errors)."""
    yaml_content = textwrap.dedent(
        """
        123:
          get:
            responses:
              '200':
                description: Success
        456.78:
          post:
            responses:
              '201':
                description: Created
        /users:
          get:
            responses:
              '200':
                description: Success
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = paths.build(root)
    assert isinstance(result, paths.Paths)

    # Only the valid path (starting with /) should be included
    path_keys = {k.value for k in result.paths.keys()}
    assert path_keys == {"/users"}

    # Numeric keys should be ignored
    assert len(result.paths) == 1
