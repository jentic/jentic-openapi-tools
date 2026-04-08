"""Command-line interface for jentic-openapi-validator."""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import os
import sys
from pathlib import Path

from lsprotocol import converters as lsp_converters
from lsprotocol.types import DiagnosticSeverity

from jentic.apitools.openapi.common.uri import is_http_https_url
from jentic.apitools.openapi.validator.core import OpenAPIValidator
from jentic.apitools.openapi.validator.core.diagnostics import JenticDiagnostic, ValidationResult


_SEVERITY_LABELS: dict[DiagnosticSeverity, str] = {
    DiagnosticSeverity.Error: "error",
    DiagnosticSeverity.Warning: "warning",
    DiagnosticSeverity.Information: "info",
    DiagnosticSeverity.Hint: "hint",
}

_GITHUB_LEVELS: dict[DiagnosticSeverity, str] = {
    DiagnosticSeverity.Error: "error",
    DiagnosticSeverity.Warning: "warning",
    DiagnosticSeverity.Information: "notice",
    DiagnosticSeverity.Hint: "notice",
}

# ANSI color codes
_COLORS: dict[DiagnosticSeverity, str] = {
    DiagnosticSeverity.Error: "\033[31m",  # red
    DiagnosticSeverity.Warning: "\033[33m",  # yellow
    DiagnosticSeverity.Information: "\033[34m",  # blue
    DiagnosticSeverity.Hint: "\033[2m",  # dim
}
_RESET = "\033[0m"


def _get_version() -> str:
    return importlib.metadata.version("jentic-openapi-validator")


def _use_color(args: argparse.Namespace) -> bool:
    if args.no_color:
        return False
    if os.environ.get("NO_COLOR") is not None:
        return False
    return sys.stdout.isatty()


def _resolve_backends(raw: list[str] | None) -> list[str]:
    """Expand comma-separated backend names into a flat list."""
    if raw is None:
        return ["default"]
    backends: list[str] = []
    for item in raw:
        backends.extend(name.strip() for name in item.split(",") if name.strip())
    return backends or ["default"]


def _count_by_severity(diagnostics: list[JenticDiagnostic]) -> dict[str, int]:
    counts = {"errors": 0, "warnings": 0, "information": 0, "hints": 0}
    for d in diagnostics:
        if d.severity == DiagnosticSeverity.Error:
            counts["errors"] += 1
        elif d.severity == DiagnosticSeverity.Warning:
            counts["warnings"] += 1
        elif d.severity == DiagnosticSeverity.Information:
            counts["information"] += 1
        elif d.severity == DiagnosticSeverity.Hint:
            counts["hints"] += 1
    return counts


def _summary_line(document_label: str, counts: dict[str, int], total: int) -> str:
    if total == 0:
        return f"{document_label}: no problems found"
    parts: list[str] = []
    if counts["errors"]:
        parts.append(f"{counts['errors']} error{'s' if counts['errors'] != 1 else ''}")
    if counts["warnings"]:
        parts.append(f"{counts['warnings']} warning{'s' if counts['warnings'] != 1 else ''}")
    if counts["information"]:
        parts.append(f"{counts['information']} info")
    if counts["hints"]:
        parts.append(f"{counts['hints']} hint{'s' if counts['hints'] != 1 else ''}")
    detail = ", ".join(parts)
    return f"{document_label}: {total} problem{'s' if total != 1 else ''} ({detail})"


def format_text(result: ValidationResult, document_label: str, *, color: bool = False) -> str:
    counts = _count_by_severity(result.diagnostics)
    total = len(result.diagnostics)
    lines: list[str] = [_summary_line(document_label, counts, total)]

    if total > 0:
        lines.append("")

    for d in result.diagnostics:
        severity = d.severity or DiagnosticSeverity.Error
        label = _SEVERITY_LABELS.get(severity, "error")
        line = d.range.start.line + 1 if d.range else 1
        col = d.range.start.character + 1 if d.range else 1
        pos = f"{line}:{col}"
        code = d.code or ""
        source = f"({d.source})" if d.source else ""

        if color:
            severity_color = _COLORS.get(severity, "")
            lines.append(
                f"  {severity_color}{label:7s}{_RESET}  {pos:>6s}  {d.message}  {code}  {source}"
            )
        else:
            lines.append(f"  {label:7s}  {pos:>6s}  {d.message}  {code}  {source}")

    return "\n".join(lines)


