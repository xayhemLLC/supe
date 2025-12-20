"""TASC_CORE_TERMINAL_RUN_AND_OBSERVE - Run terminal commands and capture output.

Hypothesis: "We can run a terminal op, detect completion, capture outputs,
and parse results deterministically."

Evidence: stdout, stderr, exit_code, timings, working dir, env allowlist.

Supports completion detection modes:
- process exit (default)
- sentinel line in stdout (HOOK:COMPLETE)
- file-based hook (a file appears)
- timeout with partial evidence
"""

import os
import subprocess
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Union


@dataclass
class TerminalResult:
    """Result of a terminal command execution."""
    
    exit_code: int
    stdout: str
    stderr: str
    duration_ms: float
    cwd: str
    env_snapshot: Dict[str, str] = field(default_factory=dict)
    completion_mode: str = "process_exit"  # process_exit | sentinel | file_hook | timeout
    timed_out: bool = False
    
    def to_dict(self) -> Dict:
        return {
            "exit_code": self.exit_code,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "duration_ms": self.duration_ms,
            "cwd": self.cwd,
            "env_snapshot": self.env_snapshot,
            "completion_mode": self.completion_mode,
            "timed_out": self.timed_out,
        }


def run_and_observe(
    command: Union[str, List[str]],
    cwd: Optional[str] = None,
    timeout_sec: float = 60,
    completion_sentinel: Optional[str] = None,
    completion_file: Optional[str] = None,
    env_allowlist: Optional[List[str]] = None,
    env_override: Optional[Dict[str, str]] = None,
    shell: bool = False,
) -> TerminalResult:
    """Run a terminal command and capture outputs deterministically.
    
    TASC_CORE_TERMINAL_RUN_AND_OBSERVE implementation.
    
    Args:
        command: Command to run (string or list of args).
        cwd: Working directory. Defaults to current directory.
        timeout_sec: Maximum execution time in seconds.
        completion_sentinel: String to watch for in stdout indicating completion.
        completion_file: Path to file whose appearance indicates completion.
        env_allowlist: Env vars to capture in result (never secrets!).
        env_override: Additional env vars to set for the command.
        shell: Whether to run through shell.
    
    Returns:
        TerminalResult with captured outputs and timing.
    """
    if cwd is None:
        cwd = os.getcwd()
    
    # Prepare environment
    env = os.environ.copy()
    if env_override:
        env.update(env_override)
    
    # Capture allowed env vars
    captured_env = {}
    if env_allowlist:
        for var in env_allowlist:
            if var in env:
                captured_env[var] = env[var]
    
    start_time = time.perf_counter()
    timed_out = False
    completion_mode = "process_exit"
    
    try:
        # If using sentinel or file hook, we need to handle differently
        if completion_sentinel or completion_file:
            # For sentinel/file completion, use Popen for real-time monitoring
            result = _run_with_hooks(
                command=command,
                cwd=cwd,
                env=env,
                timeout_sec=timeout_sec,
                completion_sentinel=completion_sentinel,
                completion_file=completion_file,
                shell=shell,
            )
            completion_mode = result["completion_mode"]
            timed_out = result["timed_out"]
            stdout = result["stdout"]
            stderr = result["stderr"]
            exit_code = result["exit_code"]
        else:
            # Simple subprocess.run
            proc_result = subprocess.run(
                command,
                cwd=cwd,
                env=env,
                capture_output=True,
                text=True,
                timeout=timeout_sec,
                shell=shell,
            )
            stdout = proc_result.stdout
            stderr = proc_result.stderr
            exit_code = proc_result.returncode
    except subprocess.TimeoutExpired as e:
        timed_out = True
        completion_mode = "timeout"
        stdout = e.stdout.decode() if e.stdout else ""
        stderr = e.stderr.decode() if e.stderr else ""
        exit_code = -1
    except FileNotFoundError:
        timed_out = False
        stdout = ""
        stderr = f"Command not found: {command}"
        exit_code = 127
    except Exception as e:
        timed_out = False
        stdout = ""
        stderr = str(e)
        exit_code = -1
    
    end_time = time.perf_counter()
    duration_ms = (end_time - start_time) * 1000
    
    return TerminalResult(
        exit_code=exit_code,
        stdout=stdout,
        stderr=stderr,
        duration_ms=duration_ms,
        cwd=cwd,
        env_snapshot=captured_env,
        completion_mode=completion_mode,
        timed_out=timed_out,
    )


