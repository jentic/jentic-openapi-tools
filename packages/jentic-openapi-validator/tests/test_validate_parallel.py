"""Tests for parallel validation execution."""

import multiprocessing
import textwrap
import time
from collections.abc import Sequence
from unittest.mock import patch

import pytest

from jentic.apitools.openapi.validator.backends.base import BaseValidatorBackend
from jentic.apitools.openapi.validator.core import OpenAPIValidator
from jentic.apitools.openapi.validator.core.diagnostics import JenticDiagnostic, ValidationResult


class SlowMockBackend(BaseValidatorBackend):
    """Mock CPU-bound backend that simulates slow validation with configurable delay."""

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


class SlowMockIOBackend(SlowMockBackend):
    """Mock I/O-bound backend (simulates subprocess-based validators)."""

    @staticmethod
    def execution_type() -> str:
        return "io"


class SlowMockCPUHeavyBackend(SlowMockBackend):
    """Mock cpu-heavy backend (simulates long-running pure-Python analysis).

    Must be picklable for ProcessPoolExecutor with spawn.
    """

    @staticmethod
    def execution_type() -> str:
        return "cpu-heavy"


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


class MockIOBackendWithDiagnostics(MockBackendWithDiagnostics):
    """Mock I/O-bound backend that returns specific diagnostics."""

    @staticmethod
    def execution_type() -> str:
        return "io"


class MockCPUHeavyBackendWithDiagnostics(MockBackendWithDiagnostics):
    """Mock cpu-heavy backend that returns specific diagnostics.

    Must be picklable for ProcessPoolExecutor with spawn.
    """

    @staticmethod
    def execution_type() -> str:
        return "cpu-heavy"


@pytest.fixture
def use_fork_for_process_pool():
    """Patch multiprocessing.get_context in the orchestrator to return fork context.

    ProcessPoolExecutor with spawn context requires child processes to import the
    backend class for unpickling. Test-defined mock backend classes live in
    non-installed test modules, so the spawned process fails to import them.
    Using fork context shares memory with the parent, avoiding the import issue.

    Yields the mock so tests can assert get_context was called with "spawn".
    """
    fork_context = multiprocessing.get_context("fork")
    with patch(
        "jentic.apitools.openapi.validator.core.openapi_validator.multiprocessing.get_context",
        return_value=fork_context,
    ) as mock_get_context:
        yield mock_get_context


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


def test_parallel_true_runs_io_backends_concurrently(valid_openapi_dict):
    """Test that parallel=True runs I/O backends concurrently via ThreadPoolExecutor."""
    delay = 0.3

    # Run sequential first
    validator_seq = OpenAPIValidator(
        backends=[SlowMockIOBackend(delay=delay), SlowMockIOBackend(delay=delay)]
    )
    start_time = time.time()
    result_seq = validator_seq.validate(valid_openapi_dict, parallel=False)
    sequential_time = time.time() - start_time

    # Run parallel — I/O backends go into ThreadPoolExecutor
    validator_par = OpenAPIValidator(
        backends=[SlowMockIOBackend(delay=delay), SlowMockIOBackend(delay=delay)]
    )
    start_time = time.time()
    result_par = validator_par.validate(valid_openapi_dict, parallel=True)
    parallel_time = time.time() - start_time

    assert result_seq.valid
    assert result_par.valid
    # Parallel should be significantly faster than sequential (at least 1.3x faster)
    # With 2 I/O backends of 0.3s each: sequential ~0.6s, parallel ~0.3s + overhead
    assert parallel_time < sequential_time * 0.85, (
        f"Parallel ({parallel_time:.2f}s) should be faster than "
        f"sequential ({sequential_time:.2f}s) by factor of 0.85"
    )


def test_parallel_single_backend_no_parallelization(valid_openapi_dict):
    """Test that parallel=True with single backend doesn't use parallelization."""
    backend = SlowMockBackend(delay=0.05, name="single")

    validator = OpenAPIValidator(backends=[backend])

    # Should not create ThreadPoolExecutor for single backend
    with patch(
        "jentic.apitools.openapi.validator.core.openapi_validator.ThreadPoolExecutor"
    ) as mock_executor:
        result = validator.validate(valid_openapi_dict, parallel=True)

    assert result.valid
    assert backend.call_count == 1
    # ThreadPoolExecutor should not be created for single backend
    mock_executor.assert_not_called()


