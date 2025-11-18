"""Shared pytest fixtures for jentic-openapi-datamodels tests."""

import pytest

from jentic.apitools.openapi.parser.backends.ruamel_ast import MappingNode
from jentic.apitools.openapi.parser.core import OpenAPIParser


@pytest.fixture
def parse_yaml():
    """Fixture that provides a YAML parser function.

    Returns a function that parses YAML content and returns a MappingNode.
    Uses the ruamel-ast backend to preserve source location information.

    Example:
        def test_something(parse_yaml):
            root = parse_yaml("key: value")
            # root is a MappingNode
    """
    parser = OpenAPIParser("ruamel-ast")

    def _parse(yaml_content: str) -> MappingNode:
        return parser.parse(yaml_content, return_type=MappingNode)

    return _parse
