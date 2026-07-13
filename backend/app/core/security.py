"""
IP-based rate-limiting using slowapi.
"""

from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from backend.app.core.config import settings

def get_proxy_safe_ip(request: Request) -> str:
    """
    Extract the real client IP address by checking common proxy headers.
    Falls back to slowapi's default client host resolver if no headers are present.
    """
    # Cloudflare client IP
    cf_ip = request.headers.get("cf-connecting-ip")
    if cf_ip:
        return cf_ip.strip()

    # Standard X-Forwarded-For header (comma-separated chain)
    xff = request.headers.get("x-forwarded-for")
    if xff:
        # The client IP is the first address in the chain
        return xff.split(",")[0].strip()

    # X-Real-IP header set by Nginx, Render, or other proxies
    x_real_ip = request.headers.get("x-real-ip")
    if x_real_ip:
        return x_real_ip.strip()

    # Fallback to the socket connection IP
    return get_remote_address(request)


limiter = Limiter(
    key_func=get_proxy_safe_ip,
    default_limits=[settings.rate_limit],
)
