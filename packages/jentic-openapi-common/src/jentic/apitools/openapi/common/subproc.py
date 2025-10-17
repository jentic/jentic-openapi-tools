"""Subprocess execution utilities for OpenAPI tools."""

import subprocess
from collections.abc import Sequence
from dataclasses import dataclass


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

    Returns
    -------
    (stdout, stderr, returncode): SubprocessExecutionResult
    """
    try:
        completed_process = subprocess.run(
            cmd,
            check=False,
            capture_output=True,
            text=True,
            shell=False,
            encoding=encoding,  # ensure the CompletedProcess has stdout/stderr
            errors=errors,
            timeout=timeout,
            cwd=cwd,
        )
    except subprocess.TimeoutExpired as e:
        stdout = e.stdout.decode(encoding, errors) if isinstance(e.stdout, bytes) else e.stdout
        stderr = e.stderr.decode(encoding, errors) if isinstance(e.stderr, bytes) else e.stderr
        raise SubprocessExecutionError(cmd, -1, stdout, stderr) from e
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
