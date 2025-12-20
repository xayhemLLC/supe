"""Observation primitives for capturing system state.

These primitives act as measurement instruments for the Tascer framework,
providing deterministic ways to observe and record state before and after
tasc execution.
"""

from .context import capture_context
from .terminal import run_and_observe, terminal_watch, TerminalResult, WatchResult, StreamChunk
from .git import capture_git_state, get_git_diff, get_untracked_files
from .file_ops import snapshot_file, snapshot_directory, diff_directories, FileSnapshot, DirectoryDiff
from .http import http_request, http_get, http_post, HttpResponse
from .process import process_list, process_logs, process_start, process_stop, process_restart, ProcessInfo
from .env import env_read, env_set, env_reset, EnvReadResult, EnvSetResult
from .file_mutations import file_write, file_patch, file_delete, WriteResult, PatchResult, DeleteResult
from .git_mutations import git_checkout, git_commit, git_log, CheckoutResult, CommitResult
from .control import sleep_wait, noop, WaitResult, NoopResult
from .browser import browser_capture, browser_evaluate, browser_interact, BrowserState, BrowserNotAvailableError
from .frontend import frontend_state_dump, frontend_inject, FrontendState, FrontendNotAvailableError
from .sandbox import sandbox_enter, sandbox_exit, is_in_sandbox, SandboxNotImplementedError

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

