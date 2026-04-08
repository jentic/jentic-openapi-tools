"""Tests for the jentic-openapi-tools CLI."""

from __future__ import annotations

import json
import subprocess
import sys
from io import StringIO
from unittest.mock import patch

import pytest
from lsprotocol.types import DiagnosticSeverity, Position, Range

from jentic.apitools.openapi.validator.cli import build_parser, format_github, format_text, main
from jentic.apitools.openapi.validator.core.diagnostics import JenticDiagnostic, ValidationResult


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

VALID_SPEC = {
    "openapi": "3.1.0",
    "info": {"title": "Test API", "version": "1.0.0"},
    "paths": {},
    "servers": [{"url": "https://api.example.com"}],
}

INVALID_SPEC = {
    "openapi": "3.1.0",
    "info": {"title": "Test API", "version": "1.0.0"},
    # missing paths and servers -> triggers errors
}


@pytest.fixture()
def valid_spec_file(tmp_path):
    spec = tmp_path / "valid.json"
    spec.write_text(json.dumps(VALID_SPEC))
    return spec


@pytest.fixture()
def invalid_spec_file(tmp_path):
    spec = tmp_path / "invalid.json"
    spec.write_text(json.dumps(INVALID_SPEC))
    return spec


# ---------------------------------------------------------------------------
# Top-level parser
# ---------------------------------------------------------------------------


class TestTopLevel:
    def test_no_subcommand_prints_help_and_exits_two(self, capsys):
        exit_code = main([])
        assert exit_code == 2
        output = capsys.readouterr().out
        assert "validate" in output

    def test_version_flag(self):
        with pytest.raises(SystemExit, match="0"):
            main(["--version"])


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------


class TestBuildParser:
    def test_document_positional(self):
        args = build_parser().parse_args(["validate", "spec.yaml"])
        assert args.document == "spec.yaml"

    def test_backend_single(self):
        args = build_parser().parse_args(["validate", "-b", "spectral", "spec.yaml"])
        assert args.backend == ["spectral"]

    def test_backend_multiple(self):
        args = build_parser().parse_args(
            ["validate", "-b", "spectral", "-b", "redocly", "spec.yaml"]
        )
        assert args.backend == ["spectral", "redocly"]

    def test_format_choices(self):
        for fmt in ("text", "json", "github"):
            args = build_parser().parse_args(["validate", "--format", fmt, "spec.yaml"])
            assert args.format == fmt

    def test_parallel_flag(self):
        args = build_parser().parse_args(["validate", "--parallel", "spec.yaml"])
        assert args.parallel is True

    def test_all_backends_flag(self):
        args = build_parser().parse_args(["validate", "-a", "spec.yaml"])
        assert args.all_backends is True

    def test_all_backends_long_flag(self):
        args = build_parser().parse_args(["validate", "--all-backends", "spec.yaml"])
        assert args.all_backends is True

    def test_defaults(self):
        args = build_parser().parse_args(["validate", "spec.yaml"])
        assert args.backend is None
        assert args.all_backends is False
        assert args.format == "text"
        assert args.parallel is False
        assert args.quiet is False
        assert args.no_color is False
        assert args.base_url is None
        assert args.target is None
        assert args.max_workers is None
        assert args.max_process_workers is None

    def test_base_url(self):
        args = build_parser().parse_args(
            ["validate", "--base-url", "https://example.com", "spec.yaml"]
        )
        assert args.base_url == "https://example.com"

    def test_target(self):
        args = build_parser().parse_args(["validate", "--target", "my-target", "spec.yaml"])
        assert args.target == "my-target"


# ---------------------------------------------------------------------------
# --list-backends
# ---------------------------------------------------------------------------


class TestListBackends:
    def test_prints_and_exits_zero(self, capsys):
        exit_code = main(["validate", "--list-backends"])
        assert exit_code == 0
        output = capsys.readouterr().out
        assert "default" in output
        assert "openapi-spec" in output

    def test_works_without_document(self, capsys):
        exit_code = main(["validate", "--list-backends"])
        assert exit_code == 0


# ---------------------------------------------------------------------------
# Validation outcomes
# ---------------------------------------------------------------------------


