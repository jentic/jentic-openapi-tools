"""Pytest configuration and fixtures for jentic-openapi-parser tests."""

from pathlib import Path

import pytest

from jentic.apitools.openapi.parser.core import OpenAPIParser


@pytest.fixture
def fixtures_dir() -> Path:
    """Path to the test fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def openapi_fixtures_dir(fixtures_dir: Path) -> Path:
    """Path to the OpenAPI test fixtures directory."""
    return fixtures_dir / "openapi"


@pytest.fixture
def parser() -> OpenAPIParser:
    """A default OpenAPIParser instance."""
    return OpenAPIParser("pyyaml")


@pytest.fixture
def parser_default() -> OpenAPIParser:
    """An OpenAPIParser instance with pyyaml backend (default)."""
    return OpenAPIParser("pyyaml")


@pytest.fixture
def parser_pyyaml() -> OpenAPIParser:
    """An OpenAPIParser instance with pyyaml backend."""
    return OpenAPIParser("pyyaml")


@pytest.fixture
def parser_ruamel() -> OpenAPIParser:
    """An OpenAPIParser instance with ruamel-safe backend."""
    return OpenAPIParser("ruamel-safe")


@pytest.fixture
def parser_ruamel_roundtrip() -> OpenAPIParser:
    """An OpenAPIParser instance with ruamel-roundtrip backend."""
    return OpenAPIParser("ruamel-roundtrip")


@pytest.fixture
def simple_openapi_path(openapi_fixtures_dir: Path) -> Path:
    """Path to a simple OpenAPI document fixture."""
    return openapi_fixtures_dir / "simple_openapi.json"


@pytest.fixture
def simple_openapi_uri(simple_openapi_path: Path) -> str:
    """URI to a simple OpenAPI document fixture."""
    return simple_openapi_path.as_uri()


@pytest.fixture
def simple_openapi_string() -> str:
    """A simple OpenAPI document as JSON string."""
    return '{"openapi":"3.1.0","info":{"title":"x","version":"1.0.0"}}'


@pytest.fixture
def simple_openapi_dict() -> dict:
    """A simple OpenAPI document as dictionary."""
    return {"openapi": "3.1.0", "info": {"title": "x", "version": "1.0.0"}}
