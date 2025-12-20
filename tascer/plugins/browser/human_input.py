"""Human Input Handler for Browser Automation.

Provides a way for browser automation to pause and request
human input for 2FA codes, captcha solutions, and other interactive challenges.

Integrates with the tascer approval system.
"""

import json
import os
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Literal, Optional


class InputType(str, Enum):
    """Types of human input that may be required."""
    TWO_FA_CODE = "2fa_code"         # 6-digit authenticator code
    SMS_CODE = "sms_code"             # SMS verification code
    EMAIL_CODE = "email_code"         # Email verification code
    CAPTCHA_TEXT = "captcha_text"     # Text captcha solution
    CAPTCHA_CLICK = "captcha_click"   # "Click all X" captcha (need browser)
    SECURITY_QUESTION = "security_question"
    PASSWORD = "password"             # Re-enter password
    CUSTOM = "custom"                 # Custom prompt


@dataclass
class HumanInputRequest:
    """A request for human input during browser automation.
    
    The automation will pause until the human provides the requested input.
    """
    id: str
    input_type: InputType
    prompt: str
    
    # Context to help the human
    service_name: str = ""
    page_url: str = ""
    screenshot_path: Optional[str] = None  # Path to screenshot if available
    
    # Validation
    expected_format: Optional[str] = None  # e.g., "6 digits", "email"
    
    # Status
    status: Literal["pending", "completed", "timeout", "cancelled"] = "pending"
    response: Optional[str] = None
    responded_at: Optional[str] = None
    
    # Timing
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    timeout_seconds: int = 300  # 5 minutes default
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "input_type": self.input_type.value if isinstance(self.input_type, InputType) else self.input_type,
            "prompt": self.prompt,
            "service_name": self.service_name,
            "page_url": self.page_url,
            "screenshot_path": self.screenshot_path,
            "expected_format": self.expected_format,
            "status": self.status,
            "response": self.response,
            "responded_at": self.responded_at,
            "created_at": self.created_at,
            "timeout_seconds": self.timeout_seconds,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HumanInputRequest":
        input_type = data.get("input_type", "custom")
        if isinstance(input_type, str):
            try:
                input_type = InputType(input_type)
            except ValueError:
                input_type = InputType.CUSTOM
        
        return cls(
            id=data.get("id", ""),
            input_type=input_type,
            prompt=data.get("prompt", ""),
            service_name=data.get("service_name", ""),
            page_url=data.get("page_url", ""),
            screenshot_path=data.get("screenshot_path"),
            expected_format=data.get("expected_format"),
            status=data.get("status", "pending"),
            response=data.get("response"),
            responded_at=data.get("responded_at"),
            created_at=data.get("created_at", ""),
            timeout_seconds=data.get("timeout_seconds", 300),
        )


class HumanInputStore:
    """Storage for human input requests."""
    
    def __init__(self, path: str = ".tascer/human_input.json"):
        self.path = path
        self._ensure_file()
    
    def _ensure_file(self):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        if not os.path.exists(self.path):
            self._save({})
    
    def _load(self) -> Dict[str, Dict]:
        with open(self.path) as f:
            return json.load(f)
    
    def _save(self, data: Dict):
        with open(self.path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def save(self, request: HumanInputRequest):
        data = self._load()
        data[request.id] = request.to_dict()
        self._save(data)
    
    def get(self, request_id: str) -> Optional[HumanInputRequest]:
        data = self._load()
        if request_id in data:
            return HumanInputRequest.from_dict(data[request_id])
        return None
    
    def get_pending(self) -> List[HumanInputRequest]:
        data = self._load()
        return [
            HumanInputRequest.from_dict(item)
            for item in data.values()
            if item["status"] == "pending"
        ]
    
    def respond(self, request_id: str, response: str) -> HumanInputRequest:
        data = self._load()
        if request_id not in data:
            raise ValueError(f"Request not found: {request_id}")
        
        data[request_id]["response"] = response
        data[request_id]["status"] = "completed"
        data[request_id]["responded_at"] = datetime.now().isoformat()
        self._save(data)
        
        return HumanInputRequest.from_dict(data[request_id])


# Global store instance
_store: Optional[HumanInputStore] = None


def get_store() -> HumanInputStore:
    global _store
    if _store is None:
        _store = HumanInputStore()
    return _store


def request_human_input(
    input_type: InputType,
    prompt: str,
    service_name: str = "",
    page_url: str = "",
    screenshot_path: Optional[str] = None,
    expected_format: Optional[str] = None,
    timeout_seconds: int = 300,
) -> HumanInputRequest:
    """Create a request for human input.
    
    This pauses the automation and creates a request that the human
    must respond to before the automation can continue.
    
    Example:
        # Request 2FA code
        request = request_human_input(
            input_type=InputType.TWO_FA_CODE,
            prompt="Enter your 6-digit authenticator code for OpenAI",
            service_name="openai",
            expected_format="6 digits",
        )
        
        # Wait for response
        code = wait_for_human_input(request.id)
        
        # Use the code
        session.post(verify_url, data={"code": code})
    """
    request = HumanInputRequest(
        id=f"input_{uuid.uuid4().hex[:12]}",
        input_type=input_type,
        prompt=prompt,
        service_name=service_name,
        page_url=page_url,
        screenshot_path=screenshot_path,
        expected_format=expected_format,
        timeout_seconds=timeout_seconds,
    )
    
    get_store().save(request)
    
    # Also create an approval request so it shows in `supe approve list`
    try:
        from tascer.approval import request_approval
        
        request_approval(
            tasc_id=f"browser_{request.id}",
            title=f"🔐 {input_type.value}: {service_name or 'Browser'}",
            description=prompt,
            action_type="human_input",
            requested_by="browser_automation",
            context={
                "input_type": input_type.value,
                "input_request_id": request.id,
                "page_url": page_url,
                "expected_format": expected_format,
            },
        )
    except Exception:
        pass  # Approval system optional
    
    return request


def wait_for_human_input(
    request_id: str,
    poll_interval: float = 1.0,
    timeout: Optional[int] = None,
) -> str:
    """Wait for human to provide input.
    
    Blocks until:
    - Human responds with input
    - Timeout expires
    - Request is cancelled
    
    Returns the human's response.
    
    Raises:
        TimeoutError: If timeout expires
        ValueError: If request is cancelled or not found
    """
    store = get_store()
    start_time = time.time()
    
    while True:
        request = store.get(request_id)
        
        if not request:
            raise ValueError(f"Request not found: {request_id}")
        
        if request.status == "completed" and request.response:
            return request.response
        
        if request.status == "cancelled":
            raise ValueError("Request was cancelled")
        
        # Check timeout
        effective_timeout = timeout or request.timeout_seconds
        if time.time() - start_time > effective_timeout:
            # Mark as timeout
            data = store._load()
            data[request_id]["status"] = "timeout"
            store._save(data)
            raise TimeoutError(f"Human input request timed out after {effective_timeout}s")
        
        time.sleep(poll_interval)


def respond_to_input(request_id: str, response: str) -> HumanInputRequest:
    """Provide a response to a human input request.
    
    Used by CLI or UI to submit the user's input.
    """
    return get_store().respond(request_id, response)


def get_pending_inputs() -> List[HumanInputRequest]:
    """Get all pending human input requests."""
    return get_store().get_pending()


def cancel_input(request_id: str):
    """Cancel a pending input request."""
    store = get_store()
    data = store._load()
    if request_id in data:
        data[request_id]["status"] = "cancelled"
        store._save(data)
