from __future__ import annotations
import requests
from bs4 import BeautifulSoup

def duckduckgo_search(query: str, max_results: int = 5):
    url = "https://html.duckduckgo.com/html/"
    resp = requests.post(url, data={"q": query}, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    results = []
    for a in soup.select("a.result__a")[:max_results]:
        results.append({"title": a.get_text(" ", strip=True), "url": a.get("href", "")})
    return results
