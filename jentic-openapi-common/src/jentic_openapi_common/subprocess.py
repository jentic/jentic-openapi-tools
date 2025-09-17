import subprocess
from typing import Sequence, Optional


class SubprocessExecutionResult:
    """Returned by a subprocess."""

    def __init__(
        self,
        returncode: int,
        stdout: str = "",
        stderr: str = "",
    ):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


class SubprocessExecutionError(RuntimeError):
    """Raised when a subprocess exits with non-zero return code."""

    def __init__(
        self,
        cmd: Sequence[str],
        returncode: int,
        stdout: Optional[str] = None,
        stderr: Optional[str] = None,
    ):
        self.cmd = list(cmd)
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
        message = (
            f"Command {cmd!r} failed with exit code {returncode}\n"
            f"--- stdout ---\n{stdout or ''}\n"
            f"--- stderr ---\n{stderr or ''}"
        )
        super().__init__(message)


def run_checked(
    cmd: Sequence[str],
    *,
    fail_on_error: bool = False,
    timeout: Optional[float] = None,
    encoding: str = "utf-8",
    errors: str = "strict",
) -> SubprocessExecutionResult:
    """
    Run a subprocess command and return (stdout, stderr) as text.
    Raises SubprocessExecutionError if the command fails.

    Parameters
    ----------
    cmd : sequence of str
        The command and its arguments.
    timeout : float | None
        Seconds before timing out.
    encoding : str
        Passed to subprocess.run so stdout/stderr are decoded as text.
    errors : str
        Error handler for text decoding.

    Returns
    -------
    (stdout, stderr, returncode) : SubprocessExecutionResult
    """
    try:
        completed = subprocess.run(
            cmd,
            check=False,
            capture_output=True,
            text=True,
            encoding=encoding,  # ensure CompletedProcess has str stdout/stderr
            errors=errors,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as e:
        # e.stdout / e.stderr are bytes|None even with text=True — normalize to str
        stdout = (
            e.stdout.decode(encoding, errors)
            if isinstance(e.stdout, (bytes, bytearray))
            else (e.stdout or "")
        )
        stderr = (
            e.stderr.decode(encoding, errors)
            if isinstance(e.stderr, (bytes, bytearray))
            else (e.stderr or "")
        )
        raise SubprocessExecutionError(cmd, -1, stdout, stderr) from e
    except OSError as e:  # e.g., executable not found, permission denied
        raise SubprocessExecutionError(cmd, -1, None, str(e)) from e

    if completed.returncode != 0 and fail_on_error:
        raise SubprocessExecutionError(
            cmd,
            completed.returncode,
            completed.stdout or "",
            completed.stderr or "",
        )

    # At this point CompletedProcess stdout/stderr are str due to text=True + encoding
    return SubprocessExecutionResult(
        completed.returncode, completed.stdout or "", completed.stderr or ""
    )
