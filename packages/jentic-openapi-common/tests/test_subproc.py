import platform
import sys

import pytest

from jentic.apitools.openapi.common.subproc import (
    SubprocessExecutionError,
    SubprocessExecutionResult,
    run_subprocess,
)


@pytest.fixture
def is_windows():
    """Check if running on Windows."""
    return platform.system() == "Windows"


@pytest.fixture
def is_unix():
    """Check if running on Unix-like system."""
    return platform.system() in ("Linux", "Darwin")


@pytest.mark.skipif(
    platform.system() not in ("Linux", "Darwin", "Windows"),
    reason="Requires a supported operating system",
)
def test_successful_command(is_windows):
    """Test running a successful command."""
    if is_windows:
        cmd = ["cmd", "/c", "echo", "hello"]
    else:
        cmd = ["echo", "hello"]

    result = run_subprocess(cmd)

    assert isinstance(result, SubprocessExecutionResult)
    assert result.returncode == 0
    assert "hello" in result.stdout
    assert result.stderr == ""


@pytest.mark.skipif(
    platform.system() not in ("Linux", "Darwin"), reason="Requires Unix-like system"
)
def test_unix_ls_command():
    """Test ls command on Unix systems."""
    result = run_subprocess(["ls", "/"])

    assert result.returncode == 0
    assert isinstance(result.stdout, str)
    assert len(result.stdout) > 0


@pytest.mark.skipif(platform.system() != "Windows", reason="Requires Windows system")
def test_windows_dir_command():
    """Test dir command on Windows systems."""
    result = run_subprocess(["cmd", "/c", "dir", "C:\\"])

    assert result.returncode == 0
    assert isinstance(result.stdout, str)
    assert len(result.stdout) > 0


@pytest.mark.skipif(
    platform.system() not in ("Linux", "Darwin", "Windows"),
    reason="Requires a supported operating system",
)
def test_python_version_command():
    """Test running python --version command."""
    # Use sys.executable to ensure we're using the right Python
    result = run_subprocess([sys.executable, "--version"])

    assert result.returncode == 0
    assert "Python" in result.stdout


def test_nonexistent_command():
    """Test running a command that doesn't exist."""
    with pytest.raises(SubprocessExecutionError) as exc_info:
        run_subprocess(["nonexistent_command_12345"])

    assert exc_info.value.returncode == -1
    assert exc_info.value.cmd == ["nonexistent_command_12345"]


@pytest.mark.skipif(
    platform.system() not in ("Linux", "Darwin", "Windows"),
    reason="Requires a supported operating system",
)
def test_command_with_non_zero_exit_code(is_windows):
    """Test command that exits with non-zero code."""
    if is_windows:
        cmd = ["cmd", "/c", "exit", "1"]
    else:
        cmd = ["sh", "-c", "exit 1"]

    # Without fail_on_error, should not raise exception
    result = run_subprocess(cmd)
    assert result.returncode == 1

    # With fail_on_error=True, should raise exception
    with pytest.raises(SubprocessExecutionError) as exc_info:
        run_subprocess(cmd, fail_on_error=True)

    assert exc_info.value.returncode == 1
    assert exc_info.value.cmd == cmd


@pytest.mark.skipif(
    platform.system() not in ("Linux", "Darwin"),
    reason="Requires Unix-like system for stderr test",
)
def test_command_with_stderr():
    """Test command that produces stderr output."""
    # Use a command that writes to stderr
    result = run_subprocess(["sh", "-c", "echo 'error message' >&2"])

    assert result.returncode == 0
    assert result.stdout == ""
    assert "error message" in result.stderr


def test_encoding_parameter(is_windows):
    """Test custom encoding parameter."""
    if is_windows:
        cmd = ["cmd", "/c", "echo", "hello"]
    else:
        cmd = ["echo", "hello"]

    result = run_subprocess(cmd, encoding="utf-8")

    assert result.returncode == 0
    assert "hello" in result.stdout
    assert isinstance(result.stdout, str)


