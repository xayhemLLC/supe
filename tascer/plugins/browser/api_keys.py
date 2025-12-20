"""API Key Manager for Browser Automation.

Automates the process of fetching, rotating, and managing API keys
from various platforms that require browser login.
"""

import os
from dataclasses import dataclass
from typing import Dict, Optional

from .session import BrowserSession, PageResult
from .human_input import (
    InputType,
    request_human_input,
    wait_for_human_input,
)


@dataclass
class APIKeyResult:
    """Result of an API key operation."""
    success: bool
    key: Optional[str] = None
    message: str = ""
    requires_human_input: bool = False
    input_request_id: Optional[str] = None


class APIKeyManager:
    """Manage API keys that require browser login.
    
    Handles:
    - Initial login with optional 2FA
    - Navigating to API key pages
    - Extracting keys from pages
    - Rotating keys
    
    Example:
        manager = APIKeyManager("openai")
        
        # Login (may prompt for 2FA)
        manager.login(
            login_url="https://platform.openai.com/login",
            username="user@example.com",
            password="secret",
        )
        
        # Get API key
        result = manager.get_key(
            dashboard_url="https://platform.openai.com/api-keys",
            key_selector="td.api-key-value code",
        )
        
        print(f"API Key: {result.key}")
    """
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.session = BrowserSession(service_name)
    
    def login(
        self,
        login_url: str,
        username: str,
        password: str,
        username_field: str = "username",
        password_field: str = "password",
        two_fa_field: str = "code",
        wait_for_2fa: bool = True,
    ) -> APIKeyResult:
        """Login to the service, handling 2FA if needed.
        
        If 2FA is detected:
        1. Prompts user for code via human_input system
        2. Waits for user to provide code
        3. Submits code and completes login
        """
        # Attempt login
        result = self.session.login(
            login_url=login_url,
            username=username,
            password=password,
            username_field=username_field,
            password_field=password_field,
        )
        
        # Check for 2FA
        if result.requires_2fa:
            if not wait_for_2fa:
                return APIKeyResult(
                    success=False,
                    message="2FA required but wait_for_2fa=False",
                    requires_human_input=True,
                )
            
            # Request 2FA code from human
            input_request = request_human_input(
                input_type=InputType.TWO_FA_CODE,
                prompt=f"Enter your 2FA code for {self.service_name}",
                service_name=self.service_name,
                page_url=login_url,
                expected_format="6 digits",
            )
            
            print(f"🔐 2FA required for {self.service_name}")
            print(f"   Request ID: {input_request.id}")
            print(f"   Use: supe input respond {input_request.id} <code>")
            
            try:
                # Wait for human to provide code
                code = wait_for_human_input(input_request.id)
                
                # Submit 2FA code
                verify_result = self.session.post(
                    login_url,  # Often same URL, may need customization
                    data={two_fa_field: code},
                )
                
                if verify_result.ok and not verify_result.requires_2fa:
                    return APIKeyResult(success=True, message="Login successful with 2FA")
                else:
                    return APIKeyResult(success=False, message="2FA verification failed")
                    
            except TimeoutError:
                return APIKeyResult(
                    success=False,
                    message="2FA code timeout - user did not respond in time",
                    requires_human_input=True,
                    input_request_id=input_request.id,
                )
        
        # Check if login succeeded
        if result.ok:
            return APIKeyResult(success=True, message="Login successful")
        else:
            return APIKeyResult(
                success=False,
                message=f"Login failed with status {result.status_code}",
            )
    
    def get_key(
        self,
        dashboard_url: str,
        key_selector: str,
        key_index: int = 0,
    ) -> APIKeyResult:
        """Fetch API key from dashboard page.
        
        Args:
            dashboard_url: URL of the API keys page
            key_selector: CSS selector to find the key element
            key_index: Which key to return if multiple found (default: first)
        """
        result = self.session.get(dashboard_url)
        
        if not result.ok:
            return APIKeyResult(
                success=False,
                message=f"Failed to load dashboard: {result.status_code}",
            )
        
        if result.requires_2fa:
            # Need to re-login with 2FA
            return APIKeyResult(
                success=False,
                message="Session expired, 2FA required",
                requires_human_input=True,
            )
        
        # Find key elements
        if not result.soup:
            return APIKeyResult(success=False, message="Failed to parse page")
        
        key_elements = result.soup.select(key_selector)
        
        if not key_elements:
            return APIKeyResult(
                success=False,
                message=f"No elements found with selector: {key_selector}",
            )
        
        if key_index >= len(key_elements):
            return APIKeyResult(
                success=False,
                message=f"Key index {key_index} out of range (found {len(key_elements)})",
            )
        
        key_text = key_elements[key_index].get_text(strip=True)
        
        return APIKeyResult(
            success=True,
            key=key_text,
            message=f"Found API key: {key_text[:8]}...{key_text[-4:]}",
        )
    
    def rotate_key(
        self,
        rotate_url: str,
        method: str = "POST",
        key_field: str = "api_key",
    ) -> APIKeyResult:
        """Rotate an API key.
        
        Args:
            rotate_url: URL to POST/GET for rotation
            method: HTTP method (POST or DELETE usually)
            key_field: Field name in response containing new key
        """
        if method.upper() == "POST":
            result = self.session.post(rotate_url)
        else:
            result = self.session.get(rotate_url)
        
        if not result.ok:
            return APIKeyResult(
                success=False,
                message=f"Rotation failed with status {result.status_code}",
            )
        
        # Try to extract new key from JSON response
        if result.json_data:
            new_key = result.json_data.get(key_field)
            if new_key:
                return APIKeyResult(
                    success=True,
                    key=new_key,
                    message="Key rotated successfully",
                )
        
        return APIKeyResult(
            success=False,
            message="Rotation succeeded but could not extract new key",
        )


# Pre-configured managers for common services
KNOWN_SERVICES: Dict[str, Dict] = {
    "openai": {
        "login_url": "https://platform.openai.com/login",
        "dashboard_url": "https://platform.openai.com/api-keys",
        "key_selector": "td.sensitive code",
    },
    "anthropic": {
        "login_url": "https://console.anthropic.com/login",
        "dashboard_url": "https://console.anthropic.com/settings/keys",
        "key_selector": ".api-key-value",
    },
    "github": {
        "login_url": "https://github.com/login",
        "dashboard_url": "https://github.com/settings/tokens",
        "key_selector": ".token-description",
    },
}


def get_manager(service: str) -> APIKeyManager:
    """Get a pre-configured manager for a known service."""
    return APIKeyManager(service)