def test_parallel_aggregates_diagnostics(valid_openapi_dict):
    """Test that parallel execution aggregates diagnostics from mixed backend types."""
    from lsprotocol import types as lsp

    diag1 = JenticDiagnostic(
        range=lsp.Range(start=lsp.Position(0, 0), end=lsp.Position(0, 1)),
        message="Error from CPU backend",
        severity=lsp.DiagnosticSeverity.Error,
    )
    diag2 = JenticDiagnostic(
        range=lsp.Range(start=lsp.Position(1, 0), end=lsp.Position(1, 1)),
        message="Error from IO backend",
        severity=lsp.DiagnosticSeverity.Error,
    )

    backend_cpu = MockBackendWithDiagnostics([diag1])
    backend_io = MockIOBackendWithDiagnostics([diag2])

    validator = OpenAPIValidator(backends=[backend_cpu, backend_io])
    result = validator.validate(valid_openapi_dict, parallel=True)

    assert len(result.diagnostics) == 2
    messages = [d.message for d in result.diagnostics]
    assert "Error from CPU backend" in messages
    assert "Error from IO backend" in messages


def test_parallel_with_max_workers(valid_openapi_dict):
    """Test that max_workers parameter limits concurrency for I/O backends."""
    delay = 0.2
    num_backends = 4

    # Run sequential first
    backends_seq: list[BaseValidatorBackend] = [
        SlowMockIOBackend(delay=delay, name=f"backend{i}") for i in range(num_backends)
    ]
    validator_seq = OpenAPIValidator(backends=backends_seq)
    start_time = time.time()
    result_seq = validator_seq.validate(valid_openapi_dict, parallel=False)
    sequential_time = time.time() - start_time

    # Run parallel with max_workers=2
    backends_par: list[BaseValidatorBackend] = [
        SlowMockIOBackend(delay=delay, name=f"backend{i}") for i in range(num_backends)
    ]
    validator_par = OpenAPIValidator(backends=backends_par)
    start_time = time.time()
    # With max_workers=2, should process 4 I/O backends with 2 at a time
    # This means 2 batches of 0.2s each = ~0.4s total
    result_par = validator_par.validate(valid_openapi_dict, parallel=True, max_workers=2)
    parallel_time = time.time() - start_time

    assert result_seq.valid
    assert result_par.valid
    # With max_workers=2 and 4 I/O backends:
    # - Sequential: 4 × delay = 4 × 0.2s = 0.8s
    # - Parallel: 2 batches × delay = 2 × 0.2s = ~0.4s + overhead
    # Parallel should be at least 1.3x faster (factor of ~0.77)
    assert parallel_time < sequential_time * 0.85, (
        f"Parallel with max_workers=2 ({parallel_time:.2f}s) should be faster than "
        f"sequential ({sequential_time:.2f}s) by factor of 0.85"
    )


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
    """Test parallel execution with string document input is faster than sequential."""
    delay = 0.15

    # Run sequential first (I/O backends to get thread parallelism)
    validator_seq = OpenAPIValidator(
        backends=[SlowMockIOBackend(delay=delay), SlowMockIOBackend(delay=delay)]
    )
    start_time = time.time()
    result_seq = validator_seq.validate(valid_openapi_string, parallel=False)
    sequential_time = time.time() - start_time

    # Run parallel
    validator_par = OpenAPIValidator(
        backends=[SlowMockIOBackend(delay=delay), SlowMockIOBackend(delay=delay)]
    )
    start_time = time.time()
    result_par = validator_par.validate(valid_openapi_string, parallel=True)
    parallel_time = time.time() - start_time

    assert result_seq.valid
    assert result_par.valid
    # Parallel should be significantly faster than sequential
    assert parallel_time < sequential_time * 0.85, (
        f"Parallel ({parallel_time:.2f}s) should be faster than "
        f"sequential ({sequential_time:.2f}s) by factor of 0.85"
    )


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


# --- GIL-aware scheduling tests ---


