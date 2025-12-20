"""TASC_REPRO_BUNDLE_EXPORT - Create reproducibility packages.

Create a "repro pack":
- context.json
- commands run
- evidence artifacts
- diffs
- minimal instructions

This makes failures transferable to another agent/human instantly.
"""

import json
import os
import shutil
import tempfile
import zipfile
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

from ..contracts import ValidationReport


@dataclass
class ReproBundle:
    """A reproducibility bundle for sharing failures."""
    
    bundle_id: str
    created_at: str
    tasc_id: str
    run_id: str
    archive_path: Optional[str] = None
    contents: List[str] = field(default_factory=list)
    instructions: str = ""
    
    def to_dict(self) -> Dict:
        return {
            "bundle_id": self.bundle_id,
            "created_at": self.created_at,
            "tasc_id": self.tasc_id,
            "run_id": self.run_id,
            "archive_path": self.archive_path,
            "contents": self.contents,
            "instructions": self.instructions,
        }


def export_repro_bundle(
    report: ValidationReport,
    output_dir: str,
    include_evidence: bool = True,
    include_git_diff: bool = True,
    additional_files: Optional[List[str]] = None,
) -> ReproBundle:
    """Export a reproducibility bundle from a validation report.
    
    TASC_REPRO_BUNDLE_EXPORT implementation.
    
    Args:
        report: ValidationReport to bundle.
        output_dir: Directory to write bundle to.
        include_evidence: Include evidence artifacts.
        include_git_diff: Include git diff if available.
        additional_files: Extra files to include.
    
    Returns:
        ReproBundle with archive path.
    """
    bundle_id = f"{report.run_id}_{report.tasc_id}"
    timestamp = datetime.utcnow().isoformat()
    
    # Create temp directory for bundle contents
    with tempfile.TemporaryDirectory() as temp_dir:
        contents = []
        
        # Write context.json
        context_path = os.path.join(temp_dir, "context.json")
        with open(context_path, "w") as f:
            json.dump(report.context.to_dict(), f, indent=2)
        contents.append("context.json")
        
        # Write action_spec.json
        action_path = os.path.join(temp_dir, "action_spec.json")
        with open(action_path, "w") as f:
            json.dump(report.action_spec.to_dict(), f, indent=2)
        contents.append("action_spec.json")
        
        # Write action_result.json
        result_path = os.path.join(temp_dir, "action_result.json")
        with open(result_path, "w") as f:
            json.dump(report.action_result.to_dict(), f, indent=2)
        contents.append("action_result.json")
        
        # Write full report
        report_path = os.path.join(temp_dir, "validation_report.json")
        with open(report_path, "w") as f:
            json.dump(report.to_dict(), f, indent=2)
        contents.append("validation_report.json")
        
        # Write gate results summary
        gates_path = os.path.join(temp_dir, "gates.json")
        with open(gates_path, "w") as f:
            json.dump({
                "passed": [g.to_dict() for g in report.gates_passed],
                "failed": [g.to_dict() for g in report.gates_failed],
            }, f, indent=2)
        contents.append("gates.json")
        
        # Copy evidence artifacts
        if include_evidence and report.evidence_index:
            evidence_dir = os.path.join(temp_dir, "evidence")
            os.makedirs(evidence_dir, exist_ok=True)
            
            for name, path in report.evidence_index.items():
                if os.path.exists(path):
                    dest = os.path.join(evidence_dir, os.path.basename(path))
                    shutil.copy2(path, dest)
                    contents.append(f"evidence/{os.path.basename(path)}")
        
        # Include git diff
        if include_git_diff and report.context.git_state:
            git_state = report.context.git_state
            if git_state.diff_stat:
                diff_path = os.path.join(temp_dir, "git_diff_stat.txt")
                with open(diff_path, "w") as f:
                    f.write(git_state.diff_stat)
                contents.append("git_diff_stat.txt")
            
            if git_state.status:
                status_path = os.path.join(temp_dir, "git_status.txt")
                with open(status_path, "w") as f:
                    f.write(git_state.status)
                contents.append("git_status.txt")
        
        # Copy additional files
        if additional_files:
            extras_dir = os.path.join(temp_dir, "extras")
            os.makedirs(extras_dir, exist_ok=True)
            
            for file_path in additional_files:
                if os.path.exists(file_path):
                    dest = os.path.join(extras_dir, os.path.basename(file_path))
                    shutil.copy2(file_path, dest)
                    contents.append(f"extras/{os.path.basename(file_path)}")
        
        # Generate instructions
        instructions = _generate_instructions(report)
        instructions_path = os.path.join(temp_dir, "README.md")
        with open(instructions_path, "w") as f:
            f.write(instructions)
        contents.append("README.md")
        
        # Create zip archive
        os.makedirs(output_dir, exist_ok=True)
        archive_name = f"repro_{bundle_id}.zip"
        archive_path = os.path.join(output_dir, archive_name)
        
        with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arc_name = os.path.relpath(file_path, temp_dir)
                    zf.write(file_path, arc_name)
    
    return ReproBundle(
        bundle_id=bundle_id,
        created_at=timestamp,
        tasc_id=report.tasc_id,
        run_id=report.run_id,
        archive_path=archive_path,
        contents=contents,
        instructions=instructions,
    )


def _generate_instructions(report: ValidationReport) -> str:
    """Generate reproduction instructions from report."""
    lines = [
        "# Reproduction Bundle",
        "",
        f"**Tasc ID:** {report.tasc_id}",
        f"**Run ID:** {report.run_id}",
        f"**Status:** {report.overall_status}",
        f"**Generated:** {datetime.utcnow().isoformat()}",
        "",
        "## Environment",
        "",
        f"- OS: {report.context.os_name} ({report.context.arch})",
        f"- CWD: {report.context.cwd}",
        f"- Repo: {report.context.repo_root}",
    ]
    
    if report.context.git_state:
        gs = report.context.git_state
        lines.extend([
            f"- Branch: {gs.branch}",
            f"- Commit: {gs.commit}",
            f"- Dirty: {'Yes' if gs.dirty else 'No'}",
        ])
    
    if report.context.toolchain_versions:
        lines.append("")
        lines.append("### Toolchain Versions")
        lines.append("")
        for tool, version in list(report.context.toolchain_versions.items())[:10]:
            lines.append(f"- {tool}: {version[:50]}")
    
    lines.extend([
        "",
        "## Command",
        "",
        f"```bash",
        f"cd {report.context.repo_root}",
        f"{report.action_spec.op_ref}",
        f"```",
        "",
        "## Result",
        "",
        f"- Status: {report.action_result.status}",
        f"- Exit Code: {report.action_result.op_result}",
    ])
    
    if report.gates_failed:
        lines.extend([
            "",
            "## Failed Gates",
            "",
        ])
        for gate in report.gates_failed:
            lines.append(f"- **{gate.gate_name}**: {gate.message}")
    
    lines.extend([
        "",
        "## Files Included",
        "",
        "- `context.json` - Execution context snapshot",
        "- `action_spec.json` - Action specification",
        "- `action_result.json` - Execution result",
        "- `validation_report.json` - Full validation report",
        "- `gates.json` - Gate results",
        "- `evidence/` - Output artifacts",
    ])
    
    return "\n".join(lines)
