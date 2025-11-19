"""Tests for OpenAPI version detection."""

import textwrap

from jentic.apitools.openapi.common.version_detection import (
    get_version,
    is_openapi_20,
    is_openapi_30,
    is_openapi_31,
    is_openapi_32,
)


# Version Extraction Tests


def test_get_version_swagger_20_yaml():
    """Test version extraction from Swagger 2.0 YAML."""
    yaml_text = textwrap.dedent("""
        swagger: 2.0
        info:
          title: Test API
          version: 1.0.0
    """)
    assert get_version(yaml_text) == "2.0"


def test_get_version_swagger_20_json():
    """Test version extraction from Swagger 2.0 JSON."""
    assert get_version('{"swagger": "2.0"}') == "2.0"


def test_get_version_swagger_20_mapping():
    """Test version extraction from Swagger 2.0 Mapping."""
    assert get_version({"swagger": "2.0"}) == "2.0"


def test_get_version_openapi_30_yaml():
    """Test version extraction from OpenAPI 3.0 YAML."""
    yaml_text = textwrap.dedent("""
        openapi: 3.0.4
        info:
          title: Test API
          version: 1.0.0
    """)
    assert get_version(yaml_text) == "3.0.4"


def test_get_version_openapi_30_json():
    """Test version extraction from OpenAPI 3.0 JSON."""
    assert get_version('{"openapi": "3.0.4"}') == "3.0.4"


def test_get_version_openapi_30_mapping():
    """Test version extraction from OpenAPI 3.0 Mapping."""
    assert get_version({"openapi": "3.0.4"}) == "3.0.4"


def test_get_version_openapi_31_yaml():
    """Test version extraction from OpenAPI 3.1 YAML."""
    assert get_version("openapi: 3.1.2") == "3.1.2"


def test_get_version_openapi_31_json():
    """Test version extraction from OpenAPI 3.1 JSON."""
    assert get_version('{"openapi": "3.1.2"}') == "3.1.2"


def test_get_version_openapi_31_mapping():
    """Test version extraction from OpenAPI 3.1 Mapping."""
    assert get_version({"openapi": "3.1.2"}) == "3.1.2"


def test_get_version_openapi_32_yaml():
    """Test version extraction from OpenAPI 3.2 YAML."""
    assert get_version("openapi: 3.2.0") == "3.2.0"


def test_get_version_openapi_32_json():
    """Test version extraction from OpenAPI 3.2 JSON."""
    assert get_version('{"openapi": "3.2.0"}') == "3.2.0"


def test_get_version_openapi_32_mapping():
    """Test version extraction from OpenAPI 3.2 Mapping."""
    assert get_version({"openapi": "3.2.0"}) == "3.2.0"


def test_get_version_with_quotes():
    """Test version extraction with quoted values."""
    assert get_version('openapi: "3.0.4"') == "3.0.4"
    assert get_version("openapi: '3.1.2'") == "3.1.2"


def test_get_version_various_patches():
    """Test version extraction with various patch versions."""
    assert get_version({"openapi": "3.0.0"}) == "3.0.0"
    assert get_version({"openapi": "3.0.10"}) == "3.0.10"
    assert get_version({"openapi": "3.1.100"}) == "3.1.100"
    assert get_version({"openapi": "3.2.5"}) == "3.2.5"


def test_get_version_invalid_inputs():
    """Test get_version returns None for invalid inputs."""
    assert get_version("") is None
    assert get_version("not yaml") is None
    assert get_version({}) is None
    assert get_version({"info": "test"}) is None


def test_get_version_invalid_types():
    """Test get_version returns None for invalid types."""
    assert get_version({"openapi": None}) is None
    assert get_version({"openapi": 3.0}) is None
    assert get_version({"swagger": None}) is None
    assert get_version({"swagger": 2.0}) is None


def test_get_version_returns_suffixes():
    """Test get_version returns versions with suffixes as-is from Mapping."""
    assert get_version({"openapi": "3.0.4-rc1"}) == "3.0.4-rc1"
    assert get_version({"openapi": "3.1.2-beta"}) == "3.1.2-beta"
    assert get_version({"openapi": "3.2.0-alpha.1"}) == "3.2.0-alpha.1"


