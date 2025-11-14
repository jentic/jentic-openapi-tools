"""Tests for Encoding low-level datamodel."""

import textwrap

from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap

from jentic.apitools.openapi.datamodels.low.context import Context
from jentic.apitools.openapi.datamodels.low.sources import FieldSource, KeySource, ValueSource
from jentic.apitools.openapi.datamodels.low.v30 import encoding
from jentic.apitools.openapi.datamodels.low.v30.header import Header
from jentic.apitools.openapi.datamodels.low.v30.reference import Reference


def test_build_with_content_type_only():
    """Test building Encoding with only contentType field."""
    yaml_content = textwrap.dedent(
        """
        contentType: application/xml
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = encoding.build(root)
    assert isinstance(result, encoding.Encoding)

    assert result.root_node == root
    assert isinstance(result.contentType, FieldSource)
    assert result.contentType.value == "application/xml"

    # Optional fields should be None
    assert result.headers is None
    assert result.style is None
    assert result.explode is None
    assert result.allowReserved is None
    assert result.extensions == {}


def test_build_with_headers():
    """Test building Encoding with headers field."""
    yaml_content = textwrap.dedent(
        """
        contentType: application/xml
        headers:
          X-Rate-Limit:
            description: Rate limit header
            schema:
              type: integer
          X-Expires-After:
            description: Expiration header
            schema:
              type: string
              format: date-time
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = encoding.build(root)
    assert isinstance(result, encoding.Encoding)

    assert result.contentType is not None
    assert result.contentType.value == "application/xml"

    assert result.headers is not None
    assert isinstance(result.headers, FieldSource)
    assert isinstance(result.headers.value, dict)
    assert len(result.headers.value) == 2

    # Check header keys
    header_keys = {k.value for k in result.headers.value.keys()}
    assert header_keys == {"X-Rate-Limit", "X-Expires-After"}

    # Check X-Rate-Limit header
    rate_limit_key = next(k for k in result.headers.value.keys() if k.value == "X-Rate-Limit")
    rate_limit_header = result.headers.value[rate_limit_key]
    assert isinstance(rate_limit_header, Header)
    assert rate_limit_header.description is not None
    assert rate_limit_header.description.value == "Rate limit header"


def test_build_with_headers_reference():
    """Test building Encoding with headers containing $ref."""
    yaml_content = textwrap.dedent(
        """
        contentType: application/json
        headers:
          X-Custom-Header:
            $ref: '#/components/headers/CustomHeader'
          X-Another-Header:
            description: Direct header definition
            schema:
              type: string
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = encoding.build(root)
    assert isinstance(result, encoding.Encoding)

    assert result.headers is not None
    assert len(result.headers.value) == 2

    # Check that X-Custom-Header is a Reference
    custom_key = next(k for k in result.headers.value.keys() if k.value == "X-Custom-Header")
    custom_header = result.headers.value[custom_key]
    assert isinstance(custom_header, Reference)
    assert custom_header.ref is not None
    assert custom_header.ref.value == "#/components/headers/CustomHeader"

    # Check that X-Another-Header is a Header
    another_key = next(k for k in result.headers.value.keys() if k.value == "X-Another-Header")
    another_header = result.headers.value[another_key]
    assert isinstance(another_header, Header)


def test_build_with_style_and_explode():
    """Test building Encoding with style and explode fields."""
    yaml_content = textwrap.dedent(
        """
        contentType: application/json
        style: form
        explode: true
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = encoding.build(root)
    assert isinstance(result, encoding.Encoding)

    assert result.style is not None
    assert result.style.value == "form"
    assert result.explode is not None
    assert result.explode.value is True


def test_build_with_allow_reserved():
    """Test building Encoding with allowReserved field."""
    yaml_content = textwrap.dedent(
        """
        contentType: application/x-www-form-urlencoded
        allowReserved: true
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = encoding.build(root)
    assert isinstance(result, encoding.Encoding)

    assert result.allowReserved is not None
    assert result.allowReserved.value is True


def test_build_with_all_fields():
    """Test building Encoding with all fields."""
    yaml_content = textwrap.dedent(
        """
        contentType: application/xml; charset=utf-8
        headers:
          X-Custom:
            description: Custom header
            schema:
              type: string
        style: form
        explode: false
        allowReserved: true
        x-custom: value
        x-internal: true
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = encoding.build(root)
    assert isinstance(result, encoding.Encoding)

    assert result.contentType is not None
    assert result.contentType.value == "application/xml; charset=utf-8"
    assert result.headers is not None
    assert len(result.headers.value) == 1
    assert result.style is not None
    assert result.style.value == "form"
    assert result.explode is not None
    assert result.explode.value is False
    assert result.allowReserved is not None
    assert result.allowReserved.value is True

    # Check extensions
    assert len(result.extensions) == 2
    ext_dict = {k.value: v.value for k, v in result.extensions.items()}
    assert ext_dict["x-custom"] == "value"
    assert ext_dict["x-internal"] is True


def test_build_with_empty_object():
    """Test building Encoding from empty YAML object."""
    yaml_content = "{}"
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = encoding.build(root)
    assert isinstance(result, encoding.Encoding)

    assert result.root_node == root
    assert result.contentType is None
    assert result.headers is None
    assert result.style is None
    assert result.explode is None
    assert result.allowReserved is None
    assert result.extensions == {}


def test_build_with_invalid_node_returns_value_source():
    """Test that build returns ValueSource for non-mapping nodes."""
    yaml_parser = YAML()

    # Scalar node
    scalar_root = yaml_parser.compose("not-an-encoding-object")
    result = encoding.build(scalar_root)
    assert isinstance(result, ValueSource)
    assert result.value == "not-an-encoding-object"
    assert result.value_node == scalar_root

    # Sequence node
    sequence_root = yaml_parser.compose("['item1', 'item2']")
    result = encoding.build(sequence_root)
    assert isinstance(result, ValueSource)
    assert result.value == ["item1", "item2"]
    assert result.value_node == sequence_root


def test_build_preserves_invalid_types():
    """Test that build preserves values even with 'wrong' types."""
    yaml_content = textwrap.dedent(
        """
        contentType: 12345
        style: 999
        explode: not-a-boolean
        allowReserved: invalid-value
        headers: not-a-mapping
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = encoding.build(root)
    assert isinstance(result, encoding.Encoding)

    # Should preserve the actual values, not convert them
    assert result.contentType is not None
    assert result.contentType.value == 12345

    assert result.style is not None
    assert result.style.value == 999

    assert result.explode is not None
    assert result.explode.value == "not-a-boolean"

    assert result.allowReserved is not None
    assert result.allowReserved.value == "invalid-value"

    assert result.headers is not None
    assert result.headers.value == "not-a-mapping"


def test_build_with_invalid_headers_data():
    """Test that invalid headers data is preserved."""
    yaml_content = textwrap.dedent(
        """
        contentType: application/json
        headers:
          broken: invalid-string-not-object
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = encoding.build(root)
    assert isinstance(result, encoding.Encoding)

    assert result.headers is not None
    assert len(result.headers.value) == 1

    header_keys = list(result.headers.value.keys())
    assert header_keys[0].value == "broken"
    # The invalid data should be preserved - child builder returns ValueSource
    header_value = result.headers.value[header_keys[0]]
    assert isinstance(header_value, ValueSource)
    assert header_value.value == "invalid-string-not-object"


def test_build_with_custom_context():
    """Test building Encoding with a custom context."""
    yaml_content = textwrap.dedent(
        """
        contentType: text/plain
        style: simple
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    custom_context = Context()
    result = encoding.build(root, context=custom_context)
    assert isinstance(result, encoding.Encoding)

    assert isinstance(result.contentType, FieldSource)
    assert result.contentType.value == "text/plain"


def test_source_tracking():
    """Test that source location information is preserved."""
    yaml_content = textwrap.dedent(
        """
        contentType: application/json
        style: form
        explode: true
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = encoding.build(root)
    assert isinstance(result, encoding.Encoding)

    # Check contentType source tracking
    assert isinstance(result.contentType, FieldSource)
    assert result.contentType.key_node is not None
    assert result.contentType.value_node is not None
    assert result.contentType.key_node.value == "contentType"
    assert result.contentType.value_node.value == "application/json"

    # Check style source tracking
    assert isinstance(result.style, FieldSource)
    assert result.style.key_node is not None
    assert result.style.value_node is not None
    assert result.style.key_node.value == "style"

    # Check explode source tracking
    assert isinstance(result.explode, FieldSource)
    assert result.explode.key_node is not None
    assert result.explode.value_node is not None
    assert result.explode.key_node.value == "explode"

    # Check line numbers are available
    assert hasattr(result.contentType.key_node.start_mark, "line")
    assert hasattr(result.contentType.value_node.start_mark, "line")


def test_build_with_null_values():
    """Test that build preserves null values."""
    yaml_content = textwrap.dedent(
        """
        contentType:
        headers:
        style:
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = encoding.build(root)
    assert isinstance(result, encoding.Encoding)

    assert result.contentType is not None
    assert result.contentType.value is None

    assert result.headers is not None
    assert result.headers.value is None

    assert result.style is not None
    assert result.style.value is None


def test_build_with_complex_extensions():
    """Test building Encoding with complex extension objects."""
    yaml_content = textwrap.dedent(
        """
        contentType: application/json
        x-encoding-config:
          compression: gzip
          level: 9
        x-format: custom
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = encoding.build(root)
    assert isinstance(result, encoding.Encoding)

    assert len(result.extensions) == 2
    ext_dict = {k.value: v.value for k, v in result.extensions.items()}

    # Check x-encoding-config extension
    encoding_config = ext_dict["x-encoding-config"]
    assert isinstance(encoding_config, CommentedMap)
    assert encoding_config["compression"] == "gzip"
    assert encoding_config["level"] == 9

    # Check x-format extension
    assert ext_dict["x-format"] == "custom"


def test_build_real_world_multipart():
    """Test a complete real-world multipart/form-data Encoding."""
    yaml_content = textwrap.dedent(
        """
        contentType: application/json
        headers:
          X-Custom-Header:
            description: Custom header for this part
            schema:
              type: string
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = encoding.build(root)
    assert isinstance(result, encoding.Encoding)

    assert isinstance(result.contentType, FieldSource)
    assert result.contentType.value == "application/json"
    assert result.headers is not None
    assert len(result.headers.value) == 1

    header_key = next(k for k in result.headers.value.keys())
    assert header_key.value == "X-Custom-Header"
    header_obj = result.headers.value[header_key]
    assert isinstance(header_obj, Header)
    assert header_obj.description is not None
    assert header_obj.description.value == "Custom header for this part"


def test_build_real_world_url_encoded():
    """Test a complete real-world application/x-www-form-urlencoded Encoding."""
    yaml_content = textwrap.dedent(
        """
        contentType: application/x-www-form-urlencoded
        style: form
        explode: true
        allowReserved: false
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = encoding.build(root)
    assert isinstance(result, encoding.Encoding)

    assert result.contentType is not None
    assert result.contentType.value == "application/x-www-form-urlencoded"
    assert result.style is not None
    assert result.style.value == "form"
    assert result.explode is not None
    assert result.explode.value is True
    assert result.allowReserved is not None
    assert result.allowReserved.value is False


def test_headers_source_tracking():
    """Test that headers maintain proper source tracking."""
    yaml_content = textwrap.dedent(
        """
        contentType: application/json
        headers:
          X-First:
            description: First header
            schema:
              type: string
          X-Second:
            description: Second header
            schema:
              type: integer
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = encoding.build(root)
    assert isinstance(result, encoding.Encoding)

    assert result.headers is not None

    # Check that each header key has source tracking
    for header_key, header_value in result.headers.value.items():
        assert isinstance(header_key, KeySource)
        assert header_key.key_node is not None

        # Check that the Header or ValueSource has proper root_node/value_node
        if isinstance(header_value, Header):
            assert header_value.root_node is not None
        elif isinstance(header_value, ValueSource):
            assert header_value.value_node is not None


def test_build_with_binary_content_type():
    """Test building Encoding with binary content type."""
    yaml_content = textwrap.dedent(
        """
        contentType: application/octet-stream
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = encoding.build(root)
    assert isinstance(result, encoding.Encoding)

    assert result.contentType is not None
    assert result.contentType.value == "application/octet-stream"


def test_build_with_multiple_headers_mixed():
    """Test building Encoding with mix of Header objects and References."""
    yaml_content = textwrap.dedent(
        """
        contentType: multipart/form-data
        headers:
          Content-Type:
            schema:
              type: string
          X-Rate-Limit:
            $ref: '#/components/headers/RateLimit'
          X-Custom:
            description: Custom header
            required: true
            schema:
              type: integer
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = encoding.build(root)
    assert isinstance(result, encoding.Encoding)

    assert result.headers is not None
    assert len(result.headers.value) == 3

    # Check Content-Type is a Header
    content_type_key = next(k for k in result.headers.value.keys() if k.value == "Content-Type")
    content_type_header = result.headers.value[content_type_key]
    assert isinstance(content_type_header, Header)

    # Check X-Rate-Limit is a Reference
    rate_limit_key = next(k for k in result.headers.value.keys() if k.value == "X-Rate-Limit")
    rate_limit_ref = result.headers.value[rate_limit_key]
    assert isinstance(rate_limit_ref, Reference)
    assert rate_limit_ref.ref is not None
    assert rate_limit_ref.ref.value == "#/components/headers/RateLimit"

    # Check X-Custom is a Header
    custom_key = next(k for k in result.headers.value.keys() if k.value == "X-Custom")
    custom_header = result.headers.value[custom_key]
    assert isinstance(custom_header, Header)
    assert custom_header.required is not None
    assert custom_header.required.value is True