def _run_with_hooks(
    command: Union[str, List[str]],
    cwd: str,
    env: Dict[str, str],
    timeout_sec: float,
    completion_sentinel: Optional[str],
    completion_file: Optional[str],
    shell: bool,
) -> Dict:
    """Run a command with sentinel or file completion detection."""
    stdout_lines: List[str] = []
    stderr_lines: List[str] = []
    completion_mode = "process_exit"
    timed_out = False
    
    proc = subprocess.Popen(
        command,
        cwd=cwd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        shell=shell,
    )
    
    start_time = time.time()
    
    try:
        while True:
            # Check timeout
            elapsed = time.time() - start_time
            if elapsed > timeout_sec:
                proc.kill()
                timed_out = True
                completion_mode = "timeout"
                break
            
            # Check if process exited
            poll = proc.poll()
            if poll is not None:
                completion_mode = "process_exit"
                break
            
            # Check file hook
            if completion_file and os.path.exists(completion_file):
                proc.terminate()
                completion_mode = "file_hook"
                break
            
            # Read available output (non-blocking would be better, but keeping simple)
            time.sleep(0.1)
        
        # Collect remaining output
        stdout_text, stderr_text = proc.communicate(timeout=5)
        stdout_lines.append(stdout_text)
        stderr_lines.append(stderr_text)
        
        # Check for sentinel in stdout
        full_stdout = "".join(stdout_lines)
        if completion_sentinel and completion_sentinel in full_stdout:
            completion_mode = "sentinel"
        
        return {
            "stdout": full_stdout,
            "stderr": "".join(stderr_lines),
            "exit_code": proc.returncode if proc.returncode is not None else -1,
            "completion_mode": completion_mode,
            "timed_out": timed_out,
        }
    except subprocess.TimeoutExpired:
        proc.kill()
        return {
            "stdout": "".join(stdout_lines),
            "stderr": "".join(stderr_lines),
            "exit_code": -1,
            "completion_mode": "timeout",
            "timed_out": True,
        }


@dataclass
class StreamChunk:
    """A chunk of streaming output."""
    
    stream: str  # "stdout" or "stderr"
    content: str
    timestamp: float
    
    def to_dict(self) -> Dict:
        return {
            "stream": self.stream,
            "content": self.content,
            "timestamp": self.timestamp,
        }


@dataclass
class WatchResult:
    """Result of watching a long-running command."""
    
    exit_code: Optional[int]
    chunks: List[StreamChunk]
    completion_mode: str
    started_at: float
    ended_at: Optional[float]
    pid: int
    still_running: bool = False
    
    def to_dict(self) -> Dict:
        return {
            "exit_code": self.exit_code,
            "chunks": [c.to_dict() for c in self.chunks],
            "completion_mode": self.completion_mode,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "pid": self.pid,
            "still_running": self.still_running,
        }
    
    @property
    def stdout(self) -> str:
        """Get all stdout as single string."""
        return "".join(c.content for c in self.chunks if c.stream == "stdout")
    
    @property
    def stderr(self) -> str:
        """Get all stderr as single string."""
        return "".join(c.content for c in self.chunks if c.stream == "stderr")


def terminal_watch(
    command: Union[str, List[str]],
    cwd: Optional[str] = None,
    max_wait_sec: float = 60,
    check_interval_sec: float = 0.5,
    completion_sentinel: Optional[str] = None,
    completion_file: Optional[str] = None,
    shell: bool = False,
    env_override: Optional[Dict[str, str]] = None,
) -> WatchResult:
    """Watch a long-running command with streaming output.
    
    ACTION: terminal.watch
    
    Unlike run_and_observe, this streams output in chunks and can
    detect completion via sentinel or file hooks while the process runs.
    
    Args:
        command: Command to run.
        cwd: Working directory.
        max_wait_sec: Maximum time to wait for completion.
        check_interval_sec: How often to check for output/completion.
        completion_sentinel: String in output indicating completion.
        completion_file: File whose appearance indicates completion.
        shell: Run through shell.
        env_override: Additional environment variables.
    
    Returns:
        WatchResult with streaming chunks and completion status.
    """
    if cwd is None:
        cwd = os.getcwd()
    
    # Prepare environment
    env = os.environ.copy()
    if env_override:
        env.update(env_override)
    
    started_at = time.time()
    chunks: List[StreamChunk] = []
    completion_mode = "process_exit"
    
    proc = subprocess.Popen(
        command,
        cwd=cwd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        shell=shell,
    )
    
    try:
        while True:
            elapsed = time.time() - started_at
            
            # Check timeout
            if elapsed > max_wait_sec:
                completion_mode = "timeout"
                break
            
            # Check if process exited
            if proc.poll() is not None:
                completion_mode = "process_exit"
                break
            
            # Check file hook
            if completion_file and os.path.exists(completion_file):
                completion_mode = "file_hook"
                break
            
            # Read available output
            # Note: This is simplified - real implementation would use select/poll
            time.sleep(check_interval_sec)
            
            # Try to read without blocking (simplified approach)
            try:
                if proc.stdout and proc.stdout.readable():
                    line = proc.stdout.readline()
                    if line:
                        chunks.append(StreamChunk(
                            stream="stdout",
                            content=line,
                            timestamp=time.time(),
                        ))
                        # Check sentinel
                        if completion_sentinel and completion_sentinel in line:
                            completion_mode = "sentinel"
                            break
            except Exception:
                pass
        
        # Collect remaining output
        if completion_mode != "timeout":
            remaining_stdout, remaining_stderr = proc.communicate(timeout=5)
            if remaining_stdout:
                chunks.append(StreamChunk(
                    stream="stdout",
                    content=remaining_stdout,
                    timestamp=time.time(),
                ))
            if remaining_stderr:
                chunks.append(StreamChunk(
                    stream="stderr",
                    content=remaining_stderr,
                    timestamp=time.time(),
                ))
        
        return WatchResult(
            exit_code=proc.returncode,
            chunks=chunks,
            completion_mode=completion_mode,
            started_at=started_at,
            ended_at=time.time(),
            pid=proc.pid,
            still_running=proc.poll() is None,
        )
        
    except Exception as e:
        proc.kill()
        return WatchResult(
            exit_code=-1,
            chunks=chunks,
            completion_mode="error",
            started_at=started_at,
            ended_at=time.time(),
            pid=proc.pid,
            still_running=False,
        )
