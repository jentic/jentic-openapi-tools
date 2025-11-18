"""Tests for Callback low-level datamodel."""

import textwrap

from ruamel.yaml import YAML

from jentic.apitools.openapi.datamodels.low.context import Context
from jentic.apitools.openapi.datamodels.low.sources import KeySource, ValueSource
from jentic.apitools.openapi.datamodels.low.v30 import callback
from jentic.apitools.openapi.datamodels.low.v30.reference import Reference


def test_build_with_single_expression(parse_yaml):
    """Test building Callback with single expression."""
    yaml_content = textwrap.dedent(
        """
        '{$request.body#/callbackUrl}':
          post:
            requestBody:
              required: true
            responses:
              '200':
                description: callback processed
        """
    )
    root = parse_yaml(yaml_content)

    result = callback.build(root)
    assert isinstance(result, callback.Callback)

    assert result.root_node == root
    assert len(result.path_items) == 1
    assert result.extensions == {}

    # Check the expression key
    expression_keys = {k.value for k in result.path_items.keys()}
    assert "{$request.body#/callbackUrl}" in expression_keys


def test_build_with_multiple_expressions(parse_yaml):
    """Test building Callback with multiple expressions."""
    yaml_content = textwrap.dedent(
        """
        '{$request.body#/callbackUrl}':
          post:
            responses:
              '200':
                description: callback processed
        '{$request.body#/webhookUrl}':
          post:
            responses:
              '200':
                description: webhook processed
        """
    )
    root = parse_yaml(yaml_content)

    result = callback.build(root)
    assert isinstance(result, callback.Callback)

    assert len(result.path_items) == 2
    expression_keys = {k.value for k in result.path_items.keys()}
    assert expression_keys == {"{$request.body#/callbackUrl}", "{$request.body#/webhookUrl}"}


def test_build_with_extensions(parse_yaml):
    """Test building Callback with specification extensions."""
    yaml_content = textwrap.dedent(
        """
        '{$request.body#/callbackUrl}':
          post:
            responses:
              '200':
                description: callback processed
        x-callback-timeout: 30
        x-callback-retries: 3
        """
    )
    root = parse_yaml(yaml_content)

    result = callback.build(root)
    assert isinstance(result, callback.Callback)

    assert len(result.path_items) == 1
    assert len(result.extensions) == 2
    ext_dict = {k.value: v.value for k, v in result.extensions.items()}
    assert ext_dict["x-callback-timeout"] == 30
    assert ext_dict["x-callback-retries"] == 3


def test_build_with_url_expression(parse_yaml):
    """Test building Callback with URL expression."""
    yaml_content = textwrap.dedent(
        """
        'https://example.com/callback':
          post:
            requestBody:
              content:
                application/json:
                  schema:
                    type: object
            responses:
              '200':
                description: success
        """
    )
    root = parse_yaml(yaml_content)

    result = callback.build(root)
    assert isinstance(result, callback.Callback)

    assert len(result.path_items) == 1
    expression_keys = {k.value for k in result.path_items.keys()}
    assert "https://example.com/callback" in expression_keys


def test_build_with_complex_expression(parse_yaml):
    """Test building Callback with complex runtime expression."""
    yaml_content = textwrap.dedent(
        """
        '{$request.header.X-Callback-Url}':
          post:
            responses:
              '200':
                description: callback received
        '{$request.query.callback}':
          get:
            responses:
              '200':
                description: callback received
        """
    )
    root = parse_yaml(yaml_content)

    result = callback.build(root)
    assert isinstance(result, callback.Callback)

    assert len(result.path_items) == 2
    expression_keys = {k.value for k in result.path_items.keys()}
    assert "{$request.header.X-Callback-Url}" in expression_keys
    assert "{$request.query.callback}" in expression_keys


def test_build_with_empty_object(parse_yaml):
    """Test building Callback from empty YAML object."""
    yaml_content = "{}"
    root = parse_yaml(yaml_content)

    result = callback.build(root)
    assert isinstance(result, callback.Callback)

    assert result.root_node == root
    assert result.path_items == {}
    assert result.extensions == {}


