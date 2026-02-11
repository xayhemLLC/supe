"""Observation primitives for capturing system state.

These primitives act as measurement instruments for the Tascer framework,
providing deterministic ways to observe and record state before and after
tasc execution.
"""

from .browser import (
    BrowserNotAvailableError,
    BrowserState,
    browser_capture,
    browser_evaluate,
    browser_interact,
)
from .context import capture_context
from .control import NoopResult, WaitResult, noop, sleep_wait
from .env import EnvReadResult, EnvSetResult, env_read, env_reset, env_set
from .file_mutations import (
    DeleteResult,
    PatchResult,
    WriteResult,
    file_delete,
    file_patch,
    file_write,
)
from .file_ops import (
    DirectoryDiff,
    FileSnapshot,
    diff_directories,
    snapshot_directory,
    snapshot_file,
)
from .frontend import FrontendNotAvailableError, FrontendState, frontend_inject, frontend_state_dump
from .git import capture_git_state, get_git_diff, get_untracked_files
from .git_mutations import CheckoutResult, CommitResult, git_checkout, git_commit, git_log
from .http import HttpResponse, http_get, http_post, http_request
from .process import (
    ProcessInfo,
    process_list,
    process_logs,
    process_restart,
    process_start,
    process_stop,
)
from .sandbox import SandboxNotImplementedError, is_in_sandbox, sandbox_enter, sandbox_exit
from .terminal import StreamChunk, TerminalResult, WatchResult, run_and_observe, terminal_watch

__all__ = [
    # Context
    "capture_context",
    # Terminal
    "run_and_observe",
    "terminal_watch",
    "TerminalResult",
    "WatchResult",
    "StreamChunk",
    # Git
    "capture_git_state",
    "get_git_diff",
    "get_untracked_files",
    "git_checkout",
    "git_commit",
    "git_log",
    "CheckoutResult",
    "CommitResult",
    # Files
    "snapshot_file",
    "snapshot_directory",
    "diff_directories",
    "FileSnapshot",
    "DirectoryDiff",
    "file_write",
    "file_patch",
    "file_delete",
    "WriteResult",
    "PatchResult",
    "DeleteResult",
    # HTTP
    "http_request",
    "http_get",
    "http_post",
    "HttpResponse",
    # Process
    "process_list",
    "process_logs",
    "process_start",
    "process_stop",
    "process_restart",
    "ProcessInfo",
    # Environment
    "env_read",
    "env_set",
    "env_reset",
    "EnvReadResult",
    "EnvSetResult",
    # Control
    "sleep_wait",
    "noop",
    "WaitResult",
    "NoopResult",
    # Browser (stubs)
    "browser_capture",
    "browser_evaluate",
    "browser_interact",
    "BrowserState",
    "BrowserNotAvailableError",
    # Frontend (stubs)
    "frontend_state_dump",
    "frontend_inject",
    "FrontendState",
    "FrontendNotAvailableError",
    # Sandbox (stubs)
    "sandbox_enter",
    "sandbox_exit",
    "is_in_sandbox",
    "SandboxNotImplementedError",
]

