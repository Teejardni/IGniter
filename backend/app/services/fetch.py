import httpx
from . import parse
from ..core.settings import settings
from typing import Optional
import logging
from urllib.parse import urlparse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ALLOWED_CONTENT_TYPES = {"text/html", "application/xhtml+xml"}

def get_user_agent(url: str) -> str:
    """Determine the best user agent for the given URL."""
    clean_url = urlparse(url).hostname or url
    
    if any(site in clean_url for site in settings.GOOGLEBOT_SITES):
        logger.info(f"Using Googlebot user agent for: {clean_url}")
        return settings.USER_AGENT_GOOGLEBOT
    
    # Check if site is blocked
    if any(site in clean_url for site in settings.BLOCKED_SITES):
        logger.info(f"Using Generic user agent for blocked site: {clean_url}")
        return settings.USER_AGENT_GENERIC
    
    # Default to Twitterbot
    logger.info(f"Using Twitterbot user agent for: {clean_url}")
    return settings.USER_AGENT_TWITTERBOT


async def _fetch_with_client(client: httpx.AsyncClient, url: str) -> str:
    async with client.stream("GET", url) as resp:
        resp.raise_for_status()
        
        ctype = resp.headers.get("content-type", "").split(";")[0].strip()
        if ctype and not any(ctype.startswith(t) for t in ALLOWED_CONTENT_TYPES):
            if "html" not in ctype:
                raise httpx.HTTPError(f"Unsupported content-type: {ctype}")
        
        total = 0
        chunks = []
        async for chunk in resp.aiter_bytes():
            total += len(chunk)
            if total > settings.MAX_BYTES:
                raise httpx.HTTPError("Response too large")
            chunks.append(chunk)
        
        content = b"".join(chunks)
        return content.decode(errors="replace")

async def fetch_html(url: str, retry_with_different_ua: bool = True) -> str:
    user_agent = get_user_agent(url)
    
    headers = {
        "User-Agent": user_agent,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Cache-Control": "max-age=0",
        "Referer": "https://www.google.com/",
    }
    
    limits = httpx.Limits(max_connections=10, max_keepalive_connections=10)
    timeout = httpx.Timeout(settings.HTTP_TIMEOUT_SECONDS)
    
    try:
        async with httpx.AsyncClient(
            headers=headers, 
            follow_redirects=True, 
            limits=limits, 
            timeout=timeout
        ) as client:
            return await _fetch_with_client(client, url)
    
    except (httpx.HTTPStatusError, httpx.HTTPError) as e:
        if retry_with_different_ua and user_agent != settings.USER_AGENT_GOOGLEBOT:
            logger.warning(f"Initial fetch failed: {e}. Retrying with Googlebot UA...")
            headers["User-Agent"] = settings.USER_AGENT_GOOGLEBOT
            
            async with httpx.AsyncClient(
                headers=headers, 
                follow_redirects=True, 
                limits=limits, 
                timeout=timeout
            ) as client:
                return await _fetch_with_client(client, url)
        else:
            raise

async def preview_from_url(url: str) -> dict:
    html = await fetch_html(url)
    processed_html = parse.process_html_content(url, html)
    metadata = parse.extract_metadata(url, processed_html)
    metadata['articleContent'] = processed_html
    return metadata