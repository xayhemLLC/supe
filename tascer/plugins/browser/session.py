"""Browser Session with Cookie Persistence.

Provides a requests-based browser session that:
- Persists cookies between runs
- Mimics real browser headers
- Handles CSRF tokens
- Parses responses with BeautifulSoup
"""

import os
from dataclasses import dataclass, field
from datetime import datetime
from http.cookiejar import LWPCookieJar
from typing import Any, Dict, List, Optional

import requests
from bs4 import BeautifulSoup


@dataclass
class PageResult:
    """Result of fetching a page."""
    url: str
    status_code: int
    soup: Optional[BeautifulSoup] = None
    json_data: Optional[Dict] = None
    text: str = ""
    headers: Dict[str, str] = field(default_factory=dict)
    
    # For detecting challenges
    requires_2fa: bool = False
    requires_captcha: bool = False
    challenge_type: Optional[str] = None
    
    @property
    def ok(self) -> bool:
        return 200 <= self.status_code < 300


class BrowserSession:
    """Persistent browser session with cookie management.
    
    Cookies are saved to disk and restored on subsequent runs,
    allowing for session persistence across script executions.
    
    Example:
        session = BrowserSession("openai")
        
        # Login (only needed once, cookies persist)
        session.login("https://example.com/login", "user", "pass")
        
        # Later - session restored from cookies
        result = session.get("https://example.com/dashboard")
        print(result.soup.title.text)
    """
    
    # Common patterns that indicate 2FA/captcha
    TWO_FA_PATTERNS = [
        "two-factor", "2fa", "verification code", "authenticator",
        "security code", "otp", "one-time password", "verify your identity",
    ]
    
    CAPTCHA_PATTERNS = [
        "captcha", "recaptcha", "hcaptcha", "cloudflare", "challenge",
        "verify you are human", "robot", "automated access",
    ]
    
    def __init__(
        self,
        name: str,
        cookie_dir: str = ".tascer/cookies",
        user_agent: Optional[str] = None,
    ):
        self.name = name
        self.cookie_dir = cookie_dir
        self.cookie_file = os.path.join(cookie_dir, f"{name}.cookies")
        
        # Create session
        self.session = requests.Session()
        
        # Set browser-like headers
        self.session.headers.update({
            'User-Agent': user_agent or (
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/120.0.0.0 Safari/537.36'
            ),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate',  # No brotli - requests handles gzip/deflate
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        # Load existing cookies
        self._load_cookies()
    
    def _load_cookies(self):
        """Load cookies from disk."""
        os.makedirs(self.cookie_dir, exist_ok=True)
        
        if os.path.exists(self.cookie_file):
            try:
                jar = LWPCookieJar(self.cookie_file)
                jar.load(ignore_discard=True, ignore_expires=True)
                self.session.cookies = jar
            except Exception:
                pass  # Start fresh if cookies are corrupted
    
    def save_cookies(self):
        """Save cookies to disk."""
        jar = LWPCookieJar(self.cookie_file)
        for cookie in self.session.cookies:
            jar.set_cookie(cookie)
        jar.save(ignore_discard=True, ignore_expires=True)
    
    def _detect_challenge(self, text: str) -> tuple[bool, bool, Optional[str]]:
        """Detect if page requires 2FA or captcha."""
        text_lower = text.lower()
        
        requires_2fa = any(p in text_lower for p in self.TWO_FA_PATTERNS)
        requires_captcha = any(p in text_lower for p in self.CAPTCHA_PATTERNS)
        
        challenge_type = None
        if requires_2fa:
            challenge_type = "2fa"
        elif requires_captcha:
            challenge_type = "captcha"
        
        return requires_2fa, requires_captcha, challenge_type
    
    def get(
        self,
        url: str,
        params: Optional[Dict] = None,
        **kwargs,
    ) -> PageResult:
        """GET a page and parse with BeautifulSoup."""
        resp = self.session.get(url, params=params, **kwargs)
        self.save_cookies()
        
        requires_2fa, requires_captcha, challenge_type = self._detect_challenge(resp.text)
        
        return PageResult(
            url=url,
            status_code=resp.status_code,
            soup=BeautifulSoup(resp.text, 'html.parser'),
            text=resp.text,
            headers=dict(resp.headers),
            requires_2fa=requires_2fa,
            requires_captcha=requires_captcha,
            challenge_type=challenge_type,
        )
    
    def post(
        self,
        url: str,
        data: Optional[Dict] = None,
        json_data: Optional[Dict] = None,
        **kwargs,
    ) -> PageResult:
        """POST data to a page."""
        resp = self.session.post(url, data=data, json=json_data, **kwargs)
        self.save_cookies()
        
        requires_2fa, requires_captcha, challenge_type = self._detect_challenge(resp.text)
        
        # Try to parse JSON if content-type indicates it
        json_response = None
        if 'application/json' in resp.headers.get('Content-Type', ''):
            try:
                json_response = resp.json()
            except Exception:
                pass
        
        return PageResult(
            url=url,
            status_code=resp.status_code,
            soup=BeautifulSoup(resp.text, 'html.parser'),
            json_data=json_response,
            text=resp.text,
            headers=dict(resp.headers),
            requires_2fa=requires_2fa,
            requires_captcha=requires_captcha,
            challenge_type=challenge_type,
        )
    
    def login(
        self,
        login_url: str,
        username: str,
        password: str,
        username_field: str = "username",
        password_field: str = "password",
        csrf_field: str = "csrf_token",
        extra_fields: Optional[Dict] = None,
    ) -> PageResult:
        """Login to a website.
        
        Automatically handles CSRF tokens if present.
        """
        # Get login page for CSRF token
        login_page = self.get(login_url)
        
        # Build form data
        form_data = {
            username_field: username,
            password_field: password,
        }
        
        # Look for CSRF token
        if login_page.soup:
            csrf_input = login_page.soup.find('input', {'name': csrf_field})
            if csrf_input and csrf_input.get('value'):
                form_data[csrf_field] = csrf_input['value']
            
            # Also check for common alternative names
            for alt_csrf in ['_token', 'authenticity_token', 'csrfmiddlewaretoken']:
                csrf_alt = login_page.soup.find('input', {'name': alt_csrf})
                if csrf_alt and csrf_alt.get('value'):
                    form_data[alt_csrf] = csrf_alt['value']
        
        # Add extra fields
        if extra_fields:
            form_data.update(extra_fields)
        
        # Submit login form
        result = self.post(login_url, data=form_data)
        
        return result
    
    def extract(self, url: str, selector: str) -> List[str]:
        """Fetch page and extract text from elements matching CSS selector."""
        result = self.get(url)
        if not result.soup:
            return []
        
        elements = result.soup.select(selector)
        return [el.get_text(strip=True) for el in elements]
    
    def clear_cookies(self):
        """Clear all cookies for this session."""
        self.session.cookies.clear()
        if os.path.exists(self.cookie_file):
            os.remove(self.cookie_file)