def test_get_version_returns_any_version_string():
    """Test get_version returns any version string from Mapping, even if unsupported."""
    assert get_version({"openapi": "3.3.0"}) == "3.3.0"  # Future version
    assert get_version({"openapi": "4.0.0"}) == "4.0.0"  # Future version
    assert get_version({"openapi": "3.0.01"}) == "3.0.01"  # Invalid format
    assert get_version({"swagger": "2.1"}) == "2.1"  # Non-standard swagger
    assert get_version({"swagger": "1.2"}) == "1.2"  # Old swagger version


def test_get_version_text_validates_with_regex():
    """Test get_version validates text input with regex patterns."""
    # Text with suffixes should return None (doesn't match our patterns)
    assert get_version("openapi: 3.0.4-rc1") is None
    assert get_version("openapi: 3.1.2-beta") is None
    # Text with unsupported versions should return None
    assert get_version("openapi: 3.3.0") is None
    assert get_version("openapi: 4.0.0") is None
    # Valid text should extract version
    assert get_version("openapi: 3.0.4") == "3.0.4"
    assert get_version("openapi: 3.1.2") == "3.1.2"


# OpenAPI 2.0 Detection Tests


def test_is_openapi_20_yaml_basic():
    """Test basic YAML format detection for 2.0."""
    yaml_text = textwrap.dedent("""
        swagger: 2.0
        info:
          title: Test API
          version: 1.0.0
    """)
    assert is_openapi_20(yaml_text) is True


def test_is_openapi_20_yaml_with_quotes():
    """Test YAML format with quotes around version."""
    assert is_openapi_20('swagger: "2.0"') is True
    assert is_openapi_20("swagger: '2.0'") is True


def test_is_openapi_20_json():
    """Test JSON format detection for 2.0."""
    assert is_openapi_20('{"swagger": "2.0"}') is True
    assert is_openapi_20('{"swagger":"2.0","info":{}}') is True


def test_is_openapi_20_mapping():
    """Test Mapping object detection for 2.0."""
    assert is_openapi_20({"swagger": "2.0"}) is True


def test_is_openapi_20_negative_30():
    """Test that 3.0.x is not detected as 2.0."""
    assert is_openapi_20("openapi: 3.0.4") is False
    assert is_openapi_20('{"openapi": "3.0.4"}') is False
    assert is_openapi_20({"openapi": "3.0.4"}) is False


def test_is_openapi_20_negative_31():
    """Test that 3.1.x is not detected as 2.0."""
    assert is_openapi_20("openapi: 3.1.0") is False
    assert is_openapi_20('{"openapi": "3.1.0"}') is False
    assert is_openapi_20({"openapi": "3.1.0"}) is False


def test_is_openapi_20_negative_invalid():
    """Test invalid inputs return False."""
    assert is_openapi_20("") is False
    assert is_openapi_20("not yaml") is False
    assert is_openapi_20({}) is False
    assert is_openapi_20({"swagger": None}) is False
    assert is_openapi_20({"swagger": 2.0}) is False  # Not a string
    assert is_openapi_20({"info": "test"}) is False  # Missing swagger


def test_is_openapi_20_negative_other_versions():
    """Test that other swagger versions are rejected."""
    assert is_openapi_20("swagger: 2.1") is False
    assert is_openapi_20("swagger: 1.2") is False
    assert is_openapi_20({"swagger": "2.1"}) is False
    assert is_openapi_20({"swagger": "1.2"}) is False


# OpenAPI 3.0 Detection Tests


def test_is_openapi_30_yaml_basic():
    """Test basic YAML format detection for 3.0.x."""
    yaml_text = textwrap.dedent("""
        openapi: 3.0.4
        info:
          title: Test API
          version: 1.0.0
    """)
    assert is_openapi_30(yaml_text) is True


def test_is_openapi_30_yaml_with_quotes():
    """Test YAML format with quotes around version."""
    assert is_openapi_30('openapi: "3.0.4"') is True
    assert is_openapi_30("openapi: '3.0.4'") is True


