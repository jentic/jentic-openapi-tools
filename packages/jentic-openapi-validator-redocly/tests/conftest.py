"""Pytest configuration and fixtures for jentic-openapi-validator-redocly tests."""

from pathlib import Path

import pytest

from jentic.apitools.openapi.validator.backends.redocly import RedoclyValidatorBackend


@pytest.fixture
def fixtures_dir() -> Path:
    """Path to the test fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def openapi_fixtures_dir(fixtures_dir: Path) -> Path:
    """Path to the OpenAPI test fixtures directory."""
    return fixtures_dir / "openapi"


@pytest.fixture
def ruleset_fixtures_dir(fixtures_dir: Path) -> Path:
    """Path to the ruleset test fixtures directory."""
    return fixtures_dir / "rulesets"


@pytest.fixture
def valid_openapi_path(openapi_fixtures_dir: Path) -> Path:
    """Path to a valid OpenAPI document fixture."""
    return openapi_fixtures_dir / "simple_openapi.json"


@pytest.fixture
def invalid_openapi_path(openapi_fixtures_dir: Path) -> Path:
    """Path to an invalid OpenAPI document fixture."""
    return openapi_fixtures_dir / "simple_openapi_invalid.json"


@pytest.fixture
def custom_ruleset_path(ruleset_fixtures_dir: Path) -> Path:
    """Path to a custom Redocly ruleset fixture."""
    return ruleset_fixtures_dir / "custom_redocly.yaml"


@pytest.fixture
def redocly_validator() -> RedoclyValidatorBackend:
    """A default RedoclyValidator instance."""
    return RedoclyValidatorBackend()


@pytest.fixture
def redocly_validator_with_custom_ruleset(custom_ruleset_path: Path) -> RedoclyValidatorBackend:
    """A RedoclyValidator instance with a custom ruleset."""
    return RedoclyValidatorBackend(ruleset_path=str(custom_ruleset_path))


@pytest.fixture
def redocly_validator_with_short_timeout() -> RedoclyValidatorBackend:
    """A RedoclyValidator instance with a short timeout for testing."""
    return RedoclyValidatorBackend(timeout=1.0)


@pytest.fixture
def redocly_validator_with_long_timeout() -> RedoclyValidatorBackend:
    """A RedoclyValidator instance with a long timeout."""
    return RedoclyValidatorBackend(timeout=120.0)