def test_subprocess_execution_result_initialization():
    """Test SubprocessExecutionResult initialization."""
    result = SubprocessExecutionResult(0, "stdout", "stderr")

    assert result.returncode == 0
    assert result.stdout == "stdout"
    assert result.stderr == "stderr"

    # Test with defaults
    result_defaults = SubprocessExecutionResult(1)
    assert result_defaults.returncode == 1
    assert result_defaults.stdout == ""
    assert result_defaults.stderr == ""


def test_subprocess_execution_error_initialization():
    """Test SubprocessExecutionError initialization."""
    cmd = ["test", "command"]
    error = SubprocessExecutionError(cmd, 1, "out", "err")

    assert error.cmd == ["test", "command"]
    assert error.returncode == 1
    assert error.stdout == "out"
    assert error.stderr == "err"

    # Test message formatting
    error_msg = str(error)
    assert "['test', 'command']" in error_msg
    assert "exit code 1" in error_msg
    assert "out" in error_msg
    assert "err" in error_msg


@pytest.mark.skipif(
    platform.system() not in ("Linux", "Darwin"), reason="Requires Unix-like system"
)
def test_empty_command_output():
    """Test command that produces no output."""
    result = run_subprocess(["true"])  # Unix command that does nothing and succeeds

    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


@pytest.mark.skipif(
    platform.system() not in ("Linux", "Darwin", "Windows"),
    reason="Requires a supported operating system",
)
def test_command_with_arguments(is_windows):
    """Test command with multiple arguments."""
    if is_windows:
        cmd = ["cmd", "/c", "echo", "hello", "world"]
    else:
        cmd = ["echo", "hello", "world"]

    result = run_subprocess(cmd)

    assert result.returncode == 0
    assert "hello" in result.stdout
    assert "world" in result.stdout


@pytest.mark.skipif(
    platform.system() not in ("Linux", "Darwin"), reason="Requires Unix-like system"
)
def test_cwd_parameter():
    """Test running command with custom working directory."""
    # Test running 'pwd' command in root directory
    result = run_subprocess(["pwd"], cwd="/")

    assert result.returncode == 0
    assert result.stdout.strip() == "/"


@pytest.mark.skipif(platform.system() != "Windows", reason="Requires Windows system")
def test_cwd_parameter_windows():
    """Test running command with custom working directory on Windows."""
    # Test running 'cd' command in C:\ directory
    result = run_subprocess(["cmd", "/c", "cd"], cwd="C:\\")

    assert result.returncode == 0
    assert "C:\\" in result.stdout


def test_cwd_parameter_with_nonexistent_directory():
    """Test running command with non-existent working directory."""
    with pytest.raises(SubprocessExecutionError) as exc_info:
        run_subprocess(["echo", "test"], cwd="/nonexistent/directory/path")

    assert exc_info.value.returncode == -1


def test_cwd_parameter_none(is_windows):
    """Test that cwd=None works (uses current directory)."""
    if is_windows:
        cmd = ["cmd", "/c", "echo", "test"]
    else:
        cmd = ["echo", "test"]

    result = run_subprocess(cmd, cwd=None)

    assert result.returncode == 0
    assert "test" in result.stdout


@pytest.mark.skipif(
    platform.system() not in ("Linux", "Darwin", "Windows"),
    reason="Requires a supported operating system",
)
def test_timeout_scenario(is_windows):
    """Test command timeout handling."""
    if is_windows:
        # Use timeout command on Windows (if available) or ping with delay
        cmd = ["ping", "-n", "3", "127.0.0.1"]  # Takes ~2 seconds
    else:
        cmd = ["sleep", "2"]  # Takes 2 seconds

    # Test that command times out after 0.5 seconds
    with pytest.raises(SubprocessExecutionError) as exc_info:
        run_subprocess(cmd, timeout=0.5)

    assert exc_info.value.returncode == -1
    # The exception should contain timeout information
    assert "sleep" in " ".join(exc_info.value.cmd) if not is_windows else "ping"


def test_timeout_successful_completion(is_windows):
    """Test that timeout doesn't interfere with commands that complete quickly."""
    if is_windows:
        cmd = ["cmd", "/c", "echo", "quick"]
    else:
        cmd = ["echo", "quick"]

    # Command should complete well within 5 second timeout
    result = run_subprocess(cmd, timeout=5)

    assert result.returncode == 0
    assert "quick" in result.stdout