def test_is_openapi_30_yaml_various_patches():
    """Test various patch versions for 3.0.x."""
    assert is_openapi_30("openapi: 3.0.0") is True
    assert is_openapi_30("openapi: 3.0.1") is True
    assert is_openapi_30("openapi: 3.0.2") is True
    assert is_openapi_30("openapi: 3.0.3") is True
    assert is_openapi_30("openapi: 3.0.4") is True
    assert is_openapi_30("openapi: 3.0.10") is True
    assert is_openapi_30("openapi: 3.0.100") is True


def test_is_openapi_30_json():
    """Test JSON format detection for 3.0.x."""
    assert is_openapi_30('{"openapi": "3.0.4"}') is True
    assert is_openapi_30('{"openapi":"3.0.4","info":{}}') is True


def test_is_openapi_30_mapping():
    """Test Mapping object detection for 3.0.x."""
    assert is_openapi_30({"openapi": "3.0.4"}) is True
    assert is_openapi_30({"openapi": "3.0.0"}) is True
    assert is_openapi_30({"openapi": "3.0.10"}) is True


def test_is_openapi_30_negative_suffix():
    """Test that version suffixes like -rc1 are rejected."""
    assert is_openapi_30({"openapi": "3.0.4-rc1"}) is False
    assert is_openapi_30({"openapi": "3.0.4-beta"}) is False
    assert is_openapi_30({"openapi": "3.0.4-alpha.1"}) is False


def test_is_openapi_30_negative_31():
    """Test that 3.1.x is not detected as 3.0.x."""
    assert is_openapi_30("openapi: 3.1.0") is False
    assert is_openapi_30('{"openapi": "3.1.0"}') is False
    assert is_openapi_30({"openapi": "3.1.0"}) is False


def test_is_openapi_30_negative_20():
    """Test that Swagger 2.0 is not detected as 3.0.x."""
    assert is_openapi_30("swagger: 2.0") is False
    assert is_openapi_30('{"swagger": "2.0"}') is False
    assert is_openapi_30({"swagger": "2.0"}) is False


def test_is_openapi_30_negative_32():
    """Test that future 3.2.x is not detected as 3.0.x."""
    assert is_openapi_30("openapi: 3.2.0") is False
    assert is_openapi_30({"openapi": "3.2.0"}) is False


def test_is_openapi_30_negative_invalid():
    """Test invalid inputs return False."""
    assert is_openapi_30("") is False
    assert is_openapi_30("not yaml") is False
    assert is_openapi_30({}) is False
    assert is_openapi_30({"openapi": None}) is False
    assert is_openapi_30({"openapi": 3.0}) is False  # Not a string
    assert is_openapi_30({"info": "test"}) is False  # Missing openapi


def test_is_openapi_30_negative_leading_zeros():
    """Test that versions with invalid leading zeros are rejected."""
    # Leading zeros in patch version should be rejected (except 0 itself)
    assert is_openapi_30("openapi: 3.0.01") is False
    assert is_openapi_30("openapi: 3.0.001") is False
    assert is_openapi_30({"openapi": "3.0.01"}) is False


# OpenAPI 3.1 Detection Tests


def test_is_openapi_31_yaml_basic():
    """Test basic YAML format detection for 3.1.x."""
    yaml_text = textwrap.dedent("""
        openapi: 3.1.2
        info:
          title: Test API
          version: 1.0.0
    """)
    assert is_openapi_31(yaml_text) is True


def test_is_openapi_31_yaml_with_quotes():
    """Test YAML format with quotes around version."""
    assert is_openapi_31('openapi: "3.1.2"') is True
    assert is_openapi_31("openapi: '3.1.2'") is True


def test_is_openapi_31_yaml_various_patches():
    """Test various patch versions for 3.1.x."""
    assert is_openapi_31("openapi: 3.1.0") is True
    assert is_openapi_31("openapi: 3.1.1") is True
    assert is_openapi_31("openapi: 3.1.2") is True
    assert is_openapi_31("openapi: 3.1.10") is True
    assert is_openapi_31("openapi: 3.1.100") is True


def test_is_openapi_31_json():
    """Test JSON format detection for 3.1.x."""
    assert is_openapi_31('{"openapi": "3.1.2"}') is True
    assert is_openapi_31('{"openapi":"3.1.0","info":{}}') is True


