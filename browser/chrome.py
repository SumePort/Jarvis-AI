"""Chrome control using the installed browser and keyboard navigation."""
from __future__ import annotations
import shutil, subprocess, time
from urllib.parse import quote

def chrome_executable() -> str|None:
    return shutil.which("chrome") or shutil.which("chrome.exe")

def open_url(url: str) -> str:
    exe=chrome_executable()
    if exe:
        subprocess.Popen([exe,url],shell=False)
    else:
        subprocess.Popen(["cmd","/c","start","",url],shell=False)
    return f"Opened {url}"

def search(query: str) -> str:
    url="https://www.google.com/search?q="+quote(query)
    return open_url(url)