def format_json(result: ValidationResult) -> str:
    converter = lsp_converters.get_converter()
    counts = _count_by_severity(result.diagnostics)
    output = {
        "valid": result.valid,
        "diagnostics": [converter.unstructure(d) for d in result.diagnostics],
        "summary": {**counts, "total": len(result.diagnostics)},
    }
    return json.dumps(output, indent=2)


def format_github(result: ValidationResult, document_label: str) -> str:
    lines: list[str] = []
    for d in result.diagnostics:
        severity = d.severity or DiagnosticSeverity.Error
        level = _GITHUB_LEVELS.get(severity, "notice")
        line = d.range.start.line + 1 if d.range else 1
        col = d.range.start.character + 1 if d.range else 1
        code_suffix = f" ({d.code})" if d.code else ""
        lines.append(
            f"::{level} file={document_label},line={line},col={col}::{d.message}{code_suffix}"
        )
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="openapi-validate",
        description="Validate OpenAPI documents using pluggable backends.",
    )
    parser.add_argument(
        "document",
        nargs="?",
        help="Path or URI to an OpenAPI document, or '-' to read from stdin.",
    )
    parser.add_argument(
        "-b",
        "--backend",
        action="append",
        default=None,
        metavar="NAME",
        help="Backend to use (repeatable, or comma-separated). Default: 'default'.",
    )
    parser.add_argument(
        "-a",
        "--all-backends",
        action="store_true",
        help="Use all available validator backends.",
    )
    parser.add_argument(
        "--list-backends",
        action="store_true",
        help="List available validator backends and exit.",
    )
    parser.add_argument(
        "--base-url",
        default=None,
        help="Base URL for resolving relative $ref references.",
    )
    parser.add_argument(
        "--target",
        default=None,
        help="Target identifier for validation context.",
    )
    parser.add_argument(
        "--parallel",
        action="store_true",
        help="Run backends in parallel.",
    )
    parser.add_argument(
        "--max-workers",
        type=int,
        default=None,
        help="Thread pool size for I/O backends (requires --parallel).",
    )
    parser.add_argument(
        "--max-process-workers",
        type=int,
        default=None,
        help="Process pool size for CPU-heavy backends (requires --parallel).",
    )
    parser.add_argument(
        "-f",
        "--format",
        choices=["text", "json", "github"],
        default="text",
        help="Output format (default: text).",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Suppress output; only set exit code.",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable colored output.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {_get_version()}",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI entry point. Returns exit code: 0=valid, 1=invalid, 2=error."""
    parser = build_parser()
    args = parser.parse_args(argv)

    # --list-backends: print available backends and exit
    if args.list_backends:
        for name in sorted(OpenAPIValidator.list_backends()):
            print(name)
        return 0

    # Check mutual exclusivity before document requirement
    if args.all_backends and args.backend:
        parser.error("--all-backends/-a and --backend/-b are mutually exclusive")

    # Require document when not using --list-backends
    if args.document is None:
        parser.error("the following arguments are required: document")

    # Resolve document input
    document_label = args.document
    if args.document == "-":
        document: str | dict = sys.stdin.read()
        document_label = "<stdin>"
    elif is_http_https_url(args.document):
        document = args.document
    else:
        path = Path(args.document)
        if not path.exists():
            print(f"error: file not found: {args.document}", file=sys.stderr)
            return 2
        document = path.resolve().as_uri()

    # Resolve backends
    if args.all_backends:
        backends = OpenAPIValidator.list_backends()
    else:
        backends = _resolve_backends(args.backend)

    # Create validator
    try:
        validator = OpenAPIValidator(backends=backends)
    except ValueError as exc:
        available = ", ".join(sorted(OpenAPIValidator.list_backends()))
        print(f"error: {exc}\navailable backends: {available}", file=sys.stderr)
        return 2

    # Run validation
    try:
        result = validator.validate(
            document,
            base_url=args.base_url,
            target=args.target,
            parallel=args.parallel,
            max_workers=args.max_workers,
            max_process_workers=args.max_process_workers,
        )
    except Exception as exc:
        print(f"error: validation failed: {exc}", file=sys.stderr)
        return 2

    # Output
    if not args.quiet:
        if args.format == "json":
            print(format_json(result))
        elif args.format == "github":
            output = format_github(result, document_label)
            if output:
                print(output)
        else:
            color = _use_color(args)
            print(format_text(result, document_label, color=color))

    return 0 if result.valid else 1


if __name__ == "__main__":
    sys.exit(main())
