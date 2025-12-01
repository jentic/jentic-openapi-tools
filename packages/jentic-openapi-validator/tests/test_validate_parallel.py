"""Tests for parallel validation execution."""

import textwrap
import time
from collections.abc import Sequence
from unittest.mock import patch

import pytest

from jentic.apitools.openapi.validator.backends.base import BaseValidatorBackend
from jentic.apitools.openapi.validator.core import OpenAPIValidator
from jentic.apitools.openapi.validator.core.diagnostics import JenticDiagnostic, ValidationResult


class SlowMockBackend(BaseValidatorBackend):
    """Mock backend that simulates slow validation with configurable delay."""

    def __init__(self, delay: float = 0.1, name: str = "mock"):
        self.delay = delay
        self.name = name
        self.call_count = 0

    def validate(
        self, document: str | dict, *, base_url: str | None = None, target: str | None = None
    ) -> ValidationResult:
        self.call_count += 1
        time.sleep(self.delay)
        return ValidationResult(diagnostics=[])

    @staticmethod
    def accepts() -> Sequence[str]:
        return ["dict", "text"]


class MockBackendWithDiagnostics(BaseValidatorBackend):
    """Mock backend that returns specific diagnostics."""

    def __init__(self, diagnostics: list[JenticDiagnostic]):
        self._diagnostics = diagnostics

    def validate(
        self, document: str | dict, *, base_url: str | None = None, target: str | None = None
    ) -> ValidationResult:
        return ValidationResult(diagnostics=self._diagnostics)

    @staticmethod
    def accepts() -> Sequence[str]:
        return ["dict", "text"]


def test_parallel_false_runs_sequentially(valid_openapi_dict):
    """Test that parallel=False (default) runs backends sequentially."""
    backend1 = SlowMockBackend(delay=0.05, name="backend1")
    backend2 = SlowMockBackend(delay=0.05, name="backend2")

    validator = OpenAPIValidator(backends=[backend1, backend2])

    start_time = time.time()
    result = validator.validate(valid_openapi_dict, parallel=False)
    elapsed = time.time() - start_time

    assert result.valid
    assert backend1.call_count == 1
    assert backend2.call_count == 1
    # Sequential execution should take at least 0.1s (0.05 + 0.05)
    # Use 0.09 threshold to account for timing precision on slow systems
    assert elapsed >= 0.09


def test_parallel_true_runs_concurrently(valid_openapi_dict):
    """Test that parallel=True runs backends concurrently."""
    # Use longer delays to make timing differences more reliable
    backend1 = SlowMockBackend(delay=0.3, name="backend1")
    backend2 = SlowMockBackend(delay=0.3, name="backend2")

    validator = OpenAPIValidator(backends=[backend1, backend2])

    start_time = time.time()
    result = validator.validate(valid_openapi_dict, parallel=True)
    elapsed = time.time() - start_time

    assert result.valid
    # Parallel execution should take less than 0.6s (both run concurrently)
    # Sequential would take at least 0.6s, parallel should be around 0.3s + overhead
    # Note: call_count won't be updated because ProcessPoolExecutor pickles backends
    assert elapsed < 0.55, f"Parallel execution took {elapsed:.2f}s, expected < 0.55s"


def test_parallel_single_backend_no_parallelization(valid_openapi_dict):
    """Test that parallel=True with single backend doesn't use parallelization."""
    backend = SlowMockBackend(delay=0.05, name="single")

    validator = OpenAPIValidator(backends=[backend])

    # Should not call asyncio.run for single backend
    with patch("jentic.apitools.openapi.validator.core.openapi_validator.asyncio.run") as mock_run:
        result = validator.validate(valid_openapi_dict, parallel=True)

    assert result.valid
    assert backend.call_count == 1
    # asyncio.run should not be called for single backend
    mock_run.assert_not_called()


def test_parallel_aggregates_diagnostics(valid_openapi_dict):
    """Test that parallel execution aggregates diagnostics from all backends."""
    from lsprotocol import types as lsp

    diag1 = JenticDiagnostic(
        range=lsp.Range(start=lsp.Position(0, 0), end=lsp.Position(0, 1)),
        message="Error from backend 1",
        severity=lsp.DiagnosticSeverity.Error,
    )
    diag2 = JenticDiagnostic(
        range=lsp.Range(start=lsp.Position(1, 0), end=lsp.Position(1, 1)),
        message="Error from backend 2",
        severity=lsp.DiagnosticSeverity.Error,
    )

    backend1 = MockBackendWithDiagnostics([diag1])
    backend2 = MockBackendWithDiagnostics([diag2])

    validator = OpenAPIValidator(backends=[backend1, backend2])
    result = validator.validate(valid_openapi_dict, parallel=True)

    assert len(result.diagnostics) == 2
    messages = [d.message for d in result.diagnostics]
    assert "Error from backend 1" in messages
    assert "Error from backend 2" in messages


def test_parallel_with_max_workers(valid_openapi_dict):
    """Test that max_workers parameter limits concurrency."""
    # 4 backends with 0.2s delay each
    backends: list[BaseValidatorBackend] = [
        SlowMockBackend(delay=0.2, name=f"backend{i}") for i in range(4)
    ]

    validator = OpenAPIValidator(backends=backends)

    start_time = time.time()
    # With max_workers=2, should process 4 backends with 2 at a time
    # This means 2 batches of 0.2s each = ~0.4s total
    result = validator.validate(valid_openapi_dict, parallel=True, max_workers=2)
    elapsed = time.time() - start_time

    assert result.valid
    # With max_workers=2 and 4 backends: 2 batches of 2 parallel executions
    # Expected time: ~0.4s (2 batches × 0.2s)
    # Sequential would be: 4 × 0.2s = 0.8s
    # Note: call_count won't be updated because ProcessPoolExecutor pickles backends
    assert elapsed < 0.7, f"Parallel execution with max_workers=2 took {elapsed:.2f}s"


