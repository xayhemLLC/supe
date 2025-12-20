"""HTTP Request primitive.

ACTION: http.request
Make HTTP requests and capture responses.
"""

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union
import urllib.request
import urllib.error
import urllib.parse
import json


@dataclass
class HttpResponse:
    """Response from an HTTP request."""
    
    status_code: int
    headers: Dict[str, str]
    body: str
    duration_ms: float
    url: str
    method: str
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "status_code": self.status_code,
            "headers": self.headers,
            "body": self.body,
            "duration_ms": self.duration_ms,
            "url": self.url,
            "method": self.method,
            "error": self.error,
        }
    
    def json(self) -> Any:
        """Parse body as JSON."""
        return json.loads(self.body)
    
    @property
    def ok(self) -> bool:
        """Check if response was successful (2xx)."""
        return 200 <= self.status_code < 300


def http_request(
    url: str,
    method: str = "GET",
    headers: Optional[Dict[str, str]] = None,
    body: Optional[Union[str, bytes, Dict]] = None,
    timeout_sec: float = 30,
    follow_redirects: bool = True,
) -> HttpResponse:
    """Make an HTTP request and capture the response.
    
    ACTION: http.request
    
    Args:
        url: URL to request.
        method: HTTP method (GET, POST, PUT, DELETE, etc.).
        headers: Request headers.
        body: Request body. Dicts are JSON-encoded.
        timeout_sec: Request timeout.
        follow_redirects: Whether to follow redirects.
    
    Returns:
        HttpResponse with status, headers, body, and timing.
    """
    headers = headers or {}
    start_time = time.perf_counter()
    
    # Prepare body
    data = None
    if body is not None:
        if isinstance(body, dict):
            data = json.dumps(body).encode("utf-8")
            if "Content-Type" not in headers:
                headers["Content-Type"] = "application/json"
        elif isinstance(body, str):
            data = body.encode("utf-8")
        else:
            data = body
    
    # Create request
    req = urllib.request.Request(
        url,
        data=data,
        headers=headers,
        method=method.upper(),
    )
    
    try:
        with urllib.request.urlopen(req, timeout=timeout_sec) as response:
            response_body = response.read().decode("utf-8", errors="replace")
            response_headers = dict(response.headers)
            status_code = response.status
            
        end_time = time.perf_counter()
        
        return HttpResponse(
            status_code=status_code,
            headers=response_headers,
            body=response_body,
            duration_ms=(end_time - start_time) * 1000,
            url=url,
            method=method.upper(),
        )
        
    except urllib.error.HTTPError as e:
        end_time = time.perf_counter()
        body_content = ""
        try:
            body_content = e.read().decode("utf-8", errors="replace")
        except Exception:
            pass
        
        return HttpResponse(
            status_code=e.code,
            headers=dict(e.headers) if e.headers else {},
            body=body_content,
            duration_ms=(end_time - start_time) * 1000,
            url=url,
            method=method.upper(),
            error=str(e.reason),
        )
        
    except urllib.error.URLError as e:
        end_time = time.perf_counter()
        return HttpResponse(
            status_code=0,
            headers={},
            body="",
            duration_ms=(end_time - start_time) * 1000,
            url=url,
            method=method.upper(),
            error=str(e.reason),
        )
        
    except Exception as e:
        end_time = time.perf_counter()
        return HttpResponse(
            status_code=0,
            headers={},
            body="",
            duration_ms=(end_time - start_time) * 1000,
            url=url,
            method=method.upper(),
            error=str(e),
        )


def http_get(url: str, **kwargs) -> HttpResponse:
    """Convenience function for GET requests."""
    return http_request(url, method="GET", **kwargs)


def http_post(
    url: str,
    body: Optional[Union[str, bytes, Dict]] = None,
    **kwargs
) -> HttpResponse:
    """Convenience function for POST requests."""
    return http_request(url, method="POST", body=body, **kwargs)