class TestValidation:
    def test_valid_document_exits_zero(self, valid_spec_file, capsys):
        exit_code = main(["validate", "--no-color", str(valid_spec_file)])
        assert exit_code == 0
        output = capsys.readouterr().out
        assert "no problems found" in output

    def test_invalid_document_exits_one(self, invalid_spec_file, capsys):
        exit_code = main(["validate", "--no-color", str(invalid_spec_file)])
        assert exit_code == 1
        output = capsys.readouterr().out
        assert "error" in output.lower()

    def test_file_not_found_exits_two(self, capsys):
        exit_code = main(["validate", "/nonexistent/path/spec.yaml"])
        assert exit_code == 2
        err = capsys.readouterr().err
        assert "file not found" in err

    def test_invalid_backend_exits_two(self, valid_spec_file, capsys):
        exit_code = main(["validate", "-b", "nonexistent-backend", str(valid_spec_file)])
        assert exit_code == 2
        err = capsys.readouterr().err
        assert "nonexistent-backend" in err
        assert "available backends" in err

    def test_comma_separated_backends(self, valid_spec_file, capsys):
        exit_code = main(["validate", "-b", "default,openapi-spec", str(valid_spec_file)])
        assert exit_code == 0

    def test_specific_backend(self, valid_spec_file, capsys):
        exit_code = main(["validate", "-b", "openapi-spec", str(valid_spec_file)])
        assert exit_code == 0

    def test_all_backends(self, valid_spec_file, capsys):
        exit_code = main(["validate", "-a", "--no-color", str(valid_spec_file)])
        assert exit_code == 0

    def test_all_backends_mutually_exclusive_with_backend(self, valid_spec_file, capsys):
        exit_code = main(["validate", "-a", "-b", "default", str(valid_spec_file)])
        assert exit_code == 2
        err = capsys.readouterr().err
        assert "mutually exclusive" in err

    def test_missing_document_exits_two(self, capsys):
        exit_code = main(["validate"])
        assert exit_code == 2
        err = capsys.readouterr().err
        assert "document" in err

    def test_directory_exits_two(self, tmp_path, capsys):
        exit_code = main(["validate", str(tmp_path)])
        assert exit_code == 2
        err = capsys.readouterr().err
        assert "not a file" in err


# ---------------------------------------------------------------------------
# Output formats
# ---------------------------------------------------------------------------


class TestOutputFormats:
    def test_json_format_valid(self, valid_spec_file, capsys):
        main(["validate", "--format", "json", str(valid_spec_file)])
        output = json.loads(capsys.readouterr().out)
        assert output["valid"] is True
        assert isinstance(output["diagnostics"], list)
        assert "summary" in output
        assert "total" in output["summary"]

    def test_json_format_invalid(self, invalid_spec_file, capsys):
        main(["validate", "--format", "json", str(invalid_spec_file)])
        output = json.loads(capsys.readouterr().out)
        assert output["valid"] is False
        assert output["summary"]["errors"] > 0

    def test_github_format(self, invalid_spec_file, capsys):
        main(["validate", "--format", "github", str(invalid_spec_file)])
        output = capsys.readouterr().out
        for line in output.strip().splitlines():
            assert line.startswith("::")

    def test_github_format_valid_no_output(self, valid_spec_file, capsys):
        main(["validate", "--format", "github", str(valid_spec_file)])
        output = capsys.readouterr().out
        assert output == ""

    def test_quiet_suppresses_output(self, invalid_spec_file, capsys):
        exit_code = main(["validate", "--quiet", str(invalid_spec_file)])
        assert exit_code == 1
        captured = capsys.readouterr()
        assert captured.out == ""

    def test_text_format_shows_diagnostics(self, invalid_spec_file, capsys):
        main(["validate", "--no-color", str(invalid_spec_file)])
        output = capsys.readouterr().out
        assert "problem" in output


# ---------------------------------------------------------------------------
# Stdin support
# ---------------------------------------------------------------------------


class TestStdin:
    def test_stdin_valid_document(self, capsys):
        with patch("sys.stdin", StringIO(json.dumps(VALID_SPEC))):
            exit_code = main(["validate", "--no-color", "-"])
        assert exit_code == 0
        output = capsys.readouterr().out
        assert "<stdin>" in output

    def test_stdin_invalid_document(self, capsys):
        with patch("sys.stdin", StringIO(json.dumps(INVALID_SPEC))):
            exit_code = main(["validate", "--no-color", "-"])
        assert exit_code == 1


