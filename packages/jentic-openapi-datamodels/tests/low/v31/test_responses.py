"""Tests for Responses low-level datamodel."""

import textwrap

from ruamel.yaml import YAML

from jentic.apitools.openapi.datamodels.low.context import Context
from jentic.apitools.openapi.datamodels.low.sources import FieldSource, KeySource, ValueSource
from jentic.apitools.openapi.datamodels.low.v31 import responses
from jentic.apitools.openapi.datamodels.low.v31.reference import Reference
from jentic.apitools.openapi.datamodels.low.v31.response import Response


def test_build_with_single_response():
    """Test building Responses with single status code."""
    yaml_content = textwrap.dedent(
        """
        '200':
          description: successful operation
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = responses.build(root)
    assert isinstance(result, responses.Responses)

    assert result.root_node == root
    assert result.default is None
    assert len(result.responses) == 1
    assert result.extensions == {}

    # Check the response
    response_keys = {k.value for k in result.responses.keys()}
    assert "200" in response_keys


def test_build_with_multiple_responses():
    """Test building Responses with multiple status codes."""
    yaml_content = textwrap.dedent(
        """
        '200':
          description: successful operation
        '404':
          description: not found
        '500':
          description: server error
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = responses.build(root)
    assert isinstance(result, responses.Responses)

    assert len(result.responses) == 3
    response_keys = {k.value for k in result.responses.keys()}
    assert response_keys == {"200", "404", "500"}

    # Verify all are Response objects
    for response_value in result.responses.values():
        assert isinstance(response_value, Response)


def test_build_with_default_response():
    """Test building Responses with default response."""
    yaml_content = textwrap.dedent(
        """
        '200':
          description: successful operation
        default:
          description: unexpected error
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = responses.build(root)
    assert isinstance(result, responses.Responses)

    assert result.default is not None
    assert isinstance(result.default, FieldSource)
    assert isinstance(result.default.value, Response)
    assert result.default.value.description is not None
    assert result.default.value.description.value == "unexpected error"

    assert len(result.responses) == 1


def test_build_with_default_only():
    """Test building Responses with only default response."""
    yaml_content = textwrap.dedent(
        """
        default:
          description: default response
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = responses.build(root)
    assert isinstance(result, responses.Responses)

    assert result.default is not None
    assert isinstance(result.default.value, Response)
    assert len(result.responses) == 0


def test_build_with_patterned_status_codes():
    """Test building Responses with patterned status codes like 2XX, 4XX."""
    yaml_content = textwrap.dedent(
        """
        '2XX':
          description: successful operation
        '4XX':
          description: client error
        '5XX':
          description: server error
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = responses.build(root)
    assert isinstance(result, responses.Responses)

    assert len(result.responses) == 3
    response_keys = {k.value for k in result.responses.keys()}
    assert response_keys == {"2XX", "4XX", "5XX"}


def test_build_with_extensions():
    """Test building Responses with specification extensions."""
    yaml_content = textwrap.dedent(
        """
        '200':
          description: successful operation
        x-custom: value
        x-internal: true
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = responses.build(root)
    assert isinstance(result, responses.Responses)

    assert len(result.extensions) == 2
    ext_dict = {k.value: v.value for k, v in result.extensions.items()}
    assert ext_dict["x-custom"] == "value"
    assert ext_dict["x-internal"] is True


def test_build_with_all_fields():
    """Test building Responses with all field types."""
    yaml_content = textwrap.dedent(
        """
        '200':
          description: successful operation
        '404':
          description: not found
        default:
          description: unexpected error
        x-response-codes: [200, 404]
        x-metrics: true
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = responses.build(root)
    assert isinstance(result, responses.Responses)

    assert result.default is not None
    assert len(result.responses) == 2
    assert len(result.extensions) == 2


def test_build_with_response_references():
    """Test building Responses with $ref references."""
    yaml_content = textwrap.dedent(
        """
        '200':
          $ref: '#/components/responses/Success'
        '404':
          $ref: '#/components/responses/NotFound'
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = responses.build(root)
    assert isinstance(result, responses.Responses)

    assert len(result.responses) == 2

    # Verify they are Reference objects
    for response_value in result.responses.values():
        assert isinstance(response_value, Reference)
        assert response_value.ref is not None


def test_build_with_default_reference():
    """Test building Responses with default as a reference."""
    yaml_content = textwrap.dedent(
        """
        '200':
          description: success
        default:
          $ref: '#/components/responses/DefaultError'
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = responses.build(root)
    assert isinstance(result, responses.Responses)

    assert result.default is not None
    assert isinstance(result.default.value, Reference)
    assert result.default.value.ref is not None
    assert result.default.value.ref.value == "#/components/responses/DefaultError"


def test_build_with_mixed_responses_and_references():
    """Test building Responses with mix of Response objects and References."""
    yaml_content = textwrap.dedent(
        """
        '200':
          description: successful operation
          content:
            application/json:
              schema:
                type: object
        '404':
          $ref: '#/components/responses/NotFound'
        '500':
          $ref: '#/components/responses/ServerError'
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = responses.build(root)
    assert isinstance(result, responses.Responses)

    assert len(result.responses) == 3

    # Check 200 is Response
    key_200 = next(k for k in result.responses.keys() if k.value == "200")
    assert isinstance(result.responses[key_200], Response)

    # Check 404 and 500 are References
    key_404 = next(k for k in result.responses.keys() if k.value == "404")
    assert isinstance(result.responses[key_404], Reference)

    key_500 = next(k for k in result.responses.keys() if k.value == "500")
    assert isinstance(result.responses[key_500], Reference)


def test_build_with_empty_object():
    """Test building Responses from empty YAML object."""
    yaml_content = "{}"
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = responses.build(root)
    assert isinstance(result, responses.Responses)

    assert result.root_node == root
    assert result.default is None
    assert result.responses == {}
    assert result.extensions == {}


def test_build_with_invalid_node_returns_value_source():
    """Test that build returns ValueSource for non-mapping nodes."""
    yaml_parser = YAML()

    # Scalar node
    scalar_root = yaml_parser.compose("not-a-responses-object")
    result = responses.build(scalar_root)
    assert isinstance(result, ValueSource)
    assert result.value == "not-a-responses-object"
    assert result.value_node == scalar_root

    # Sequence node
    sequence_root = yaml_parser.compose("['200', '404']")
    result = responses.build(sequence_root)
    assert isinstance(result, ValueSource)
    assert result.value == ["200", "404"]
    assert result.value_node == sequence_root


def test_build_with_custom_context():
    """Test building Responses with a custom context."""
    yaml_content = textwrap.dedent(
        """
        '200':
          description: success
        default:
          description: error
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    custom_context = Context()
    result = responses.build(root, context=custom_context)
    assert isinstance(result, responses.Responses)

    assert result.default is not None
    assert len(result.responses) == 1


def test_source_tracking():
    """Test that source location information is preserved."""
    yaml_content = textwrap.dedent(
        """
        '200':
          description: success
        default:
          description: error
        x-custom: value
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = responses.build(root)
    assert isinstance(result, responses.Responses)

    # Check default source tracking
    assert isinstance(result.default, FieldSource)
    assert result.default.key_node is not None
    assert result.default.value_node is not None
    assert result.default.key_node.value == "default"

    # Check response key source tracking
    for key_source in result.responses.keys():
        assert isinstance(key_source, KeySource)
        assert key_source.key_node is not None

    # Check extension source tracking
    for key_source, value_source in result.extensions.items():
        assert isinstance(key_source, KeySource)
        assert key_source.key_node is not None
        assert isinstance(value_source, ValueSource)
        assert value_source.value_node is not None

    # Check line numbers are available
    assert hasattr(result.default.key_node.start_mark, "line")
    assert hasattr(result.default.value_node.start_mark, "line")


def test_build_with_invalid_response_data():
    """Test that invalid response data is preserved."""
    yaml_content = textwrap.dedent(
        """
        '200': invalid-string-not-object
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = responses.build(root)
    assert isinstance(result, responses.Responses)

    assert len(result.responses) == 1

    response_keys = list(result.responses.keys())
    assert response_keys[0].value == "200"
    # The invalid data should be preserved - child builder returns ValueSource
    response_value = result.responses[response_keys[0]]
    assert isinstance(response_value, ValueSource)
    assert response_value.value == "invalid-string-not-object"


def test_build_with_null_default():
    """Test that build preserves null default value."""
    yaml_content = textwrap.dedent(
        """
        '200':
          description: success
        default:
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = responses.build(root)
    assert isinstance(result, responses.Responses)

    assert result.default is not None
    assert result.default.value is None


def test_build_real_world_rest_api_responses():
    """Test a complete real-world REST API responses object."""
    yaml_content = textwrap.dedent(
        """
        '200':
          description: successful operation
          content:
            application/json:
              schema:
                type: array
                items:
                  type: object
        '400':
          description: invalid request
        '401':
          description: unauthorized
        '404':
          description: not found
        default:
          description: unexpected error
          content:
            application/json:
              schema:
                type: object
                properties:
                  code:
                    type: integer
                  message:
                    type: string
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = responses.build(root)
    assert isinstance(result, responses.Responses)

    assert result.default is not None
    assert isinstance(result.default.value, Response)
    assert len(result.responses) == 4

    response_keys = {k.value for k in result.responses.keys()}
    assert response_keys == {"200", "400", "401", "404"}

    # Check 200 response has content
    key_200 = next(k for k in result.responses.keys() if k.value == "200")
    response_200 = result.responses[key_200]
    assert isinstance(response_200, Response)
    assert response_200.content is not None


def test_build_with_http_status_code_ranges():
    """Test building Responses with various HTTP status code formats."""
    yaml_content = textwrap.dedent(
        """
        '200':
          description: OK
        '201':
          description: Created
        '2XX':
          description: Success
        '4XX':
          description: Client Error
        '5XX':
          description: Server Error
        default:
          description: Default response
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = responses.build(root)
    assert isinstance(result, responses.Responses)

    assert len(result.responses) == 5
    response_keys = {k.value for k in result.responses.keys()}
    assert response_keys == {"200", "201", "2XX", "4XX", "5XX"}
    assert result.default is not None


def test_responses_with_complex_content():
    """Test Responses with complex content including headers and links."""
    yaml_content = textwrap.dedent(
        """
        '200':
          description: successful operation
          headers:
            X-Rate-Limit:
              schema:
                type: integer
          content:
            application/json:
              schema:
                type: object
          links:
            GetUserById:
              operationId: getUserById
              parameters:
                userId: $response.body#/id
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = responses.build(root)
    assert isinstance(result, responses.Responses)

    assert len(result.responses) == 1
    key_200 = next(k for k in result.responses.keys() if k.value == "200")
    response_200 = result.responses[key_200]

    assert isinstance(response_200, Response)
    assert response_200.headers is not None
    assert response_200.content is not None
    assert response_200.links is not None


def test_build_with_numeric_status_codes():
    """Test that numeric status codes (without quotes) are handled."""
    yaml_content = textwrap.dedent(
        """
        200:
          description: successful operation
        404:
          description: not found
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = responses.build(root)
    assert isinstance(result, responses.Responses)

    assert len(result.responses) == 2
    # YAML constructor will convert numeric keys to strings
    response_keys = {k.value for k in result.responses.keys()}
    assert "200" in response_keys or 200 in response_keys
    assert "404" in response_keys or 404 in response_keys


def test_responses_preserves_order():
    """Test that response order is preserved during parsing."""
    yaml_content = textwrap.dedent(
        """
        '200':
          description: OK
        '201':
          description: Created
        '400':
          description: Bad Request
        '404':
          description: Not Found
        '500':
          description: Server Error
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = responses.build(root)
    assert isinstance(result, responses.Responses)

    # Dict should maintain insertion order (Python 3.7+)
    response_keys_list = [k.value for k in result.responses.keys()]
    assert response_keys_list == ["200", "201", "400", "404", "500"]


def test_build_with_invalid_status_codes_ignored():
    """Test that invalid status codes are ignored."""
    yaml_content = textwrap.dedent(
        """
        '200':
          description: valid
        '99':
          description: invalid - too low
        '600':
          description: invalid - too high
        '0':
          description: invalid - zero
        '999':
          description: invalid - too high
        '200':
          description: valid duplicate
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = responses.build(root)
    assert isinstance(result, responses.Responses)

    # Only valid status code 200 should be included (99, 600, 0, 999 are invalid)
    response_keys = {k.value for k in result.responses.keys()}
    assert "200" in response_keys
    assert "99" not in response_keys
    assert "600" not in response_keys
    assert "0" not in response_keys
    assert "999" not in response_keys


def test_build_with_invalid_wildcard_patterns_ignored():
    """Test that invalid wildcard patterns are ignored."""
    yaml_content = textwrap.dedent(
        """
        '2XX':
          description: valid pattern
        '0XX':
          description: invalid - starts with 0
        '6XX':
          description: invalid - starts with 6
        '9XX':
          description: invalid - starts with 9
        XXX:
          description: invalid - no digit
        '12XX':
          description: invalid - too many digits
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = responses.build(root)
    assert isinstance(result, responses.Responses)

    # Only valid pattern 2XX should be included
    response_keys = {k.value for k in result.responses.keys()}
    assert "2XX" in response_keys
    assert "0XX" not in response_keys
    assert "6XX" not in response_keys
    assert "9XX" not in response_keys
    assert "XXX" not in response_keys
    assert "12XX" not in response_keys


def test_build_with_boundary_status_codes():
    """Test boundary values for status codes (100 and 599)."""
    yaml_content = textwrap.dedent(
        """
        '100':
          description: minimum valid
        '599':
          description: maximum valid
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = responses.build(root)
    assert isinstance(result, responses.Responses)

    response_keys = {k.value for k in result.responses.keys()}
    assert "100" in response_keys
    assert "599" in response_keys
    assert len(result.responses) == 2


def test_build_with_mixed_valid_and_invalid_keys():
    """Test that valid responses are kept while invalid keys are ignored."""
    yaml_content = textwrap.dedent(
        """
        '200':
          description: valid status code
        '3XX':
          description: valid pattern
        default:
          description: valid fixed field
        invalidKey:
          description: invalid - not a status code
        randomField:
          description: invalid - random field
        x-custom:
          value: extension field
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = responses.build(root)
    assert isinstance(result, responses.Responses)

    # Should have 2 valid responses (200 and 3XX)
    response_keys = {k.value for k in result.responses.keys()}
    assert response_keys == {"200", "3XX"}

    # Should have default field
    assert result.default is not None

    # Should have extension field
    assert len(result.extensions) == 1
    ext_keys = {k.value for k in result.extensions.keys()}
    assert "x-custom" in ext_keys

    # Invalid keys should not appear anywhere
    assert "invalidKey" not in response_keys
    assert "randomField" not in response_keys
