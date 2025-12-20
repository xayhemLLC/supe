"""Markdown Audit Export.

Exports tasc runs to readable Markdown documentation.

Output format:
- Tasc-<id>.md
  - Hypothesis
  - Narrative snapshots
  - Action trace
  - Evidence links
  - Diffs
  - Screenshots
  - Final outcome
"""

import os
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..contracts import ValidationReport
from ..ledgers import MomentsLedger, ExeLedger, LedgerStorage


@dataclass
class AuditExporter:
    """Exports tasc runs to Markdown."""
    
    output_dir: str = "./audit_output"
    
    def export_report(
        self,
        report: ValidationReport,
        include_evidence: bool = True,
    ) -> str:
        """Export a ValidationReport to Markdown.
        
        Args:
            report: The validation report to export.
            include_evidence: Include evidence file references.
        
        Returns:
            Path to generated Markdown file.
        """
        os.makedirs(self.output_dir, exist_ok=True)
        
        md_content = format_tasc_report(report, include_evidence)
        
        filename = f"Tasc-{report.tasc_id}.md"
        filepath = os.path.join(self.output_dir, filename)
        
        with open(filepath, "w") as f:
            f.write(md_content)
        
        return filepath
    
    def export_ledgers(
        self,
        storage: LedgerStorage,
        hypothesis: Optional[str] = None,
    ) -> str:
        """Export ledgers to comprehensive Markdown.
        
        Args:
            storage: LedgerStorage with moments and exe.
            hypothesis: Optional hypothesis being tested.
        
        Returns:
            Path to generated Markdown file.
        """
        os.makedirs(self.output_dir, exist_ok=True)
        
        md_content = format_ledgers(storage, hypothesis)
        
        filename = f"Tasc-{storage.run_id}.md"
        filepath = os.path.join(self.output_dir, filename)
        
        with open(filepath, "w") as f:
            f.write(md_content)
        
        return filepath


def format_tasc_report(
    report: ValidationReport,
    include_evidence: bool = True,
) -> str:
    """Format a ValidationReport as Markdown.
    
    Args:
        report: Report to format.
        include_evidence: Include evidence references.
    
    Returns:
        Formatted Markdown string.
    """
    lines = [
        f"# Tasc-{report.tasc_id}",
        "",
        f"**Run ID:** `{report.run_id}`",
        f"**Status:** {report.overall_status}",
        f"**Generated:** {datetime.now().isoformat()}",
        "",
        "---",
        "",
        "## Context",
        "",
        f"- **Repository:** `{report.context.repo_root}`",
        f"- **Working Directory:** `{report.context.cwd}`",
        f"- **Git Branch:** {report.context.git.branch if report.context.git else 'N/A'}",
        f"- **Git Commit:** `{report.context.git.commit if report.context.git else 'N/A'}`",
        "",
        "---",
        "",
        "## Action",
        "",
        f"**Name:** {report.action_spec.name}",
        "",
        "```",
        report.action_spec.op_ref,
        "```",
        "",
        "### Result",
        "",
        f"- **Status:** {report.action_result.status}",
        f"- **Exit Code:** {report.action_result.op_result}",
        "",
    ]
    
    # Gates
    lines.extend([
        "---",
        "",
        "## Validation Gates",
        "",
    ])
    
    if report.gates_passed:
        lines.append("### ✅ Passed")
        lines.append("")
        for gate in report.gates_passed:
            lines.append(f"- **{gate.gate_name}**: {gate.message}")
        lines.append("")
    
    if report.gates_failed:
        lines.append("### ❌ Failed")
        lines.append("")
        for gate in report.gates_failed:
            lines.append(f"- **{gate.gate_name}**: {gate.message}")
        lines.append("")
    
    # Evidence
    if include_evidence and report.evidence_index:
        lines.extend([
            "---",
            "",
            "## Evidence",
            "",
        ])
        for key, path in report.evidence_index.items():
            lines.append(f"- **{key}**: `{path}`")
        lines.append("")
    
    # Summary
    lines.extend([
        "---",
        "",
        "## Summary",
        "",
        report.summary or "*No summary generated.*",
        "",
    ])
    
    return "\n".join(lines)


