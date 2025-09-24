import sys
import unittest
import platform

from jentic.apitools.openapi.common.subproc import (
    run_subprocess,
    SubprocessExecutionResult,
    SubprocessExecutionError,
)


class TestSubprocessModule(unittest.TestCase):
    """Test cases for the custom subprocess module."""

    def setUp(self):
        """Set up test fixtures."""
        self.is_windows = platform.system() == "Windows"
        self.is_unix = platform.system() in ("Linux", "Darwin")

    @unittest.skipUnless(
        platform.system() in ("Linux", "Darwin", "Windows"), "Requires a supported operating system"
    )
    def test_successful_command(self):
        """Test running a successful command."""
        if self.is_windows:
            cmd = ["cmd", "/c", "echo", "hello"]
        else:
            cmd = ["echo", "hello"]

        result = run_subprocess(cmd)

        self.assertIsInstance(result, SubprocessExecutionResult)
        self.assertEqual(result.returncode, 0)
        self.assertIn("hello", result.stdout)
        self.assertEqual(result.stderr, "")

    @unittest.skipUnless(platform.system() in ("Linux", "Darwin"), "Requires Unix-like system")
    def test_unix_ls_command(self):
        """Test ls command on Unix systems."""
        result = run_subprocess(["ls", "/"])

        self.assertEqual(result.returncode, 0)
        self.assertIsInstance(result.stdout, str)
        self.assertTrue(len(result.stdout) > 0)

    @unittest.skipUnless(platform.system() == "Windows", "Requires Windows system")
    def test_windows_dir_command(self):
        """Test dir command on Windows systems."""
        result = run_subprocess(["cmd", "/c", "dir", "C:\\"])

        self.assertEqual(result.returncode, 0)
        self.assertIsInstance(result.stdout, str)
        self.assertTrue(len(result.stdout) > 0)

    @unittest.skipUnless(
        platform.system() in ("Linux", "Darwin", "Windows"), "Requires a supported operating system"
    )
    def test_python_version_command(self):
        """Test running python --version command."""
        # Use sys.executable to ensure we're using the right Python
        result = run_subprocess([sys.executable, "--version"])

        self.assertEqual(result.returncode, 0)
        self.assertIn("Python", result.stdout)

    def test_nonexistent_command(self):
        """Test running a command that doesn't exist."""
        with self.assertRaises(SubprocessExecutionError) as cm:
            run_subprocess(["nonexistent_command_12345"])

        self.assertEqual(cm.exception.returncode, -1)
        self.assertEqual(cm.exception.cmd, ["nonexistent_command_12345"])

    @unittest.skipUnless(
        platform.system() in ("Linux", "Darwin", "Windows"), "Requires a supported operating system"
    )
    def test_command_with_non_zero_exit_code(self):
        """Test command that exits with non-zero code."""
        if self.is_windows:
            cmd = ["cmd", "/c", "exit", "1"]
        else:
            cmd = ["sh", "-c", "exit 1"]

        # Without fail_on_error, should not raise exception
        result = run_subprocess(cmd)
        self.assertEqual(result.returncode, 1)

        # With fail_on_error=True, should raise exception
        with self.assertRaises(SubprocessExecutionError) as cm:
            run_subprocess(cmd, fail_on_error=True)

        self.assertEqual(cm.exception.returncode, 1)
        self.assertEqual(cm.exception.cmd, cmd)

    @unittest.skipUnless(
        platform.system() in ("Linux", "Darwin"), "Requires Unix-like system for stderr test"
    )
    def test_command_with_stderr(self):
        """Test command that produces stderr output."""
        # Use a command that writes to stderr
        result = run_subprocess(["sh", "-c", "echo 'error message' >&2"])

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertIn("error message", result.stderr)

    def test_encoding_parameter(self):
        """Test custom encoding parameter."""
        if self.is_windows:
            cmd = ["cmd", "/c", "echo", "hello"]
        else:
            cmd = ["echo", "hello"]

        result = run_subprocess(cmd, encoding="utf-8")

        self.assertEqual(result.returncode, 0)
        self.assertIn("hello", result.stdout)
        self.assertIsInstance(result.stdout, str)

    def test_subprocess_execution_result_initialization(self):
        """Test SubprocessExecutionResult initialization."""
        result = SubprocessExecutionResult(0, "stdout", "stderr")

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "stdout")
        self.assertEqual(result.stderr, "stderr")

        # Test with defaults
        result_defaults = SubprocessExecutionResult(1)
        self.assertEqual(result_defaults.returncode, 1)
        self.assertEqual(result_defaults.stdout, "")
        self.assertEqual(result_defaults.stderr, "")

    def test_subprocess_execution_error_initialization(self):
        """Test SubprocessExecutionError initialization."""
        cmd = ["test", "command"]
        error = SubprocessExecutionError(cmd, 1, "out", "err")

        self.assertEqual(error.cmd, ["test", "command"])
        self.assertEqual(error.returncode, 1)
        self.assertEqual(error.stdout, "out")
        self.assertEqual(error.stderr, "err")

        # Test message formatting
        error_msg = str(error)
        self.assertIn("['test', 'command']", error_msg)
        self.assertIn("exit code 1", error_msg)
        self.assertIn("out", error_msg)
        self.assertIn("err", error_msg)

    @unittest.skipUnless(platform.system() in ("Linux", "Darwin"), "Requires Unix-like system")
    def test_empty_command_output(self):
        """Test command that produces no output."""
        result = run_subprocess(["true"])  # Unix command that does nothing and succeeds

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertEqual(result.stderr, "")

    @unittest.skipUnless(
        platform.system() in ("Linux", "Darwin", "Windows"), "Requires a supported operating system"
    )
    def test_command_with_arguments(self):
        """Test command with multiple arguments."""
        if self.is_windows:
            cmd = ["cmd", "/c", "echo", "hello", "world"]
        else:
            cmd = ["echo", "hello", "world"]

        result = run_subprocess(cmd)

        self.assertEqual(result.returncode, 0)
        self.assertIn("hello", result.stdout)
        self.assertIn("world", result.stdout)

    @unittest.skipUnless(platform.system() in ("Linux", "Darwin"), "Requires Unix-like system")
    def test_cwd_parameter(self):
        """Test running command with custom working directory."""
        # Test running 'pwd' command in root directory
        result = run_subprocess(["pwd"], cwd="/")

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), "/")

    @unittest.skipUnless(platform.system() == "Windows", "Requires Windows system")
    def test_cwd_parameter_windows(self):
        """Test running command with custom working directory on Windows."""
        # Test running 'cd' command in C:\ directory
        result = run_subprocess(["cmd", "/c", "cd"], cwd="C:\\")

        self.assertEqual(result.returncode, 0)
        self.assertIn("C:\\", result.stdout)

    def test_cwd_parameter_with_nonexistent_directory(self):
        """Test running command with non-existent working directory."""
        with self.assertRaises(SubprocessExecutionError) as cm:
            run_subprocess(["echo", "test"], cwd="/nonexistent/directory/path")

        self.assertEqual(cm.exception.returncode, -1)

    def test_cwd_parameter_none(self):
        """Test that cwd=None works (uses current directory)."""
        if self.is_windows:
            cmd = ["cmd", "/c", "echo", "test"]
        else:
            cmd = ["echo", "test"]

        result = run_subprocess(cmd, cwd=None)

        self.assertEqual(result.returncode, 0)
        self.assertIn("test", result.stdout)

    @unittest.skipUnless(
        platform.system() in ("Linux", "Darwin", "Windows"), "Requires a supported operating system"
    )
    def test_timeout_scenario(self):
        """Test command timeout handling."""
        if self.is_windows:
            # Use timeout command on Windows (if available) or ping with delay
            cmd = ["ping", "-n", "3", "127.0.0.1"]  # Takes ~2 seconds
        else:
            cmd = ["sleep", "2"]  # Takes 2 seconds

        # Test that command times out after 0.5 seconds
        with self.assertRaises(SubprocessExecutionError) as cm:
            run_subprocess(cmd, timeout=0.5)

        self.assertEqual(cm.exception.returncode, -1)
        # The exception should contain timeout information
        self.assertIn("sleep", " ".join(cm.exception.cmd) if not self.is_windows else "ping")

    def test_timeout_successful_completion(self):
        """Test that timeout doesn't interfere with commands that complete quickly."""
        if self.is_windows:
            cmd = ["cmd", "/c", "echo", "quick"]
        else:
            cmd = ["echo", "quick"]

        # Command should complete well within 5 second timeout
        result = run_subprocess(cmd, timeout=5)

        self.assertEqual(result.returncode, 0)
        self.assertIn("quick", result.stdout)


if __name__ == "__main__":
    unittest.main()
