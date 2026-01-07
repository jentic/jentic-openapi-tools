"""Subprocess execution utilities for OpenAPI tools."""

import subprocess
from collections.abc import Sequence
from dataclasses import dataclass
from typing import IO, Any, Mapping


__all__ = ["run_subprocess", "SubprocessExecutionResult", "SubprocessExecutionError"]


@dataclass
class SubprocessExecutionResult:
    """Returned by a subprocess."""

    returncode: int
    stdout: str = ""
    stderr: str = ""

    def __init__(
        self,
        returncode: int,
        stdout: str | None = None,
        stderr: str | None = None,
    ):
        self.returncode = returncode
        self.stdout = stdout if isinstance(stdout, str) else ""
        self.stderr = stderr if isinstance(stderr, str) else ""


class SubprocessExecutionError(RuntimeError):
    """Raised when a subprocess exits with non-zero return code."""

    def __init__(
        self,
        cmd: Sequence[str],
        returncode: int,
        stdout: str | None = None,
        stderr: str | None = None,
    ):
        self.cmd = list(cmd)
        self.returncode = returncode
        self.stdout = stdout if isinstance(stdout, str) else ""
        self.stderr = stderr if isinstance(stderr, str) else ""
        message = (
            f"Command {self.cmd!r} failed with exit code {self.returncode}\n"
            f"--- stdout ---\n{self.stdout}\n"
            f"--- stderr ---\n{self.stderr}"
        )
        super().__init__(message)


def run_subprocess(
    cmd: Sequence[str],
    *,
    fail_on_error: bool = False,
    timeout: float | None = None,
    encoding: str = "utf-8",
    errors: str = "strict",
    cwd: str | None = None,
    env: Mapping[str, str] | None = None,
    stdout: int | IO[Any] | None = None,
    stderr: int | IO[Any] | None = None,
) -> SubprocessExecutionResult:
    """
    Run a subprocess command and return (stdout, stderr) as text.
    Raises SubprocessExecutionError if the command fails.

    Parameters
    ----------
    cmd : sequence of str
        The command and its arguments.
    fail_on_error : bool
        If True, raises SubprocessExecutionError for non-zero return codes.
    timeout : float | None
        Seconds before timing out.
    encoding : str
        Passed to subprocess.run so stdout/stderr are decoded as text.
    errors : str
        Error handler for text decoding.
    cwd : str | None
        Working directory for the subprocess.
    env : Mapping[str, str] | None
        These are used instead of the default behavior of inheriting the current process’ environment
    stdout : int | IO[Any] | None
        Optional stdout destination. Can be subprocess.PIPE (default), subprocess.DEVNULL,
        an open file object, or None. When redirected to a file, result.stdout will be empty.
    stderr : int | IO[Any] | None
        Optional stderr destination. Can be subprocess.PIPE (default), subprocess.DEVNULL,
        an open file object, or None. When redirected to a file, result.stderr will be empty.

    Returns
    -------
    (stdout, stderr, returncode): SubprocessExecutionResult
        Note: If stdout/stderr are redirected to a file, the corresponding result fields
        will be empty strings.
    """
    try:
        # If both stdout and stderr are None, use capture_output for simplicity
        if stdout is None and stderr is None:
            completed_process = subprocess.run(
                cmd,
                check=False,
                capture_output=True,
                text=True,
                shell=False,
                encoding=encoding,
                errors=errors,
                timeout=timeout,
                cwd=cwd,
                env=env,
            )
        else:
            # Use explicit stdout/stderr with defaults to PIPE if not specified
            completed_process = subprocess.run(
                cmd,
                check=False,
                stdout=stdout if stdout is not None else subprocess.PIPE,
                stderr=stderr if stderr is not None else subprocess.PIPE,
                text=True,
                shell=False,
                encoding=encoding,
                errors=errors,
                timeout=timeout,
                cwd=cwd,
                env=env,
            )
    except subprocess.TimeoutExpired as e:
        timeout_stdout = (
            e.stdout.decode(encoding, errors) if isinstance(e.stdout, bytes) else e.stdout
        )
        timeout_stderr = (
            e.stderr.decode(encoding, errors) if isinstance(e.stderr, bytes) else e.stderr
        )
        raise SubprocessExecutionError(cmd, -1, timeout_stdout, timeout_stderr) from e
    except OSError as e:  # e.g., executable not found, permission denied
        raise SubprocessExecutionError(cmd, -1, None, str(e)) from e

    if completed_process.returncode != 0 and fail_on_error:
        raise SubprocessExecutionError(
            cmd,
            completed_process.returncode,
            completed_process.stdout,
            completed_process.stderr,
        )

    # At this point CompletedProcess stdout/stderr are str due to text=True + encoding
    return SubprocessExecutionResult(
        completed_process.returncode, completed_process.stdout, completed_process.stderr
    )