def test_execution_type_default_is_cpu():
    """Test that BaseValidatorBackend.execution_type() defaults to 'cpu'."""
    backend = SlowMockBackend()
    assert backend.execution_type() == "cpu"
    assert SlowMockBackend.execution_type() == "cpu"


def test_execution_type_io_override():
    """Test that I/O backends return 'io' from execution_type()."""
    backend = SlowMockIOBackend()
    assert backend.execution_type() == "io"
    assert SlowMockIOBackend.execution_type() == "io"


def test_all_cpu_backends_no_thread_pool(valid_openapi_dict):
    """Test that all-CPU backends skip ThreadPoolExecutor even with parallel=True."""
    backend1 = SlowMockBackend(delay=0.05, name="cpu1")
    backend2 = SlowMockBackend(delay=0.05, name="cpu2")

    validator = OpenAPIValidator(backends=[backend1, backend2])

    with patch(
        "jentic.apitools.openapi.validator.core.openapi_validator.ThreadPoolExecutor"
    ) as mock_executor:
        result = validator.validate(valid_openapi_dict, parallel=True)

    assert result.valid
    # All backends are CPU-bound, so ThreadPoolExecutor should not be created
    mock_executor.assert_not_called()


def test_cpu_backends_run_sequentially_when_parallel(valid_openapi_dict):
    """Test that CPU backends run sequentially (not in threads) even with parallel=True."""
    delay = 0.15
    backend1 = SlowMockBackend(delay=delay, name="cpu1")
    backend2 = SlowMockBackend(delay=delay, name="cpu2")

    validator = OpenAPIValidator(backends=[backend1, backend2])

    start_time = time.time()
    result = validator.validate(valid_openapi_dict, parallel=True)
    elapsed = time.time() - start_time

    assert result.valid
    # CPU backends run sequentially: should take at least 2 × delay
    assert elapsed >= delay * 2 * 0.9, (
        f"CPU backends should run sequentially ({elapsed:.2f}s < {delay * 2:.2f}s expected)"
    )


def test_mixed_backends_concurrent_execution(valid_openapi_dict):
    """Test that mixed I/O and CPU backends overlap: CPU runs in main thread
    while I/O runs in background threads."""
    io_delay = 0.3
    cpu_delay = 0.1

    io_backend = SlowMockIOBackend(delay=io_delay, name="io1")
    cpu_backend1 = SlowMockBackend(delay=cpu_delay, name="cpu1")
    cpu_backend2 = SlowMockBackend(delay=cpu_delay, name="cpu2")

    validator = OpenAPIValidator(backends=[io_backend, cpu_backend1, cpu_backend2])

    start_time = time.time()
    result = validator.validate(valid_openapi_dict, parallel=True)
    elapsed = time.time() - start_time

    assert result.valid
    # I/O backend (0.3s) runs in a thread while CPU backends (0.1+0.1=0.2s)
    # run sequentially in main thread. Total should be ~max(0.3, 0.2) = ~0.3s,
    # not 0.3+0.1+0.1=0.5s (fully sequential)
    fully_sequential = io_delay + cpu_delay * 2
    assert elapsed < fully_sequential * 0.85, (
        f"Mixed execution ({elapsed:.2f}s) should overlap I/O and CPU work, "
        f"not be fully sequential ({fully_sequential:.2f}s)"
    )


def test_mixed_backends_aggregates_all_diagnostics(valid_openapi_dict):
    """Test that mixed scheduling aggregates diagnostics from both I/O and CPU backends."""
    from lsprotocol import types as lsp

    diag_cpu1 = JenticDiagnostic(
        range=lsp.Range(start=lsp.Position(0, 0), end=lsp.Position(0, 1)),
        message="CPU error 1",
        severity=lsp.DiagnosticSeverity.Error,
    )
    diag_cpu2 = JenticDiagnostic(
        range=lsp.Range(start=lsp.Position(1, 0), end=lsp.Position(1, 1)),
        message="CPU error 2",
        severity=lsp.DiagnosticSeverity.Warning,
    )
    diag_io = JenticDiagnostic(
        range=lsp.Range(start=lsp.Position(2, 0), end=lsp.Position(2, 1)),
        message="IO error",
        severity=lsp.DiagnosticSeverity.Error,
    )

    cpu1 = MockBackendWithDiagnostics([diag_cpu1])
    cpu2 = MockBackendWithDiagnostics([diag_cpu2])
    io1 = MockIOBackendWithDiagnostics([diag_io])

    validator = OpenAPIValidator(backends=[cpu1, cpu2, io1])
    result = validator.validate(valid_openapi_dict, parallel=True)

    assert len(result.diagnostics) == 3
    messages = {d.message for d in result.diagnostics}
    assert messages == {"CPU error 1", "CPU error 2", "IO error"}