def test_is_openapi_31_mapping():
    """Test Mapping object detection for 3.1.x."""
    assert is_openapi_31({"openapi": "3.1.2"}) is True
    assert is_openapi_31({"openapi": "3.1.0"}) is True
    assert is_openapi_31({"openapi": "3.1.10"}) is True


def test_is_openapi_31_negative_suffix():
    """Test that version suffixes like -rc1 are rejected."""
    assert is_openapi_31({"openapi": "3.1.2-rc1"}) is False
    assert is_openapi_31({"openapi": "3.1.2-beta"}) is False
    assert is_openapi_31({"openapi": "3.1.2-alpha.1"}) is False


def test_is_openapi_31_negative_30():
    """Test that 3.0.x is not detected as 3.1.x."""
    assert is_openapi_31("openapi: 3.0.4") is False
    assert is_openapi_31('{"openapi": "3.0.4"}') is False
    assert is_openapi_31({"openapi": "3.0.4"}) is False


def test_is_openapi_31_negative_20():
    """Test that Swagger 2.0 is not detected as 3.1.x."""
    assert is_openapi_31("swagger: 2.0") is False
    assert is_openapi_31('{"swagger": "2.0"}') is False
    assert is_openapi_31({"swagger": "2.0"}) is False


def test_is_openapi_31_negative_32():
    """Test that future 3.2.x is not detected as 3.1.x."""
    assert is_openapi_31("openapi: 3.2.0") is False
    assert is_openapi_31({"openapi": "3.2.0"}) is False


def test_is_openapi_31_negative_invalid():
    """Test invalid inputs return False."""
    assert is_openapi_31("") is False
    assert is_openapi_31("not yaml") is False
    assert is_openapi_31({}) is False
    assert is_openapi_31({"openapi": None}) is False
    assert is_openapi_31({"openapi": 3.1}) is False  # Not a string
    assert is_openapi_31({"info": "test"}) is False  # Missing openapi


def test_is_openapi_31_negative_leading_zeros():
    """Test that versions with invalid leading zeros are rejected."""
    assert is_openapi_31("openapi: 3.1.01") is False
    assert is_openapi_31("openapi: 3.1.001") is False
    assert is_openapi_31({"openapi": "3.1.01"}) is False


# OpenAPI 3.2 Detection Tests


def test_is_openapi_32_yaml_basic():
    """Test basic YAML format detection for 3.2.x."""
    yaml_text = textwrap.dedent("""
        openapi: 3.2.0
        info:
          title: Test API
          version: 1.0.0
    """)
    assert is_openapi_32(yaml_text) is True


def test_is_openapi_32_yaml_with_quotes():
    """Test YAML format with quotes around version."""
    assert is_openapi_32('openapi: "3.2.0"') is True
    assert is_openapi_32("openapi: '3.2.0'") is True


def test_is_openapi_32_yaml_various_patches():
    """Test various patch versions for 3.2.x."""
    assert is_openapi_32("openapi: 3.2.0") is True
    assert is_openapi_32("openapi: 3.2.1") is True
    assert is_openapi_32("openapi: 3.2.2") is True
    assert is_openapi_32("openapi: 3.2.10") is True
    assert is_openapi_32("openapi: 3.2.100") is True


def test_is_openapi_32_json():
    """Test JSON format detection for 3.2.x."""
    assert is_openapi_32('{"openapi": "3.2.0"}') is True
    assert is_openapi_32('{"openapi":"3.2.0","info":{}}') is True


def test_is_openapi_32_mapping():
    """Test Mapping object detection for 3.2.x."""
    assert is_openapi_32({"openapi": "3.2.0"}) is True
    assert is_openapi_32({"openapi": "3.2.1"}) is True
    assert is_openapi_32({"openapi": "3.2.10"}) is True


def test_is_openapi_32_negative_suffix():
    """Test that version suffixes like -rc1 are rejected."""
    assert is_openapi_32({"openapi": "3.2.0-rc1"}) is False
    assert is_openapi_32({"openapi": "3.2.0-beta"}) is False
    assert is_openapi_32({"openapi": "3.2.0-alpha.1"}) is False


def test_is_openapi_32_negative_30():
    """Test that 3.0.x is not detected as 3.2.x."""
    assert is_openapi_32("openapi: 3.0.4") is False
    assert is_openapi_32('{"openapi": "3.0.4"}') is False
    assert is_openapi_32({"openapi": "3.0.4"}) is False


