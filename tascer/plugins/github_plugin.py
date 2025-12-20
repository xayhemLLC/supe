"""GitHub Integration Plugin for Tasc.

Enables Tasc to:
- Create issues and comments
- Trigger workflows
- Post status checks
- Create PRs (read-only analysis)
"""

import json
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional
from urllib.request import Request, urlopen
from urllib.error import URLError

from . import Plugin, PluginInfo, PluginEvent, PluginStatus


class GitHubPlugin(Plugin):
    """GitHub integration for Tasc.
    
    Provides actions:
    - github.comment: Add a comment to an issue/PR
    - github.status: Set commit status
    - github.issue: Create an issue
    - github.workflow: Trigger a workflow
    
    Configuration:
        Set GITHUB_TOKEN env var.
    """
    
    def __init__(
        self,
        token: Optional[str] = None,
        repo: Optional[str] = None,  # owner/repo
    ):
        super().__init__()
        self.token = token or os.environ.get("GITHUB_TOKEN")
        self.repo = repo or os.environ.get("GITHUB_REPOSITORY")
        self.api_base = "https://api.github.com"
    
    @property
    def info(self) -> PluginInfo:
        return PluginInfo(
            name="github",
            version="1.0.0",
            description="GitHub integration for issues, PRs, and workflows",
            author="Tasc",
            requires=[],
            capabilities=["issues", "comments", "status", "workflows"],
        )
    
    async def initialize(self) -> bool:
        """Initialize GitHub connection."""
        if not self.token:
            self._status = PluginStatus.ERROR
            self._error = "No GitHub token. Set GITHUB_TOKEN env var."
            return False
        
        self._status = PluginStatus.READY
        return True
    
    def get_actions(self) -> Dict[str, Callable]:
        """Return GitHub actions."""
        return {
            "comment": self.add_comment,
            "status": self.set_status,
            "issue": self.create_issue,
            "workflow": self.trigger_workflow,
        }
    
    def get_context(self) -> Dict[str, Any]:
        """Return GitHub context."""
        return {
            "configured": bool(self.token),
            "repo": self.repo,
        }
    
    def add_comment(
        self,
        issue_number: int,
        body: str,
        repo: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Add a comment to an issue or PR.
        
        ACTION: github.comment
        """
        repo = repo or self.repo
        if not repo:
            return {"error": "No repo specified"}
        
        url = f"{self.api_base}/repos/{repo}/issues/{issue_number}/comments"
        result = self._api_request("POST", url, {"body": body})
        
        return result or {"error": "Failed to add comment"}
    
    def set_status(
        self,
        sha: str,
        state: str,  # pending, success, error, failure
        description: str,
        context: str = "tascer",
        target_url: Optional[str] = None,
        repo: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Set commit status.
        
        ACTION: github.status
        """
        repo = repo or self.repo
        if not repo:
            return {"error": "No repo specified"}
        
        url = f"{self.api_base}/repos/{repo}/statuses/{sha}"
        payload = {
            "state": state,
            "description": description,
            "context": context,
        }
        if target_url:
            payload["target_url"] = target_url
        
        result = self._api_request("POST", url, payload)
        return result or {"error": "Failed to set status"}
    
    def create_issue(
        self,
        title: str,
        body: str,
        labels: Optional[List[str]] = None,
        repo: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a new issue.
        
        ACTION: github.issue
        """
        repo = repo or self.repo
        if not repo:
            return {"error": "No repo specified"}
        
        url = f"{self.api_base}/repos/{repo}/issues"
        payload = {"title": title, "body": body}
        if labels:
            payload["labels"] = labels
        
        result = self._api_request("POST", url, payload)
        return result or {"error": "Failed to create issue"}
    
    def trigger_workflow(
        self,
        workflow_id: str,
        ref: str = "main",
        inputs: Optional[Dict[str, str]] = None,
        repo: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Trigger a GitHub Actions workflow.
        
        ACTION: github.workflow
        """
        repo = repo or self.repo
        if not repo:
            return {"error": "No repo specified"}
        
        url = f"{self.api_base}/repos/{repo}/actions/workflows/{workflow_id}/dispatches"
        payload = {"ref": ref}
        if inputs:
            payload["inputs"] = inputs
        
        result = self._api_request("POST", url, payload)
        return result if result else {"success": True}
    
    def _api_request(
        self,
        method: str,
        url: str,
        data: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """Make a GitHub API request."""
        if not self.token:
            return None
        
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        
        if data:
            headers["Content-Type"] = "application/json"
        
        try:
            body = json.dumps(data).encode("utf-8") if data else None
            req = Request(url, data=body, headers=headers, method=method)
            
            with urlopen(req, timeout=30) as response:
                if response.status in (200, 201):
                    return json.loads(response.read().decode("utf-8"))
                elif response.status == 204:
                    return {}
        except URLError as e:
            return {"error": str(e)}
        except json.JSONDecodeError:
            return {}
        
        return None
    
    def on_event(self, event: PluginEvent) -> Optional[Dict[str, Any]]:
        """React to Tasc events."""
        if event.event_type == "commit_ready":
            sha = event.data.get("sha")
            if sha:
                self.set_status(
                    sha=sha,
                    state="success",
                    description="Tasc verification complete",
                )
        return None