# --- cpu-heavy (ProcessPoolExecutor) scheduling tests ---


def test_execution_type_cpu_heavy_override():
    """Test that cpu-heavy backends return 'cpu-heavy' from execution_type()."""
    backend = SlowMockCPUHeavyBackend()
    assert backend.execution_type() == "cpu-heavy"
    assert SlowMockCPUHeavyBackend.execution_type() == "cpu-heavy"


def test_no_process_pool_without_cpu_heavy_backends(valid_openapi_dict):
    """Test that ProcessPoolExecutor is not created when no cpu-heavy backends are present."""
    io_backend = SlowMockIOBackend(delay=0.05, name="io1")
    cpu_backend = SlowMockBackend(delay=0.05, name="cpu1")

    validator = OpenAPIValidator(backends=[io_backend, cpu_backend])

    with patch(
        "jentic.apitools.openapi.validator.core.openapi_validator.ProcessPoolExecutor"
    ) as mock_process_exec:
        result = validator.validate(valid_openapi_dict, parallel=True)

    assert result.valid
    mock_process_exec.assert_not_called()


def test_all_cpu_backends_no_process_pool(valid_openapi_dict):
    """Test that neither executor is created when all backends are fast CPU."""
    backend1 = SlowMockBackend(delay=0.05, name="cpu1")
    backend2 = SlowMockBackend(delay=0.05, name="cpu2")

    validator = OpenAPIValidator(backends=[backend1, backend2])

    with (
        patch(
            "jentic.apitools.openapi.validator.core.openapi_validator.ThreadPoolExecutor"
        ) as mock_thread_exec,
        patch(
            "jentic.apitools.openapi.validator.core.openapi_validator.ProcessPoolExecutor"
        ) as mock_process_exec,
    ):
        result = validator.validate(valid_openapi_dict, parallel=True)

    assert result.valid
    mock_thread_exec.assert_not_called()
    mock_process_exec.assert_not_called()


def test_cpu_heavy_backends_use_process_pool(valid_openapi_dict, use_fork_for_process_pool):
    """Test that cpu-heavy backends are dispatched to ProcessPoolExecutor."""
    heavy1 = SlowMockCPUHeavyBackend(delay=0.05, name="heavy1")
    heavy2 = SlowMockCPUHeavyBackend(delay=0.05, name="heavy2")

    validator = OpenAPIValidator(backends=[heavy1, heavy2])

    # Verify ProcessPoolExecutor is created with correct kwargs
    original_ppe = __import__(
        "concurrent.futures", fromlist=["ProcessPoolExecutor"]
    ).ProcessPoolExecutor

    ppe_init_kwargs = {}

    class SpyProcessPoolExecutor(original_ppe):
        def __init__(self, *args, **kwargs):
            ppe_init_kwargs.update(kwargs)
            super().__init__(*args, **kwargs)

    with patch(
        "jentic.apitools.openapi.validator.core.openapi_validator.ProcessPoolExecutor",
        SpyProcessPoolExecutor,
    ):
        result = validator.validate(valid_openapi_dict, parallel=True)

    assert result.valid
    assert ppe_init_kwargs.get("max_workers") == 2
    assert ppe_init_kwargs.get("mp_context") is not None
    # Verify the orchestrator requested "spawn" context (patched to fork for testability)
    use_fork_for_process_pool.assert_called_once_with("spawn")


