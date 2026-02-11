"""Supe Action Executors - Execute actions with validation and proof generation.

This module provides the execution logic for supe actions, integrating:
- Pre/post gate validation
- Proof-of-work generation
- Checkpoint management
- Audit trail recording
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ..contracts import ValidationRecord
from ..gates.builtin import BUILTIN_GATES
from .definitions import get_action


@dataclass
class ExecutionResult:
    """Result of executing a supe action."""

    action_name: str
    success: bool
    output: dict[str, Any]
    proof_hash: str | None = None
    pre_gate_results: list[dict[str, Any]] = field(default_factory=list)
    post_gate_results: list[dict[str, Any]] = field(default_factory=list)
    started_at: str = ""
    completed_at: str = ""
    duration_ms: float = 0
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "action_name": self.action_name,
            "success": self.success,
            "output": self.output,
            "proof_hash": self.proof_hash,
            "pre_gate_results": self.pre_gate_results,
            "post_gate_results": self.post_gate_results,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "duration_ms": self.duration_ms,
            "error": self.error,
        }


class SupeExecutor:
    """Executor for supe actions with validation and proof generation."""

    def __init__(
        self,
        working_dir: str | None = None,
        checkpoint_dir: str | None = None,
        custom_gates: dict[str, Any] | None = None,
    ):
        self.working_dir = working_dir or os.getcwd()
        self.checkpoint_dir = checkpoint_dir or os.path.join(
            self.working_dir, ".supe", "checkpoints"
        )
        self.custom_gates = custom_gates or {}
        self.current_checkpoint: str | None = None
        self.execution_history: list[ExecutionResult] = []

    def _get_gate(self, name: str) -> Any | None:
        """Get a gate by name, checking custom gates first."""
        return self.custom_gates.get(name) or BUILTIN_GATES.get(name)

    def _run_gates(
        self,
        gate_names: list[str],
        record: ValidationRecord,
        phase: str,
    ) -> tuple[bool, list[dict[str, Any]]]:
        """Run a list of gates and return (all_passed, results)."""
        results = []
        all_passed = True

        for gate_name in gate_names:
            gate_func = self._get_gate(gate_name)
            if not gate_func:
                results.append({
                    "gate_name": gate_name,
                    "passed": True,
                    "message": f"Gate not found: {gate_name} (skipped)",
                })
                continue

            try:
                result = gate_func(record, phase)
                results.append({
                    "gate_name": result.gate_name,
                    "passed": result.passed,
                    "message": result.message,
                })
                if not result.passed:
                    all_passed = False
            except Exception as e:
                results.append({
                    "gate_name": gate_name,
                    "passed": False,
                    "message": f"Gate error: {e}",
                })
                all_passed = False

        return all_passed, results

    def _generate_proof(
        self,
        action_name: str,
        inputs: dict[str, Any],
        outputs: dict[str, Any],
        include_output: bool = False,
    ) -> str:
        """Generate proof-of-work hash for an action execution."""
        proof_data = {
            "action": action_name,
            "inputs": inputs,
            "timestamp": datetime.now(timezone.utc).replace(tzinfo=None).isoformat(),
        }
        if include_output:
            proof_data["outputs"] = outputs

        proof_string = json.dumps(proof_data, sort_keys=True, default=str)
        return hashlib.sha256(proof_string.encode()).hexdigest()[:16]

    def execute(
        self,
        action_name: str,
        params: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> ExecutionResult:
        """Execute a supe action with full validation and proof generation."""
        started_at = datetime.now(timezone.utc).replace(tzinfo=None).isoformat()
        start_time = time.time()

        # Get action definition
        action_def = get_action(action_name)
        if not action_def:
            return ExecutionResult(
                action_name=action_name,
                success=False,
                output={},
                error=f"Unknown action: {action_name}",
                started_at=started_at,
                completed_at=datetime.now(timezone.utc).replace(tzinfo=None).isoformat(),
            )

        context = context or {}
        context["has_checkpoint"] = self.current_checkpoint is not None

        # Create validation record for gates
        record = ValidationRecord(
            tool_name=action_name,
            tool_input=params,
            tool_output={},
            context=context,
        )

        # Run pre-gates
        pre_passed, pre_results = self._run_gates(
            action_def.default_pre_gates, record, "pre"
        )

        if not pre_passed:
            return ExecutionResult(
                action_name=action_name,
                success=False,
                output={},
                pre_gate_results=pre_results,
                error="Pre-gate validation failed",
                started_at=started_at,
                completed_at=datetime.now(timezone.utc).replace(tzinfo=None).isoformat(),
                duration_ms=(time.time() - start_time) * 1000,
            )

        # Execute the action
        try:
            output = self._execute_action(action_name, params, context)
            success = output.get("success", True)
            error = output.get("error")
        except Exception as e:
            output = {"error": str(e)}
            success = False
            error = str(e)

        # Update record with output for post-gates
        record.tool_output = output

        # Run post-gates
        post_passed, post_results = self._run_gates(
            action_def.default_post_gates, record, "post"
        )

        # Generate proof if configured
        proof_hash = None
        if action_def.generates_proof:
            proof_hash = self._generate_proof(
                action_name,
                params,
                output,
                include_output=action_def.proof_includes_output,
            )

        completed_at = datetime.now(timezone.utc).replace(tzinfo=None).isoformat()
        duration_ms = (time.time() - start_time) * 1000

        result = ExecutionResult(
            action_name=action_name,
            success=success and post_passed,
            output=output,
            proof_hash=proof_hash,
            pre_gate_results=pre_results,
            post_gate_results=post_results,
            started_at=started_at,
            completed_at=completed_at,
            duration_ms=duration_ms,
            error=error if not success else None,
        )

        self.execution_history.append(result)
        return result

    def _execute_action(
        self,
        action_name: str,
        params: dict[str, Any],
        context: dict[str, Any],
    ) -> dict[str, Any]:
        """Execute the actual action logic."""
        executor_map = {
            "SupeRun": self._execute_run,
            "SupeRead": self._execute_read,
            "SupeWrite": self._execute_write,
            "SupeEdit": self._execute_edit,
            "SupeGlob": self._execute_glob,
            "SupeGrep": self._execute_grep,
            "SupeCheckpoint": self._execute_checkpoint,
            "SupeRollback": self._execute_rollback,
            "SupeProve": self._execute_prove,
            "SupeVerify": self._execute_verify,
        }

        executor = executor_map.get(action_name)
        if not executor:
            return {"error": f"No executor implemented for {action_name}", "success": False}

        return executor(params, context)

    # ─────────────────────────────────────────────────────────────────────────
    # Action Executors
    # ─────────────────────────────────────────────────────────────────────────

    def _execute_run(self, params: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
        """Execute SupeRun - run a shell command."""
        command = params.get("command", "")
        timeout_ms = params.get("timeout", 120000)
        timeout_sec = timeout_ms / 1000
        working_dir = params.get("working_dir", self.working_dir)
        env = params.get("env", {})

        # Merge environment
        full_env = os.environ.copy()
        full_env.update(env)

        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=working_dir,
                env=full_env,
                capture_output=True,
                text=True,
                timeout=timeout_sec,
            )

            return {
                "success": result.returncode == 0,
                "exit_code": result.returncode,
                "stdout": result.stdout[:10000] if result.stdout else "",
                "stderr": result.stderr[:10000] if result.stderr else "",
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "exit_code": -1,
                "error": f"Command timed out after {timeout_sec}s",
            }
        except Exception as e:
            return {
                "success": False,
                "exit_code": -1,
                "error": str(e),
            }

    def _execute_read(self, params: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
        """Execute SupeRead - read a file."""
        file_path = params.get("file_path", "")
        offset = params.get("offset", 1)
        limit = params.get("limit", 2000)
        include_hash = params.get("include_hash", True)

        if not os.path.exists(file_path):
            return {"success": False, "error": f"File not found: {file_path}"}

        try:
            with open(file_path, encoding="utf-8") as f:
                lines = f.readlines()

            # Apply offset and limit (1-indexed)
            start_idx = max(0, offset - 1)
            end_idx = start_idx + limit
            selected_lines = lines[start_idx:end_idx]

            # Format with line numbers
            content = ""
            for i, line in enumerate(selected_lines, start=offset):
                content += f"{i:>6}\t{line}"

            result: dict[str, Any] = {
                "success": True,
                "content": content,
                "total_lines": len(lines),
                "lines_returned": len(selected_lines),
            }

            if include_hash:
                with open(file_path, "rb") as f:
                    result["content_hash"] = hashlib.sha256(f.read()).hexdigest()[:16]

            return result
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _execute_write(self, params: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
        """Execute SupeWrite - write to a file."""
        file_path = params.get("file_path", "")
        content = params.get("content", "")
        create_backup = params.get("create_backup", True)
        atomic = params.get("atomic", True)

        try:
            # Create backup if file exists
            backup_path = None
            if create_backup and os.path.exists(file_path):
                backup_path = f"{file_path}.bak.{int(time.time())}"
                shutil.copy2(file_path, backup_path)

            # Ensure directory exists
            os.makedirs(os.path.dirname(file_path) or ".", exist_ok=True)

            if atomic:
                # Write to temp file then rename
                fd, temp_path = tempfile.mkstemp(dir=os.path.dirname(file_path) or ".")
                try:
                    with os.fdopen(fd, "w", encoding="utf-8") as f:
                        f.write(content)
                    shutil.move(temp_path, file_path)
                except Exception:
                    os.unlink(temp_path)
                    raise
            else:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)

            # Compute hash of written content
            content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]

            return {
                "success": True,
                "file_path": file_path,
                "content_hash": content_hash,
                "backup_path": backup_path,
                "bytes_written": len(content.encode()),
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _execute_edit(self, params: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
        """Execute SupeEdit - replace string in file."""
        file_path = params.get("file_path", "")
        old_string = params.get("old_string", "")
        new_string = params.get("new_string", "")
        replace_all = params.get("replace_all", False)

        if not os.path.exists(file_path):
            return {"success": False, "error": f"File not found: {file_path}"}

        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            # Check occurrences
            count = content.count(old_string)
            if count == 0:
                return {"success": False, "error": "old_string not found in file"}

            if count > 1 and not replace_all:
                return {
                    "success": False,
                    "error": f"old_string appears {count} times. Use replace_all=True or add context.",
                }

            # Create backup
            backup_path = f"{file_path}.bak.{int(time.time())}"
            shutil.copy2(file_path, backup_path)

            # Perform replacement
            if replace_all:
                new_content = content.replace(old_string, new_string)
                replacements = count
            else:
                new_content = content.replace(old_string, new_string, 1)
                replacements = 1

            # Write back
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(new_content)

            return {
                "success": True,
                "file_path": file_path,
                "replacements": replacements,
                "backup_path": backup_path,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _execute_glob(self, params: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
        """Execute SupeGlob - find files by pattern."""
        pattern = params.get("pattern", "")
        path = params.get("path", self.working_dir)
        limit = params.get("limit", 100)

        try:
            from pathlib import Path as P

            base = P(path)
            matches = list(base.glob(pattern))

            # Sort by modification time (newest first)
            matches.sort(key=lambda p: p.stat().st_mtime, reverse=True)

            # Apply limit
            matches = matches[:limit]

            return {
                "success": True,
                "matches": [str(m) for m in matches],
                "count": len(matches),
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _execute_grep(self, params: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
        """Execute SupeGrep - search file contents."""
        import re

        pattern = params.get("pattern", "")
        path = params.get("path", self.working_dir)
        glob_filter = params.get("glob", "**/*")
        output_mode = params.get("output_mode", "files_with_matches")
        case_insensitive = params.get("case_insensitive", False)
        limit = params.get("limit", 100)
        context_lines = params.get("context_lines", 0)

        flags = re.IGNORECASE if case_insensitive else 0

        try:
            regex = re.compile(pattern, flags)
        except re.error as e:
            return {"success": False, "error": f"Invalid regex: {e}"}

        results: list[Any] = []
        files_searched = 0

        try:
            base = Path(path)
            for file_path in base.glob(glob_filter):
                if not file_path.is_file():
                    continue
                if len(results) >= limit:
                    break

                files_searched += 1
                try:
                    with open(file_path, encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                        lines = content.splitlines()

                    if output_mode == "files_with_matches":
                        if regex.search(content):
                            results.append(str(file_path))
                    elif output_mode == "count":
                        matches = len(regex.findall(content))
                        if matches > 0:
                            results.append({"file": str(file_path), "count": matches})
                    elif output_mode == "content":
                        for i, line in enumerate(lines):
                            if regex.search(line):
                                match_result: dict[str, Any] = {
                                    "file": str(file_path),
                                    "line_number": i + 1,
                                    "line": line,
                                }
                                if context_lines > 0:
                                    start = max(0, i - context_lines)
                                    end = min(len(lines), i + context_lines + 1)
                                    match_result["context"] = lines[start:end]
                                results.append(match_result)
                                if len(results) >= limit:
                                    break
                except Exception:
                    continue

            return {
                "success": True,
                "results": results,
                "count": len(results),
                "files_searched": files_searched,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _execute_checkpoint(
        self, params: dict[str, Any], context: dict[str, Any]
    ) -> dict[str, Any]:
        """Execute SupeCheckpoint - create a checkpoint."""
        name = params.get("name", f"checkpoint_{int(time.time())}")
        include_git = params.get("include_git", True)
        paths = params.get("paths", [self.working_dir])

        checkpoint_id = f"{name}_{int(time.time() * 1000)}"
        checkpoint_path = os.path.join(self.checkpoint_dir, checkpoint_id)

        try:
            os.makedirs(checkpoint_path, exist_ok=True)

            # Save file states
            file_states = {}
            for base_path in paths:
                for root, dirs, files in os.walk(base_path):
                    # Skip hidden directories
                    dirs[:] = [d for d in dirs if not d.startswith(".")]
                    for fname in files:
                        if fname.startswith("."):
                            continue
                        fpath = os.path.join(root, fname)
                        rel_path = os.path.relpath(fpath, base_path)
                        try:
                            with open(fpath, "rb") as f:
                                content = f.read()
                            file_states[rel_path] = {
                                "hash": hashlib.sha256(content).hexdigest()[:16],
                                "size": len(content),
                            }
                            # Save content for rollback
                            backup_file = os.path.join(checkpoint_path, rel_path)
                            os.makedirs(os.path.dirname(backup_file), exist_ok=True)
                            with open(backup_file, "wb") as f:
                                f.write(content)
                        except Exception:
                            continue

            # Save git state if requested
            git_state = None
            if include_git:
                try:
                    result = subprocess.run(
                        ["git", "rev-parse", "HEAD"],
                        capture_output=True,
                        text=True,
                        cwd=self.working_dir,
                    )
                    if result.returncode == 0:
                        git_state = {"commit": result.stdout.strip()}
                except Exception:
                    pass

            # Save checkpoint metadata
            metadata = {
                "id": checkpoint_id,
                "name": name,
                "created_at": datetime.now(timezone.utc).replace(tzinfo=None).isoformat(),
                "file_count": len(file_states),
                "git_state": git_state,
            }
            with open(os.path.join(checkpoint_path, "metadata.json"), "w") as f:
                json.dump(metadata, f, indent=2)

            self.current_checkpoint = checkpoint_id

            return {
                "success": True,
                "checkpoint_id": checkpoint_id,
                "file_count": len(file_states),
                "path": checkpoint_path,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _execute_rollback(
        self, params: dict[str, Any], context: dict[str, Any]
    ) -> dict[str, Any]:
        """Execute SupeRollback - restore to checkpoint."""
        checkpoint_id = params.get("checkpoint_id", self.current_checkpoint)
        confirm = params.get("confirm", False)

        if not confirm:
            return {"success": False, "error": "Rollback requires confirm=True"}

        if not checkpoint_id:
            return {"success": False, "error": "No checkpoint specified or available"}

        checkpoint_path = os.path.join(self.checkpoint_dir, checkpoint_id)
        if not os.path.exists(checkpoint_path):
            return {"success": False, "error": f"Checkpoint not found: {checkpoint_id}"}

        try:
            # Verify checkpoint has metadata (validates it's a real checkpoint)
            with open(os.path.join(checkpoint_path, "metadata.json")) as f:
                json.load(f)  # Validates JSON structure

            # Restore files
            restored_count = 0
            for root, dirs, files in os.walk(checkpoint_path):
                for fname in files:
                    if fname == "metadata.json":
                        continue
                    src = os.path.join(root, fname)
                    rel_path = os.path.relpath(src, checkpoint_path)
                    dst = os.path.join(self.working_dir, rel_path)

                    os.makedirs(os.path.dirname(dst), exist_ok=True)
                    shutil.copy2(src, dst)
                    restored_count += 1

            return {
                "success": True,
                "checkpoint_id": checkpoint_id,
                "files_restored": restored_count,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _execute_prove(self, params: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
        """Execute SupeProve - generate proof for command or assertion."""
        command = params.get("command")
        assertion = params.get("assertion")
        include_timestamp = params.get("include_timestamp", True)

        proof_data: dict[str, Any] = {}

        if command:
            # Run command and capture output
            result = self._execute_run({"command": command}, context)
            proof_data["command"] = command
            proof_data["exit_code"] = result.get("exit_code")
            proof_data["stdout_hash"] = hashlib.sha256(
                result.get("stdout", "").encode()
            ).hexdigest()[:16]

        if assertion:
            # Evaluate assertion
            proof_data["assertion"] = assertion
            # Simple assertion types
            if assertion.startswith("file_exists:"):
                path = assertion.split(":", 1)[1].strip()
                proof_data["result"] = os.path.exists(path)
            elif assertion.startswith("file_hash:"):
                parts = assertion.split(":", 2)
                if len(parts) == 3:
                    path, expected = parts[1].strip(), parts[2].strip()
                    if os.path.exists(path):
                        with open(path, "rb") as f:
                            actual = hashlib.sha256(f.read()).hexdigest()[:16]
                        proof_data["result"] = actual == expected
                    else:
                        proof_data["result"] = False
            else:
                proof_data["result"] = "unknown_assertion_type"

        if include_timestamp:
            proof_data["timestamp"] = datetime.now(timezone.utc).replace(tzinfo=None).isoformat()

        proof_hash = hashlib.sha256(
            json.dumps(proof_data, sort_keys=True).encode()
        ).hexdigest()[:16]

        return {
            "success": True,
            "proof_hash": proof_hash,
            "proof_data": proof_data,
        }

    def _execute_verify(
        self, params: dict[str, Any], context: dict[str, Any]
    ) -> dict[str, Any]:
        """Execute SupeVerify - verify an existing proof."""
        proof_id = params.get("proof_id", "")

        # Look for proof in execution history
        for result in self.execution_history:
            if result.proof_hash == proof_id:
                return {
                    "success": True,
                    "verified": True,
                    "action": result.action_name,
                    "executed_at": result.started_at,
                }

        return {
            "success": True,
            "verified": False,
            "error": f"Proof not found: {proof_id}",
        }


# Convenience function
def execute_supe_action(
    action_name: str,
    params: dict[str, Any],
    context: dict[str, Any] | None = None,
    executor: SupeExecutor | None = None,
) -> ExecutionResult:
    """Execute a supe action with default executor."""
    if executor is None:
        executor = SupeExecutor()
    return executor.execute(action_name, params, context)
