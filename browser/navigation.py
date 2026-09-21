from __future__ import annotations
from .chrome import open_url

def navigate(url: str) -> str:
    if not url.startswith(("http://","https://")):
        url="https://"+url
    return open_url(url)