def test_build_with_invalid_node_returns_value_source():
    """Test that build returns ValueSource for non-mapping nodes."""
    # Use raw YAML() for testing invalid node types (non-mappings)
    yaml_parser = YAML()

    # Scalar node
    scalar_root = yaml_parser.compose("not-a-callback-object")
    result = callback.build(scalar_root)
    assert isinstance(result, ValueSource)
    assert result.value == "not-a-callback-object"
    assert result.value_node == scalar_root

    # Sequence node
    sequence_root = yaml_parser.compose("['expression1', 'expression2']")
    result = callback.build(sequence_root)
    assert isinstance(result, ValueSource)
    assert result.value == ["expression1", "expression2"]
    assert result.value_node == sequence_root


def test_build_with_custom_context(parse_yaml):
    """Test building Callback with a custom context."""
    yaml_content = textwrap.dedent(
        """
        '{$request.body#/callbackUrl}':
          post:
            responses:
              '200':
                description: callback processed
        """
    )
    root = parse_yaml(yaml_content)

    custom_context = Context()
    result = callback.build(root, context=custom_context)
    assert isinstance(result, callback.Callback)

    assert len(result.path_items) == 1


def test_source_tracking(parse_yaml):
    """Test that source location information is preserved."""
    yaml_content = textwrap.dedent(
        """
        '{$request.body#/callbackUrl}':
          post:
            responses:
              '200':
                description: callback processed
        x-custom: value
        """
    )
    root = parse_yaml(yaml_content)

    result = callback.build(root)
    assert isinstance(result, callback.Callback)

    # Check expression key source tracking
    for key_source in result.path_items.keys():
        assert isinstance(key_source, KeySource)
        assert key_source.key_node is not None

    # Check expression value is now a PathItem object
    from jentic.apitools.openapi.datamodels.low.v30.path_item import PathItem

    for path_item in result.path_items.values():
        assert isinstance(path_item, PathItem)
        assert path_item.root_node is not None

    # Check extension source tracking
    for key_source, value_source in result.extensions.items():
        assert isinstance(key_source, KeySource)
        assert key_source.key_node is not None
        assert isinstance(value_source, ValueSource)
        assert value_source.value_node is not None

    # Check line numbers are available
    first_key = next(iter(result.path_items.keys()))
    assert hasattr(first_key.key_node.start_mark, "line")


def test_build_preserves_path_item_structure(parse_yaml):
    """Test that path item structure is properly built as PathItem object."""
    yaml_content = textwrap.dedent(
        """
        '{$request.body#/callbackUrl}':
          post:
            summary: Callback endpoint
            requestBody:
              required: true
              content:
                application/json:
                  schema:
                    type: object
                    properties:
                      status:
                        type: string
            responses:
              '200':
                description: callback successfully processed
              '400':
                description: invalid callback data
        """
    )
    root = parse_yaml(yaml_content)

    result = callback.build(root)
    assert isinstance(result, callback.Callback)

    # Get the path item
    from jentic.apitools.openapi.datamodels.low.v30.path_item import PathItem

    key = next(iter(result.path_items.keys()))
    path_item = result.path_items[key]

    # Verify it's a PathItem object with proper structure
    from jentic.apitools.openapi.datamodels.low.v30.operation import Operation

    assert isinstance(path_item, PathItem)
    assert path_item.post is not None
    assert isinstance(path_item.post.value, Operation)
    # Verify the operation has responses
    assert path_item.post.value.responses is not None


def test_build_real_world_webhook_callback(parse_yaml):
    """Test a complete real-world webhook callback."""
    yaml_content = textwrap.dedent(
        """
        '{$request.body#/webhookUrl}':
          post:
            requestBody:
              description: Webhook notification payload
              required: true
              content:
                application/json:
                  schema:
                    type: object
                    properties:
                      event:
                        type: string
                      data:
                        type: object
            responses:
              '200':
                description: Webhook received successfully
              '401':
                description: Unauthorized
              '500':
                description: Server error
        x-webhook-secret-header: X-Webhook-Signature
        """
    )
    root = parse_yaml(yaml_content)

    result = callback.build(root)
    assert isinstance(result, callback.Callback)

    assert len(result.path_items) == 1
    assert len(result.extensions) == 1

    # Check extension
    ext_dict = {k.value: v.value for k, v in result.extensions.items()}
    assert ext_dict["x-webhook-secret-header"] == "X-Webhook-Signature"


