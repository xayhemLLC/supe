"""Validation report writer for Tascer.

Produces machine-readable (JSON) and human-readable reports.
"""

import json
import os
from datetime import datetime
from typing import Optional

from .contracts import ValidationReport


def write_validation_report(
    report: ValidationReport,
    output_dir: str,
    filename_prefix: Optional[str] = None,
    human_readable: bool = True,
) -> dict:
    """Write a validation report to disk.
    
    Creates both JSON (machine-readable) and optional text (human-readable) reports.
    
    Args:
        report: The ValidationReport to write.
        output_dir: Directory to write reports to.
        filename_prefix: Prefix for filenames. Defaults to run_id.
        human_readable: Whether to also write a human-readable text version.
    
    Returns:
        Dict with paths to written files.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    if filename_prefix is None:
        filename_prefix = f"{report.run_id}_{report.tasc_id}"
    
    # Clean filename
    filename_prefix = "".join(c if c.isalnum() or c in "-_" else "_" for c in filename_prefix)
    
    paths = {}
    
    # Write JSON report
    json_path = os.path.join(output_dir, f"{filename_prefix}_report.json")
    with open(json_path, "w") as f:
        json.dump(report.to_dict(), f, indent=2)
    paths["json"] = json_path
    
    # Write human-readable report
    if human_readable:
        text_path = os.path.join(output_dir, f"{filename_prefix}_report.txt")
        with open(text_path, "w") as f:
            f.write(_format_human_readable(report))
        paths["text"] = text_path
    
    return paths


def _format_human_readable(report: ValidationReport) -> str:
    """Format a report as human-readable text."""
    lines = [
        "=" * 60,
        "TASCER VALIDATION REPORT",
        "=" * 60,
        "",
        f"Run ID:     {report.run_id}",
        f"Tasc ID:    {report.tasc_id}",
        f"Status:     {report.overall_status.upper()}",
        "",
        "-" * 40,
        "CONTEXT",
        "-" * 40,
        f"  OS:       {report.context.os_name} ({report.context.arch})",
        f"  CWD:      {report.context.cwd}",
        f"  Repo:     {report.context.repo_root}",
        f"  Started:  {report.context.timestamp_start}",
    ]
    
    if report.context.git_state:
        gs = report.context.git_state
        lines.extend([
            f"  Branch:   {gs.branch}",
            f"  Commit:   {gs.commit[:12] if gs.commit else 'N/A'}",
            f"  Dirty:    {'Yes' if gs.dirty else 'No'}",
        ])
    
    if report.context.toolchain_versions:
        lines.append("  Toolchain:")
        for tool, version in list(report.context.toolchain_versions.items())[:5]:
            # Truncate version string
            ver_short = version[:40] + "..." if len(version) > 40 else version
            lines.append(f"    {tool}: {ver_short}")
    
    lines.extend([
        "",
        "-" * 40,
        "ACTION",
        "-" * 40,
        f"  Name:     {report.action_spec.name}",
        f"  Op Kind:  {report.action_spec.op_kind}",
        f"  Op Ref:   {report.action_spec.op_ref}",
    ])
    
    lines.extend([
        "",
        "-" * 40,
        "RESULT",
        "-" * 40,
        f"  Status:   {report.action_result.status}",
        f"  Op Result: {report.action_result.op_result}",
    ])
    
    if report.action_result.metrics:
        for key, value in report.action_result.metrics.items():
            lines.append(f"  {key}: {value}")
    
    if report.action_result.error:
        lines.extend([
            "",
            "  ERROR:",
            f"    Type: {report.action_result.error.error_type}",
            f"    Message: {report.action_result.error.message}",
        ])
    
    lines.extend([
        "",
        "-" * 40,
        "GATES",
        "-" * 40,
    ])
    
    if report.gates_passed:
        lines.append(f"  PASSED ({len(report.gates_passed)}):")
        for gate in report.gates_passed:
            lines.append(f"    ✓ {gate.gate_name}: {gate.message}")
    
    if report.gates_failed:
        lines.append(f"  FAILED ({len(report.gates_failed)}):")
        for gate in report.gates_failed:
            lines.append(f"    ✗ {gate.gate_name}: {gate.message}")
    
    if report.evidence_index:
        lines.extend([
            "",
            "-" * 40,
            "EVIDENCE",
            "-" * 40,
        ])
        for name, path in report.evidence_index.items():
            lines.append(f"  {name}: {path}")
    
    lines.extend([
        "",
        "=" * 60,
        f"Generated: {datetime.utcnow().isoformat()}",
        "=" * 60,
    ])
    
    return "\n".join(lines)


def format_summary(report: ValidationReport) -> str:
    """Generate a brief summary of the report.
    
    Suitable for logging or quick display.
    """
    status_emoji = {
        "pass": "✓",
        "fail": "✗",
        "partial": "◐",
        "pending": "○",
    }
    emoji = status_emoji.get(report.overall_status, "?")
    
    return (
        f"{emoji} [{report.overall_status.upper()}] "
        f"{report.tasc_id} - "
        f"{len(report.gates_passed)} passed, {len(report.gates_failed)} failed"
    )
