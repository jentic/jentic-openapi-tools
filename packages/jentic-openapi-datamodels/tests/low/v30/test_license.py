"""Tests for License low-level datamodel."""

import textwrap

from ruamel.yaml import YAML

from jentic.apitools.openapi.datamodels.low.context import Context
from jentic.apitools.openapi.datamodels.low.sources import FieldSource, KeySource, ValueSource
from jentic.apitools.openapi.datamodels.low.v30 import license as license_module


def test_build_with_all_fields():
    """Test building License with all specification fields."""
    yaml_content = textwrap.dedent(
        """
        name: Apache 2.0
        url: https://www.apache.org/licenses/LICENSE-2.0.html
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = license_module.build(root)
    assert isinstance(result, license_module.License)

    assert result.root_node == root

    # Check all fields are FieldSource instances
    assert isinstance(result.name, FieldSource)
    assert result.name.value == "Apache 2.0"
    assert result.name.key_node is not None
    assert result.name.value_node is not None

    assert isinstance(result.url, FieldSource)
    assert result.url.value == "https://www.apache.org/licenses/LICENSE-2.0.html"
    assert result.url.key_node is not None
    assert result.url.value_node is not None


def test_build_with_name_only():
    """Test building License with only required name field."""
    yaml_content = textwrap.dedent(
        """
        name: MIT
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = license_module.build(root)
    assert isinstance(result, license_module.License)

    assert result.root_node == root
    assert isinstance(result.name, FieldSource)
    assert result.name.value == "MIT"

    # URL is optional
    assert result.url is None
    # Extensions returns empty dict when no extensions present
    assert result.extensions == {}


def test_build_with_extensions():
    """Test building License with specification extensions (x-* fields)."""
    yaml_content = textwrap.dedent(
        """
        name: Apache 2.0
        url: https://www.apache.org/licenses/LICENSE-2.0.html
        x-spdx-id: Apache-2.0
        x-osi-approved: true
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = license_module.build(root)
    assert isinstance(result, license_module.License)

    assert result.extensions is not None
    assert len(result.extensions) == 2

    # Extensions should be dict[KeySource, ValueSource]
    keys = list(result.extensions.keys())
    assert all(isinstance(k, KeySource) for k in keys)
    assert all(isinstance(v, ValueSource) for v in result.extensions.values())

    # Check extension values
    ext_dict = {k.value: v.value for k, v in result.extensions.items()}
    assert ext_dict["x-spdx-id"] == "Apache-2.0"
    assert ext_dict["x-osi-approved"] is True


def test_build_preserves_invalid_types():
    """Test that build preserves values even with 'wrong' types (low-level model principle)."""
    yaml_content = textwrap.dedent(
        """
        name: 12345
        url: true
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = license_module.build(root)
    assert isinstance(result, license_module.License)

    assert result.name is not None
    assert result.url is not None

    # Should preserve the actual values, not convert them
    assert result.name.value == 12345
    assert result.url.value is True


def test_build_with_empty_object():
    """Test building License from empty YAML object."""
    yaml_content = "{}"
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = license_module.build(root)
    assert isinstance(result, license_module.License)

    assert result.root_node == root
    assert result.name is None
    assert result.url is None
    # Extensions returns empty dict when no extensions present
    assert result.extensions == {}


def test_build_with_invalid_node_returns_value_source():
    """Test that build returns ValueSource for non-mapping nodes (preserves invalid data)."""
    yaml_parser = YAML()

    # Scalar node
    scalar_root = yaml_parser.compose("MIT License")
    result = license_module.build(scalar_root)
    assert isinstance(result, ValueSource)
    assert result.value == "MIT License"
    assert result.value_node == scalar_root

    # Sequence node
    sequence_root = yaml_parser.compose("['MIT', 'Apache']")
    result = license_module.build(sequence_root)
    assert isinstance(result, ValueSource)
    assert result.value == ["MIT", "Apache"]
    assert result.value_node == sequence_root


def test_build_with_custom_context():
    """Test building License with a custom context."""
    yaml_content = textwrap.dedent(
        """
        name: BSD-3-Clause
        url: https://opensource.org/licenses/BSD-3-Clause
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    custom_context = Context()
    result = license_module.build(root, context=custom_context)
    assert isinstance(result, license_module.License)

    assert result.name is not None
    assert result.url is not None
    assert result.name.value == "BSD-3-Clause"
    assert result.url.value == "https://opensource.org/licenses/BSD-3-Clause"


def test_source_tracking():
    """Test that source location information is preserved."""
    yaml_content = textwrap.dedent(
        """
        name: GPL-3.0
        url: https://www.gnu.org/licenses/gpl-3.0.html
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = license_module.build(root)
    assert isinstance(result, license_module.License)

    assert result.name is not None
    assert result.url is not None

    # Check that key_node and value_node are tracked
    assert result.name.key_node is not None
    assert result.name.value_node is not None
    assert result.url.key_node is not None
    assert result.url.value_node is not None

    # The key_nodes should contain the field names
    assert result.name.key_node.value == "name"
    assert result.url.key_node.value == "url"

    # The value_nodes should contain the actual values
    assert result.name.value_node.value == "GPL-3.0"
    assert result.url.value_node.value == "https://www.gnu.org/licenses/gpl-3.0.html"

    # Check line numbers are available (for error reporting)
    assert hasattr(result.name.key_node.start_mark, "line")
    assert hasattr(result.name.value_node.start_mark, "line")


def test_mixed_extensions_and_fixed_fields():
    """Test that extensions and fixed fields are properly separated."""
    yaml_content = textwrap.dedent(
        """
        name: MIT
        x-custom: value
        url: https://opensource.org/licenses/MIT
        x-another: 123
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = license_module.build(root)
    assert isinstance(result, license_module.License)

    assert result.name is not None
    assert result.url is not None

    # Fixed fields should be present
    assert result.name.value == "MIT"
    assert result.url.value == "https://opensource.org/licenses/MIT"

    # Extensions should be in extensions dict
    assert result.extensions is not None
    assert len(result.extensions) == 2

    ext_dict = {k.value: v.value for k, v in result.extensions.items()}
    assert ext_dict["x-custom"] == "value"
    assert ext_dict["x-another"] == 123


def test_common_open_source_licenses():
    """Test that License handles common open source licenses."""
    test_cases = [
        ("MIT", "https://opensource.org/licenses/MIT"),
        ("Apache-2.0", "https://www.apache.org/licenses/LICENSE-2.0.html"),
        ("GPL-3.0-or-later", "https://www.gnu.org/licenses/gpl-3.0.html"),
        ("BSD-2-Clause", "https://opensource.org/licenses/BSD-2-Clause"),
        ("ISC", "https://opensource.org/licenses/ISC"),
        ("LGPL-3.0-only", "https://www.gnu.org/licenses/lgpl-3.0.html"),
    ]

    yaml_parser = YAML()

    for name, url in test_cases:
        yaml_content = f"name: {name}\nurl: {url}"
        root = yaml_parser.compose(yaml_content)
        result = license_module.build(root)

        assert isinstance(result, license_module.License)
        assert result.name is not None
        assert result.name.value == name
        assert result.url is not None
        assert result.url.value == url


def test_null_url_value():
    """Test handling of explicit null url value."""
    yaml_content = textwrap.dedent(
        """
        name: Proprietary
        url: null
        """
    )
    yaml_parser = YAML()
    root = yaml_parser.compose(yaml_content)

    result = license_module.build(root)
    assert isinstance(result, license_module.License)

    assert result.name is not None
    assert result.name.value == "Proprietary"

    # Null value should be preserved
    assert result.url is not None
    assert result.url.value is None


def test_various_url_formats():
    """Test that License preserves various URL formats."""
    test_cases = [
        "https://opensource.org/licenses/MIT",
        "http://www.apache.org/licenses/LICENSE-2.0",
        "https://spdx.org/licenses/Apache-2.0.html",
        "https://choosealicense.com/licenses/mit/",
    ]

    yaml_parser = YAML()

    for url in test_cases:
        yaml_content = f"name: Test License\nurl: {url}"
        root = yaml_parser.compose(yaml_content)
        result = license_module.build(root)

        assert isinstance(result, license_module.License)
        assert result.url is not None
        assert result.url.value == url