def test_is_openapi_32_negative_31():
    """Test that 3.1.x is not detected as 3.2.x."""
    assert is_openapi_32("openapi: 3.1.0") is False
    assert is_openapi_32('{"openapi": "3.1.0"}') is False
    assert is_openapi_32({"openapi": "3.1.0"}) is False


def test_is_openapi_32_negative_20():
    """Test that Swagger 2.0 is not detected as 3.2.x."""
    assert is_openapi_32("swagger: 2.0") is False
    assert is_openapi_32('{"swagger": "2.0"}') is False
    assert is_openapi_32({"swagger": "2.0"}) is False


def test_is_openapi_32_negative_33():
    """Test that future 3.3.x is not detected as 3.2.x."""
    assert is_openapi_32("openapi: 3.3.0") is False
    assert is_openapi_32({"openapi": "3.3.0"}) is False


def test_is_openapi_32_negative_invalid():
    """Test invalid inputs return False."""
    assert is_openapi_32("") is False
    assert is_openapi_32("not yaml") is False
    assert is_openapi_32({}) is False
    assert is_openapi_32({"openapi": None}) is False
    assert is_openapi_32({"openapi": 3.2}) is False  # Not a string
    assert is_openapi_32({"info": "test"}) is False  # Missing openapi


def test_is_openapi_32_negative_leading_zeros():
    """Test that versions with invalid leading zeros are rejected."""
    assert is_openapi_32("openapi: 3.2.01") is False
    assert is_openapi_32("openapi: 3.2.001") is False
    assert is_openapi_32({"openapi": "3.2.01"}) is False


# Edge Cases and Complex Scenarios


def test_multiline_yaml_detection():
    """Test detection in multiline YAML documents."""
    yaml_30 = textwrap.dedent("""
        # Comment
        openapi: 3.0.4
        info:
          title: API
          description: |
            Multi-line description
            with openapi: 3.1.0 in text (should not match)
    """)
    assert is_openapi_30(yaml_30) is True
    assert is_openapi_31(yaml_30) is False


def test_json_with_whitespace():
    """Test JSON detection with various whitespace."""
    assert is_openapi_30('{ "openapi" : "3.0.4" }') is True
    assert is_openapi_30('{"openapi":"3.0.4"}') is True
    assert is_openapi_31('{ "openapi" : "3.1.0" }') is True


def test_yaml_with_extra_whitespace():
    """Test YAML detection with extra whitespace."""
    assert is_openapi_30("openapi:   3.0.4") is True
    assert is_openapi_30("openapi:3.0.4") is True
    assert is_openapi_31("openapi:   3.1.0") is True


def test_both_versions_exclusive():
    """Test that a document cannot be both 3.0 and 3.1."""
    doc_30 = {"openapi": "3.0.4"}
    assert is_openapi_30(doc_30) is True
    assert is_openapi_31(doc_30) is False

    doc_31 = {"openapi": "3.1.0"}
    assert is_openapi_30(doc_31) is False
    assert is_openapi_31(doc_31) is True


def test_all_versions_exclusive():
    """Test that a document is detected as exactly one version."""
    doc_20 = {"swagger": "2.0"}
    assert is_openapi_20(doc_20) is True
    assert is_openapi_30(doc_20) is False
    assert is_openapi_31(doc_20) is False
    assert is_openapi_32(doc_20) is False

    doc_30 = {"openapi": "3.0.4"}
    assert is_openapi_20(doc_30) is False
    assert is_openapi_30(doc_30) is True
    assert is_openapi_31(doc_30) is False
    assert is_openapi_32(doc_30) is False

    doc_31 = {"openapi": "3.1.0"}
    assert is_openapi_20(doc_31) is False
    assert is_openapi_30(doc_31) is False
    assert is_openapi_31(doc_31) is True
    assert is_openapi_32(doc_31) is False

    doc_32 = {"openapi": "3.2.0"}
    assert is_openapi_20(doc_32) is False
    assert is_openapi_30(doc_32) is False
    assert is_openapi_31(doc_32) is False
    assert is_openapi_32(doc_32) is True