def test_default_parallel_is_false(valid_openapi_dict):
    """Test that parallel defaults to False."""
    backend1 = SlowMockBackend(delay=0.05, name="backend1")
    backend2 = SlowMockBackend(delay=0.05, name="backend2")

    validator = OpenAPIValidator(backends=[backend1, backend2])

    start_time = time.time()
    result = validator.validate(valid_openapi_dict)  # No parallel argument
    elapsed = time.time() - start_time

    assert result.valid
    # Default is sequential, so should take at least 0.1s
    # Use 0.09 threshold to account for timing precision on slow systems
    assert elapsed >= 0.09


def test_parallel_with_string_document(valid_openapi_string):
    """Test parallel execution with string document input."""
    backend1 = SlowMockBackend(delay=0.1, name="backend1")
    backend2 = SlowMockBackend(delay=0.1, name="backend2")

    validator = OpenAPIValidator(backends=[backend1, backend2])

    start_time = time.time()
    result = validator.validate(valid_openapi_string, parallel=True)
    elapsed = time.time() - start_time

    assert result.valid
    # Should be faster than sequential (0.2s)
    assert elapsed < 0.18


def test_parallel_with_real_backends_returns_diagnostics():
    """Test parallel execution with real backends returns aggregated diagnostics."""
    # Invalid OpenAPI document missing required fields
    invalid_doc = {
        "openapi": "3.1.0",
        "info": {"title": "Test API"},  # Missing version
        # Missing paths
    }

    # Use default and openapi-spec backends
    validator = OpenAPIValidator(backends=["default", "openapi-spec"])

    # Sequential execution
    result_seq = validator.validate(invalid_doc, parallel=False)
    assert not result_seq.valid
    assert len(result_seq.diagnostics) >= 2  # Each backend should report at least one issue

    # Verify diagnostics come from both backends by checking source field
    seq_sources = {d.source for d in result_seq.diagnostics}
    assert "default-validator" in seq_sources, (
        f"Expected 'default-validator' in sources, got: {seq_sources}"
    )
    assert "openapi-spec-validator" in seq_sources, (
        f"Expected 'openapi-spec-validator' in sources, got: {seq_sources}"
    )

    # Parallel execution
    result_par = validator.validate(invalid_doc, parallel=True)
    assert not result_par.valid
    assert len(result_par.diagnostics) >= 2  # Each backend should report at least one issue

    # Verify diagnostics come from both backends by checking source field
    par_sources = {d.source for d in result_par.diagnostics}
    assert "default-validator" in par_sources, (
        f"Expected 'default-validator' in sources, got: {par_sources}"
    )
    assert "openapi-spec-validator" in par_sources, (
        f"Expected 'openapi-spec-validator' in sources, got: {par_sources}"
    )

    # Both should return the same number of diagnostics (order may differ)
    assert len(result_seq.diagnostics) == len(result_par.diagnostics)


@pytest.mark.requires_redocly_cli
@pytest.mark.requires_spectral_cli
def test_parallel_with_all_backends_returns_diagnostics(tmp_path):
    """Test parallel execution with all backends (including Redocly and Spectral)."""
    # Create a temporary file for backends that require file URIs
    invalid_yaml = textwrap.dedent(
        """\
        openapi: "3.1.0"
        info:
          title: Test API
        """
    )
    yaml_file = tmp_path / "invalid_api.yaml"
    yaml_file.write_text(invalid_yaml)
    file_uri = f"file://{yaml_file}"

    # Use all available backends
    validator = OpenAPIValidator(backends=["default", "openapi-spec", "redocly", "spectral"])

    # Sequential execution
    result_seq = validator.validate(file_uri, parallel=False)
    assert not result_seq.valid

    # Verify diagnostics come from all backends by checking source field
    seq_sources = {d.source for d in result_seq.diagnostics}
    assert "default-validator" in seq_sources, (
        f"Expected 'default-validator' in sources, got: {seq_sources}"
    )
    assert "openapi-spec-validator" in seq_sources, (
        f"Expected 'openapi-spec-validator' in sources, got: {seq_sources}"
    )
    assert "redocly-validator" in seq_sources, (
        f"Expected 'redocly-validator' in sources, got: {seq_sources}"
    )
    assert "spectral-validator" in seq_sources, (
        f"Expected 'spectral-validator' in sources, got: {seq_sources}"
    )

    # Parallel execution
    result_par = validator.validate(file_uri, parallel=True)
    assert not result_par.valid

    # Verify diagnostics come from all backends by checking source field
    par_sources = {d.source for d in result_par.diagnostics}
    assert "default-validator" in par_sources, (
        f"Expected 'default-validator' in sources, got: {par_sources}"
    )
    assert "openapi-spec-validator" in par_sources, (
        f"Expected 'openapi-spec-validator' in sources, got: {par_sources}"
    )
    assert "redocly-validator" in par_sources, (
        f"Expected 'redocly-validator' in sources, got: {par_sources}"
    )
    assert "spectral-validator" in par_sources, (
        f"Expected 'spectral-validator' in sources, got: {par_sources}"
    )

    # Both should return the same number of diagnostics (order may differ)
    assert len(result_seq.diagnostics) == len(result_par.diagnostics)
