"""Action Executor.

Safe action execution with validation, logging, and error handling.
"""

import os
import time
from typing import Any, Dict, List, Optional

from .base import (
    ActionType,
    AgentAction,
    ActionResult,
    ValidationResult,
)
from .registry import (
    get_action_handler,
    get_action_metadata,
    is_dangerous,
    requires_approval,
)


class ActionExecutor:
    """Executes agent actions with safety checks and logging.
    
    Provides:
    - Parameter validation
    - Dangerous action checks
    - Approval gate integration
    - Result logging to AB Memory
    """
    
    def __init__(
        self,
        session_id: str,
        tasc_id: str,
        cwd: Optional[str] = None,
        allow_dangerous: bool = False,
        auto_approve: bool = False,
    ):
        self.session_id = session_id
        self.tasc_id = tasc_id
        self.cwd = cwd or os.getcwd()
        self.allow_dangerous = allow_dangerous
        self.auto_approve = auto_approve
        self.step_index = 0
        self.action_log: List[Dict[str, Any]] = []
    
    def execute(
        self,
        action_type: ActionType,
        params: Dict[str, Any],
        thought: Optional[str] = None,
    ) -> ActionResult:
        """Execute an action with full validation and logging.
        
        Args:
            action_type: Type of action to execute
            params: Action parameters
            thought: Optional reasoning for this action
            
        Returns:
            ActionResult with output and validation results
        """
        # Create action object
        action = AgentAction.create(
            action_type=action_type,
            params=params,
            tasc_id=self.tasc_id,
            session_id=self.session_id,
            step_index=self.step_index,
            thought=thought,
        )
        
        self.step_index += 1
        start_time = time.time()
        
        try:
            # Validate parameters
            validation_errors = validate_params(action_type, params)
            if validation_errors:
                return ActionResult(
                    action_id=action.id,
                    status="failed",
                    error=f"Invalid parameters: {', '.join(validation_errors)}",
                    validations=[
                        ValidationResult(
                            name="param_validation",
                            status="fail",
                            message=err,
                        )
                        for err in validation_errors
                    ],
                )
            
            # Check dangerous actions
            if is_dangerous(action_type) and not self.allow_dangerous:
                return ActionResult(
                    action_id=action.id,
                    status="failed",
                    error=f"Dangerous action '{action_type.value}' blocked. Use allow_dangerous=True to override.",
                    validations=[
                        ValidationResult(
                            name="safety_check",
                            status="fail",
                            message="Action blocked due to safety policy",
                        )
                    ],
                )
            
            # Check approval requirement
            if requires_approval(action_type) and not self.auto_approve:
                from ..approval import request_approval
                
                approval = request_approval(
                    tasc_id=self.tasc_id,
                    title=f"Approve: {action_type.value}",
                    description=f"Action requires approval: {params}",
                    action_type=action_type.value,
                    context=params,
                )
                
                return ActionResult(
                    action_id=action.id,
                    status="pending",
                    output_summary=f"Awaiting approval: {approval.id}",
                    validations=[
                        ValidationResult(
                            name="approval_required",
                            status="skip",
                            message=f"Approval requested: {approval.id}",
                            details={"approval_id": approval.id},
                        )
                    ],
                )
            
            # Execute the action
            result = self._execute_action(action)
            
        except Exception as e:
            result = ActionResult(
                action_id=action.id,
                status="failed",
                error=str(e),
            )
        
        # Record timing
        result.duration_ms = (time.time() - start_time) * 1000
        action.duration_ms = result.duration_ms
        
        # Log action
        self.action_log.append({
            "action": action.to_dict(),
            "result": result.to_dict(),
        })
        
        return result
    
    def _execute_action(self, action: AgentAction) -> ActionResult:
        """Execute the action using the registered handler or built-in."""
        
        # Try registered handler first
        handler = get_action_handler(action.type)
        if handler:
            return handler(action)
        
        # Built-in handlers
        if action.type == ActionType.READ_FILE:
            return self._read_file(action)
        elif action.type == ActionType.SEARCH_CODEBASE:
            return self._search_codebase(action)
        elif action.type == ActionType.RUN_CMD:
            return self._run_cmd(action)
        elif action.type == ActionType.RUN_TESTS:
            return self._run_tests(action)
        elif action.type == ActionType.FINISH:
            return self._finish(action)
        elif action.type == ActionType.EDIT_FILE:
            return self._edit_file(action)
        else:
            return ActionResult(
                action_id=action.id,
                status="failed",
                error=f"No handler for action type: {action.type}",
            )
    
    def _read_file(self, action: AgentAction) -> ActionResult:
        """Read file contents."""
        path = action.params.get("path")
        start_line = action.params.get("start_line")
        end_line = action.params.get("end_line")
        
        full_path = os.path.join(self.cwd, path) if not os.path.isabs(path) else path
        
        if not os.path.exists(full_path):
            return ActionResult(
                action_id=action.id,
                status="failed",
                error=f"File not found: {path}",
            )
        
        with open(full_path, 'r') as f:
            lines = f.readlines()
        
        if start_line or end_line:
            start = (start_line or 1) - 1
            end = end_line or len(lines)
            content = ''.join(lines[start:end])
        else:
            content = ''.join(lines)
        
        return ActionResult(
            action_id=action.id,
            status="ok",
            output=content,
            output_summary=f"Read {len(lines)} lines from {path}",
            validations=[
                ValidationResult(name="file_exists", status="pass", message="File found"),
            ],
        )
    
    def _search_codebase(self, action: AgentAction) -> ActionResult:
        """Search codebase using grep."""
        import subprocess
        
        query = action.params.get("query")
        path = action.params.get("path", ".")
        max_results = action.params.get("max_results", 50)
        
        try:
            result = subprocess.run(
                ["grep", "-rn", "--include=*.py", "--include=*.ts", "--include=*.js", query, path],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=self.cwd,
            )
            
            lines = result.stdout.strip().split('\n')[:max_results]
            matches = [l for l in lines if l]
            
            return ActionResult(
                action_id=action.id,
                status="ok",
                output=matches,
                output_summary=f"Found {len(matches)} matches for '{query}'",
            )
        except subprocess.TimeoutExpired:
            return ActionResult(
                action_id=action.id,
                status="failed",
                error="Search timed out",
            )
    
    def _run_cmd(self, action: AgentAction) -> ActionResult:
        """Run a shell command."""
        from ..primitives import run_and_observe
        
        command = action.params.get("command")
        cwd = action.params.get("cwd") or self.cwd
        timeout = action.params.get("timeout", 60)
        
        result = run_and_observe(command, cwd=cwd, shell=True, timeout_sec=timeout)
        
        return ActionResult(
            action_id=action.id,
            status="ok" if result.exit_code == 0 else "failed",
            output={"stdout": result.stdout, "stderr": result.stderr, "exit_code": result.exit_code},
            output_summary=f"Exit code: {result.exit_code}",
            validations=[
                ValidationResult(
                    name="exit_code",
                    status="pass" if result.exit_code == 0 else "fail",
                    message=f"Exit code: {result.exit_code}",
                ),
            ],
            duration_ms=result.duration_ms,
        )
    
    def _run_tests(self, action: AgentAction) -> ActionResult:
        """Run test suite."""
        pattern = action.params.get("pattern", "")
        path = action.params.get("path", "tests/")
        
        cmd = f"pytest {path} {pattern} -v --tb=short"
        action.params["command"] = cmd
        return self._run_cmd(action)
    
    def _edit_file(self, action: AgentAction) -> ActionResult:
        """Apply a diff to a file."""
        from .patch import apply_patch
        
        path = action.params.get("path")
        diff = action.params.get("diff")
        
        result = apply_patch(diff, cwd=self.cwd)
        
        return ActionResult(
            action_id=action.id,
            status="ok" if result.success else "failed",
            output=result.to_dict() if hasattr(result, 'to_dict') else str(result),
            output_summary=f"Patched {path}" if result.success else f"Patch failed: {result.error if hasattr(result, 'error') else 'unknown'}",
        )
    
    def _finish(self, action: AgentAction) -> ActionResult:
        """Mark task as complete."""
        summary = action.params.get("summary", "Task completed")
        risks = action.params.get("risks", [])
        follow_ups = action.params.get("follow_ups", [])
        
        return ActionResult(
            action_id=action.id,
            status="ok",
            output={
                "summary": summary,
                "risks": risks,
                "follow_ups": follow_ups,
            },
            output_summary=summary,
        )


def validate_params(action_type: ActionType, params: Dict[str, Any]) -> List[str]:
    """Validate action parameters against metadata.
    
    Returns list of error messages, empty if valid.
    """
    meta = get_action_metadata(action_type)
    if not meta:
        return []  # No metadata, assume valid
    
    errors = []
    for required in meta.required_params:
        if required not in params:
            errors.append(f"Missing required parameter: {required}")
    
    return errors


def execute_action(
    action_type: ActionType,
    params: Dict[str, Any],
    session_id: str = "default",
    tasc_id: str = "default",
    **kwargs,
) -> ActionResult:
    """Convenience function to execute a single action.
    
    Creates a temporary executor for one-off action execution.
    """
    executor = ActionExecutor(
        session_id=session_id,
        tasc_id=tasc_id,
        **kwargs,
    )
    return executor.execute(action_type, params)