def test_cpu_heavy_backends_run_concurrently(valid_openapi_dict, use_fork_for_process_pool):
    """Test that cpu-heavy backends achieve true parallelism via ProcessPoolExecutor."""
    delay = 1.5

    # Sequential baseline
    validator_seq = OpenAPIValidator(
        backends=[
            SlowMockCPUHeavyBackend(delay=delay),
            SlowMockCPUHeavyBackend(delay=delay),
        ]
    )
    start_time = time.time()
    result_seq = validator_seq.validate(valid_openapi_dict, parallel=False)
    sequential_time = time.time() - start_time

    # Parallel execution — cpu-heavy backends go into ProcessPoolExecutor
    validator_par = OpenAPIValidator(
        backends=[
            SlowMockCPUHeavyBackend(delay=delay),
            SlowMockCPUHeavyBackend(delay=delay),
        ]
    )
    start_time = time.time()
    result_par = validator_par.validate(valid_openapi_dict, parallel=True)
    parallel_time = time.time() - start_time

    assert result_seq.valid
    assert result_par.valid
    # Sequential: ~3.0s (2 × 1.5s). Parallel: ~1.5s + spawn overhead (~1-2s).
    # Parallel should still be faster than sequential.
    assert parallel_time < sequential_time * 0.9, (
        f"Parallel cpu-heavy ({parallel_time:.2f}s) should be faster than "
        f"sequential ({sequential_time:.2f}s)"
    )


def test_three_tier_mixed_execution(valid_openapi_dict, use_fork_for_process_pool):
    """Test that all three tiers (io, cpu, cpu-heavy) execute simultaneously."""
    io_delay = 1.0
    cpu_delay = 0.2
    heavy_delay = 2.0

    # Sequential baseline
    validator_seq = OpenAPIValidator(
        backends=[
            SlowMockIOBackend(delay=io_delay, name="io1"),
            SlowMockBackend(delay=cpu_delay, name="cpu1"),
            SlowMockCPUHeavyBackend(delay=heavy_delay, name="heavy1"),
        ]
    )
    start_time = time.time()
    result_seq = validator_seq.validate(valid_openapi_dict, parallel=False)
    sequential_time = time.time() - start_time

    # Parallel — all three tiers execute simultaneously
    validator_par = OpenAPIValidator(
        backends=[
            SlowMockIOBackend(delay=io_delay, name="io1"),
            SlowMockBackend(delay=cpu_delay, name="cpu1"),
            SlowMockCPUHeavyBackend(delay=heavy_delay, name="heavy1"),
        ]
    )
    start_time = time.time()
    result_par = validator_par.validate(valid_openapi_dict, parallel=True)
    parallel_time = time.time() - start_time

    assert result_seq.valid
    assert result_par.valid
    # Sequential: io + cpu + heavy = 1.0 + 0.2 + 2.0 = 3.2s
    # Parallel: max(io, cpu, heavy + spawn) ≈ 2.0 + spawn_overhead
    # Parallel should be noticeably faster than sequential
    assert parallel_time < sequential_time * 0.9, (
        f"Three-tier parallel ({parallel_time:.2f}s) should be faster than "
        f"sequential ({sequential_time:.2f}s)"
    )


def test_three_tier_aggregates_all_diagnostics(valid_openapi_dict, use_fork_for_process_pool):
    """Test that diagnostics from all three tiers are aggregated correctly."""
    from lsprotocol import types as lsp

    diag_cpu = JenticDiagnostic(
        range=lsp.Range(start=lsp.Position(0, 0), end=lsp.Position(0, 1)),
        message="CPU error",
        severity=lsp.DiagnosticSeverity.Error,
    )
    diag_io = JenticDiagnostic(
        range=lsp.Range(start=lsp.Position(1, 0), end=lsp.Position(1, 1)),
        message="IO error",
        severity=lsp.DiagnosticSeverity.Warning,
    )
    diag_heavy = JenticDiagnostic(
        range=lsp.Range(start=lsp.Position(2, 0), end=lsp.Position(2, 1)),
        message="CPU-heavy error",
        severity=lsp.DiagnosticSeverity.Error,
    )

    cpu = MockBackendWithDiagnostics([diag_cpu])
    io = MockIOBackendWithDiagnostics([diag_io])
    heavy = MockCPUHeavyBackendWithDiagnostics([diag_heavy])

    validator = OpenAPIValidator(backends=[cpu, io, heavy])
    result = validator.validate(valid_openapi_dict, parallel=True)

    assert len(result.diagnostics) == 3
    messages = {d.message for d in result.diagnostics}
    assert messages == {"CPU error", "IO error", "CPU-heavy error"}
