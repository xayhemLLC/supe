"""Process primitives.

ACTIONS:
- process.list: List running processes
- process.logs: Capture process output
- process.start: Start a tracked process (mutation)
- process.stop: Stop a running process (mutation)
- process.restart: Restart a process (mutation)
"""

import os
import signal
import subprocess
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Set


@dataclass
class ProcessInfo:
    """Information about a running process."""
    
    pid: int
    command: str
    status: str  # running, sleeping, stopped, zombie
    cpu_percent: Optional[float] = None
    memory_mb: Optional[float] = None
    started_at: Optional[datetime] = None
    cwd: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "pid": self.pid,
            "command": self.command,
            "status": self.status,
            "cpu_percent": self.cpu_percent,
            "memory_mb": self.memory_mb,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "cwd": self.cwd,
        }


@dataclass
class ProcessListResult:
    """Result of listing processes."""
    
    processes: List[ProcessInfo]
    timestamp: datetime
    filter_pattern: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "processes": [p.to_dict() for p in self.processes],
            "timestamp": self.timestamp.isoformat(),
            "filter_pattern": self.filter_pattern,
        }


@dataclass
class ProcessLogs:
    """Captured process logs."""
    
    pid: int
    stdout: str
    stderr: str
    captured_at: datetime
    since: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "pid": self.pid,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "captured_at": self.captured_at.isoformat(),
            "since": self.since.isoformat() if self.since else None,
        }


@dataclass
class StartedProcess:
    """A process that was started by process.start."""
    
    pid: int
    command: str
    cwd: str
    started_at: datetime
    env: Dict[str, str] = field(default_factory=dict)
    
    # Internal process handle (not serialized)
    _process: Optional[subprocess.Popen] = field(default=None, repr=False)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "pid": self.pid,
            "command": self.command,
            "cwd": self.cwd,
            "started_at": self.started_at.isoformat(),
            "env": self.env,
        }


# Global registry of started processes
_started_processes: Dict[int, StartedProcess] = {}


def process_list(
    filter_pattern: Optional[str] = None,
    user_only: bool = True,
) -> ProcessListResult:
    """List running processes.
    
    ACTION: process.list
    
    Args:
        filter_pattern: Filter processes by command pattern.
        user_only: Only list processes owned by current user.
    
    Returns:
        ProcessListResult with matching processes.
    """
    processes = []
    
    try:
        # Use ps command for cross-platform compatibility
        cmd = ["ps", "-eo", "pid,comm,stat"]
        if user_only:
            cmd = ["ps", "-u", str(os.getuid()), "-o", "pid,comm,stat"]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=10,
        )
        
        if result.returncode == 0:
            lines = result.stdout.strip().split("\n")[1:]  # Skip header
            for line in lines:
                parts = line.split()
                if len(parts) >= 3:
                    pid = int(parts[0])
                    command = parts[1]
                    status = parts[2]
                    
                    # Apply filter
                    if filter_pattern and filter_pattern not in command:
                        continue
                    
                    processes.append(ProcessInfo(
                        pid=pid,
                        command=command,
                        status=status,
                    ))
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    
    return ProcessListResult(
        processes=processes,
        timestamp=datetime.now(),
        filter_pattern=filter_pattern,
    )


def process_logs(
    pid: int,
    lines: int = 100,
) -> ProcessLogs:
    """Capture output from a running process.
    
    ACTION: process.logs
    
    Args:
        pid: Process ID to capture logs from.
        lines: Number of lines to capture.
    
    Returns:
        ProcessLogs with stdout/stderr.
    """
    stdout = ""
    stderr = ""
    
    # Check if it's a process we started
    if pid in _started_processes:
        proc = _started_processes[pid]
        if proc._process:
            try:
                # Try to read available output (non-blocking)
                if proc._process.stdout:
                    stdout = proc._process.stdout.read() or ""
                if proc._process.stderr:
                    stderr = proc._process.stderr.read() or ""
            except Exception:
                pass
    
    return ProcessLogs(
        pid=pid,
        stdout=stdout,
        stderr=stderr,
        captured_at=datetime.now(),
    )


def process_start(
    command: str,
    cwd: Optional[str] = None,
    env: Optional[Dict[str, str]] = None,
    shell: bool = True,
) -> StartedProcess:
    """Start a tracked process.
    
    ACTION: process.start (MUTATION)
    
    Args:
        command: Command to run.
        cwd: Working directory.
        env: Environment variables to set.
        shell: Run through shell.
    
    Returns:
        StartedProcess with PID and tracking info.
    """
    if cwd is None:
        cwd = os.getcwd()
    
    # Prepare environment
    process_env = os.environ.copy()
    if env:
        process_env.update(env)
    
    proc = subprocess.Popen(
        command,
        cwd=cwd,
        env=process_env,
        shell=shell,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    
    started = StartedProcess(
        pid=proc.pid,
        command=command,
        cwd=cwd,
        started_at=datetime.now(),
        env=env or {},
        _process=proc,
    )
    
    _started_processes[proc.pid] = started
    
    return started


def process_stop(
    pid: int,
    force: bool = False,
    timeout_sec: float = 10,
) -> Dict[str, Any]:
    """Stop a running process.
    
    ACTION: process.stop (MUTATION)
    
    Args:
        pid: Process ID to stop.
        force: Use SIGKILL instead of SIGTERM.
        timeout_sec: Wait time before force killing.
    
    Returns:
        Dict with stop result.
    """
    result = {
        "pid": pid,
        "stopped": False,
        "exit_code": None,
        "forced": False,
    }
    
    try:
        # Send signal
        sig = signal.SIGKILL if force else signal.SIGTERM
        os.kill(pid, sig)
        result["stopped"] = True
        result["forced"] = force
        
        # If we have the process handle, wait for it
        if pid in _started_processes:
            proc = _started_processes[pid]._process
            if proc:
                try:
                    proc.wait(timeout=timeout_sec)
                    result["exit_code"] = proc.returncode
                except subprocess.TimeoutExpired:
                    proc.kill()
                    result["forced"] = True
            del _started_processes[pid]
            
    except ProcessLookupError:
        result["stopped"] = True  # Already stopped
    except PermissionError:
        result["stopped"] = False
        
    return result


def process_restart(
    pid: int,
    timeout_sec: float = 10,
) -> Dict[str, Any]:
    """Restart a process.
    
    ACTION: process.restart (MUTATION)
    
    Args:
        pid: Process ID to restart.
        timeout_sec: Wait time for stop.
    
    Returns:
        Dict with old_pid, new_pid, and result.
    """
    result = {
        "old_pid": pid,
        "new_pid": None,
        "success": False,
    }
    
    # Get process info before stopping
    if pid not in _started_processes:
        result["error"] = "Process not tracked - cannot restart"
        return result
    
    proc_info = _started_processes[pid]
    command = proc_info.command
    cwd = proc_info.cwd
    env = proc_info.env
    
    # Stop the process
    stop_result = process_stop(pid, timeout_sec=timeout_sec)
    if not stop_result["stopped"]:
        result["error"] = "Failed to stop process"
        return result
    
    # Start again
    new_proc = process_start(command=command, cwd=cwd, env=env)
    
    result["new_pid"] = new_proc.pid
    result["success"] = True
    
    return result


def get_tracked_pids() -> Set[int]:
    """Get set of all tracked process PIDs."""
    return set(_started_processes.keys())


def is_running(pid: int) -> bool:
    """Check if a process is still running."""
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