def test_build_with_multiple_http_methods(parse_yaml):
    """Test callback with multiple HTTP methods in path item."""
    yaml_content = textwrap.dedent(
        """
        '{$request.body#/callbackUrl}':
          post:
            responses:
              '200':
                description: POST callback processed
          put:
            responses:
              '200':
                description: PUT callback processed
        """
    )
    root = parse_yaml(yaml_content)

    result = callback.build(root)
    assert isinstance(result, callback.Callback)

    # Get the path item
    from jentic.apitools.openapi.datamodels.low.v30.path_item import PathItem

    key = next(iter(result.path_items.keys()))
    path_item = result.path_items[key]

    # Verify it's a PathItem with both methods present
    assert isinstance(path_item, PathItem)
    assert path_item.post is not None
    assert path_item.put is not None


def test_build_with_expression_using_response(parse_yaml):
    """Test callback expression referencing response data."""
    yaml_content = textwrap.dedent(
        """
        '{$response.body#/callbackUrl}':
          post:
            responses:
              '200':
                description: callback received
        """
    )
    root = parse_yaml(yaml_content)

    result = callback.build(root)
    assert isinstance(result, callback.Callback)

    expression_keys = {k.value for k in result.path_items.keys()}
    assert "{$response.body#/callbackUrl}" in expression_keys


def test_build_preserves_order(parse_yaml):
    """Test that expression order is preserved during parsing."""
    yaml_content = textwrap.dedent(
        """
        '{$request.body#/url1}':
          post:
            responses:
              '200':
                description: callback 1
        '{$request.body#/url2}':
          post:
            responses:
              '200':
                description: callback 2
        '{$request.body#/url3}':
          post:
            responses:
              '200':
                description: callback 3
        """
    )
    root = parse_yaml(yaml_content)

    result = callback.build(root)
    assert isinstance(result, callback.Callback)

    # Dict should maintain insertion order (Python 3.7+)
    expression_keys_list = [k.value for k in result.path_items.keys()]
    assert expression_keys_list == [
        "{$request.body#/url1}",
        "{$request.body#/url2}",
        "{$request.body#/url3}",
    ]


def test_build_with_all_fields(parse_yaml):
    """Test building Callback with expressions and extensions."""
    yaml_content = textwrap.dedent(
        """
        '{$request.body#/callbackUrl}':
          post:
            responses:
              '200':
                description: success
        '{$request.body#/webhookUrl}':
          post:
            responses:
              '200':
                description: success
        x-timeout: 30
        x-retries: 3
        x-async: true
        """
    )
    root = parse_yaml(yaml_content)

    result = callback.build(root)
    assert isinstance(result, callback.Callback)

    assert len(result.path_items) == 2
    assert len(result.extensions) == 3

    expression_keys = {k.value for k in result.path_items.keys()}
    assert expression_keys == {"{$request.body#/callbackUrl}", "{$request.body#/webhookUrl}"}

    ext_dict = {k.value: v.value for k, v in result.extensions.items()}
    assert ext_dict["x-timeout"] == 30
    assert ext_dict["x-retries"] == 3
    assert ext_dict["x-async"] is True


def test_build_callback_or_reference_with_callback(parse_yaml):
    """Test build_callback_or_reference with a Callback object."""
    yaml_content = textwrap.dedent(
        """
        '{$request.body#/callbackUrl}':
          post:
            responses:
              '200':
                description: callback processed
        """
    )
    root = parse_yaml(yaml_content)

    result = callback.build_callback_or_reference(root, Context())
    assert isinstance(result, callback.Callback)
    assert len(result.path_items) == 1


def test_build_callback_or_reference_with_reference(parse_yaml):
    """Test build_callback_or_reference with a Reference object."""
    yaml_content = textwrap.dedent(
        """
        $ref: '#/components/callbacks/WebhookCallback'
        """
    )
    root = parse_yaml(yaml_content)

    result = callback.build_callback_or_reference(root, Context())
    assert isinstance(result, Reference)
    assert result.ref is not None
    assert result.ref.value == "#/components/callbacks/WebhookCallback"


def test_build_callback_or_reference_with_invalid_data():
    """Test build_callback_or_reference with invalid data."""
    # Use raw YAML() for testing invalid node types (non-mappings)
    yaml_parser = YAML()

    # Scalar node
    scalar_root = yaml_parser.compose("not-a-callback")
    result = callback.build_callback_or_reference(scalar_root, Context())
    assert isinstance(result, ValueSource)
    assert result.value == "not-a-callback"
