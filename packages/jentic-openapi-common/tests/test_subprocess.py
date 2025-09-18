import sys
import unittest
import platform

from jentic_openapi_common.subprocess import (
    run_checked,
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

        result = run_checked(cmd)

        self.assertIsInstance(result, SubprocessExecutionResult)
        self.assertEqual(result.returncode, 0)
        self.assertIn("hello", result.stdout)
        self.assertEqual(result.stderr, "")

    @unittest.skipUnless(platform.system() in ("Linux", "Darwin"), "Requires Unix-like system")
    def test_unix_ls_command(self):
        """Test ls command on Unix systems."""
        result = run_checked(["ls", "/"])

        self.assertEqual(result.returncode, 0)
        self.assertIsInstance(result.stdout, str)
        self.assertTrue(len(result.stdout) > 0)

    @unittest.skipUnless(platform.system() == "Windows", "Requires Windows system")
    def test_windows_dir_command(self):
        """Test dir command on Windows systems."""
        result = run_checked(["cmd", "/c", "dir", "C:\\"])

        self.assertEqual(result.returncode, 0)
        self.assertIsInstance(result.stdout, str)
        self.assertTrue(len(result.stdout) > 0)

    @unittest.skipUnless(
        platform.system() in ("Linux", "Darwin", "Windows"), "Requires a supported operating system"
    )
    def test_python_version_command(self):
        """Test running python --version command."""
        # Use sys.executable to ensure we're using the right Python
        result = run_checked([sys.executable, "--version"])

        self.assertEqual(result.returncode, 0)
        self.assertIn("Python", result.stdout)

    def test_nonexistent_command(self):
        """Test running a command that doesn't exist."""
        with self.assertRaises(SubprocessExecutionError) as cm:
            run_checked(["nonexistent_command_12345"])

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
        result = run_checked(cmd)
        self.assertEqual(result.returncode, 1)

        # With fail_on_error=True, should raise exception
        with self.assertRaises(SubprocessExecutionError) as cm:
            run_checked(cmd, fail_on_error=True)

        self.assertEqual(cm.exception.returncode, 1)
        self.assertEqual(cm.exception.cmd, cmd)

    @unittest.skipUnless(
        platform.system() in ("Linux", "Darwin"), "Requires Unix-like system for stderr test"
    )
    def test_command_with_stderr(self):
        """Test command that produces stderr output."""
        # Use a command that writes to stderr
        result = run_checked(["sh", "-c", "echo 'error message' >&2"])

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertIn("error message", result.stderr)

    def test_encoding_parameter(self):
        """Test custom encoding parameter."""
        if self.is_windows:
            cmd = ["cmd", "/c", "echo", "hello"]
        else:
            cmd = ["echo", "hello"]

        result = run_checked(cmd, encoding="utf-8")

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
        result = run_checked(["true"])  # Unix command that does nothing and succeeds

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

        result = run_checked(cmd)

        self.assertEqual(result.returncode, 0)
        self.assertIn("hello", result.stdout)
        self.assertIn("world", result.stdout)


if __name__ == "__main__":
    unittest.main()