# ---------------------------------------------------------------------------
# Text format positions
# ---------------------------------------------------------------------------


class TestFormatText:
    def test_positions_are_one_indexed(self):
        diag = JenticDiagnostic(
            range=Range(start=Position(line=0, character=0), end=Position(line=0, character=5)),
            message="test issue",
            severity=DiagnosticSeverity.Error,
            source="test",
        )
        result = ValidationResult(diagnostics=[diag])
        output = format_text(result, "spec.yaml")
        # LSP line 0, char 0 should render as 1:1 in user-facing text
        assert "1:1" in output

    def test_positions_offset(self):
        diag = JenticDiagnostic(
            range=Range(start=Position(line=9, character=4), end=Position(line=9, character=10)),
            message="test issue",
            severity=DiagnosticSeverity.Warning,
            source="test",
        )
        result = ValidationResult(diagnostics=[diag])
        output = format_text(result, "spec.yaml")
        # LSP line 9, char 4 should render as 10:5
        assert "10:5" in output

    def test_missing_range_defaults_to_1_1(self):
        diag = JenticDiagnostic(
            range=None,
            message="test issue",
            severity=DiagnosticSeverity.Error,
            source="test",
        )
        result = ValidationResult(diagnostics=[diag])
        output = format_text(result, "spec.yaml")
        assert "1:1" in output


# ---------------------------------------------------------------------------
# GitHub format escaping
# ---------------------------------------------------------------------------


class TestFormatGithub:
    def test_escapes_special_chars_in_message(self):
        diag = JenticDiagnostic(
            range=Range(start=Position(line=0, character=0), end=Position(line=0, character=1)),
            message="line1\nline2",
            severity=DiagnosticSeverity.Error,
            source="test",
        )
        result = ValidationResult(diagnostics=[diag])
        output = format_github(result, "spec.yaml")
        assert "%0A" in output
        assert "\n" not in output.split("::")[2]

    def test_escapes_special_chars_in_file_label(self):
        diag = JenticDiagnostic(
            range=Range(start=Position(line=0, character=0), end=Position(line=0, character=1)),
            message="test",
            severity=DiagnosticSeverity.Warning,
            source="test",
        )
        result = ValidationResult(diagnostics=[diag])
        output = format_github(result, "path:with,special")
        assert "path%3Awith%2Cspecial" in output


# ---------------------------------------------------------------------------
# HTTP/HTTPS URL support
# ---------------------------------------------------------------------------


class TestHttpUrl:
    def test_http_url_passed_to_validator(self, capsys):
        url = "https://example.com/openapi.json"
        mock_result = ValidationResult(diagnostics=[])
        with patch("jentic.apitools.openapi.validator.cli.OpenAPIValidator") as mock_cls:
            mock_cls.return_value.validate.return_value = mock_result
            exit_code = main(["validate", "--no-color", url])

        assert exit_code == 0
        mock_cls.return_value.validate.assert_called_once()
        call_args = mock_cls.return_value.validate.call_args
        assert call_args[0][0] == url

    def test_http_url_not_treated_as_file(self, capsys):
        url = "http://example.com/spec.yaml"
        mock_result = ValidationResult(diagnostics=[])
        with patch("jentic.apitools.openapi.validator.cli.OpenAPIValidator") as mock_cls:
            mock_cls.return_value.validate.return_value = mock_result
            exit_code = main(["validate", "--no-color", url])

        # Should not fail with "file not found"
        assert exit_code == 0
        err = capsys.readouterr().err
        assert "file not found" not in err


# ---------------------------------------------------------------------------
# Argument validation ordering
# ---------------------------------------------------------------------------


class TestArgumentOrdering:
    def test_mutual_exclusivity_before_document_check(self, capsys):
        """--all-backends + --backend should error even without a document."""
        exit_code = main(["validate", "-a", "-b", "default"])
        assert exit_code == 2
        err = capsys.readouterr().err
        assert "mutually exclusive" in err


# ---------------------------------------------------------------------------
# Entry point integration
# ---------------------------------------------------------------------------


class TestEntryPoint:
    def test_module_invocation(self):
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "jentic.apitools.openapi.validator.cli",
                "validate",
                "--list-backends",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0
        assert "default" in result.stdout