def format_ledgers(
    storage: LedgerStorage,
    hypothesis: Optional[str] = None,
) -> str:
    """Format ledgers as Markdown.
    
    Args:
        storage: LedgerStorage with moments and exe.
        hypothesis: Optional hypothesis being tested.
    
    Returns:
        Formatted Markdown string.
    """
    lines = [
        f"# Tasc-{storage.run_id}",
        "",
        f"**Generated:** {datetime.now().isoformat()}",
        "",
    ]
    
    if hypothesis:
        lines.extend([
            "## Hypothesis",
            "",
            f"> {hypothesis}",
            "",
        ])
    
    # Exe Ledger - Intent
    lines.extend([
        "---",
        "",
        "## Intent (Exe Ledger)",
        "",
    ])
    
    for decision in storage.exe.get_all():
        icon = {
            "CONTINUE": "▶️",
            "STOP": "⏹️",
            "BACKTRACK": "↩️",
        }.get(decision.decision_type.value.upper(), "•")
        
        lines.append(f"### {icon} {decision.decision_type.value.title()}")
        lines.append("")
        if decision.action_id:
            lines.append(f"**Action:** `{decision.action_id}`")
        if decision.narrative:
            lines.append(f"> {decision.narrative}")
        if decision.confidence:
            lines.append(f"**Confidence:** {decision.confidence.value:.0%}")
        lines.append("")
    
    # Moments Ledger - Reality
    lines.extend([
        "---",
        "",
        "## Reality (Moments Ledger)",
        "",
    ])
    
    for moment in storage.moments.get_all():
        icon = {
            "context_snapshot": "📷",
            "action_start": "▶️",
            "action_result": "✅",
            "error": "❌",
            "evidence": "📎",
        }.get(moment.moment_type.value, "•")
        
        lines.append(f"### {icon} {moment.moment_type.value.replace('_', ' ').title()}")
        lines.append("")
        lines.append(f"**Timestamp:** {moment.timestamp.isoformat()}")
        if moment.action_id:
            lines.append(f"**Action:** `{moment.action_id}`")
        if moment.data:
            lines.append("")
            lines.append("```json")
            import json
            lines.append(json.dumps(moment.data, indent=2, default=str)[:500])
            lines.append("```")
        lines.append("")
    
    # Cross-references
    if storage._cross_refs:
        lines.extend([
            "---",
            "",
            "## Cross-References",
            "",
            "| Decision | Moment | Action | Relationship |",
            "|----------|--------|--------|--------------|",
        ])
        for ref in storage._cross_refs:
            lines.append(
                f"| `{ref.decision_id}` | `{ref.moment_id}` | "
                f"`{ref.action_id or '-'}` | {ref.relationship} |"
            )
        lines.append("")
    
    # Divergence analysis
    divergences = storage.analyze_divergence()
    if divergences:
        lines.extend([
            "---",
            "",
            "## Divergence Analysis",
            "",
        ])
        for div in divergences:
            lines.append(f"- **{div['type']}**")
        lines.append("")
    
    return "\n".join(lines)


def export_to_markdown(
    report: Optional[ValidationReport] = None,
    storage: Optional[LedgerStorage] = None,
    output_dir: str = "./audit_output",
    hypothesis: Optional[str] = None,
) -> str:
    """Convenience function to export to Markdown.
    
    Args:
        report: ValidationReport to export (optional).
        storage: LedgerStorage to export (optional).
        output_dir: Output directory.
        hypothesis: Optional hypothesis.
    
    Returns:
        Path to generated file.
    """
    exporter = AuditExporter(output_dir=output_dir)
    
    if report:
        return exporter.export_report(report)
    elif storage:
        return exporter.export_ledgers(storage, hypothesis)
    else:
        raise ValueError("Either report or storage must be provided")
