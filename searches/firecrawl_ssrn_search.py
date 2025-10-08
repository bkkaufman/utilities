import requests
import os
import time
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# ---------------------------------------
# CONFIGURATION CONSTANTS
# ---------------------------------------

MAX_RESULTS = 100
SEARCH_QUERY = "artificial intelligence"
SEARCH_URL = f"https://papers.ssrn.com/sol3/results.cfm?txtKey_Words={SEARCH_QUERY}"

'''
Firecrawl SSRN search configuration.

Firecrawl's API now runs asynchronously:
1. POST to /v1/crawl starts a crawl job and returns an ID + job URL.
2. You then poll that URL until results are ready (status: "completed").

This module handles both automatically and returns extracted page data.

Docs: https://docs.firecrawl.dev/api-reference/crawl
'''

FIRECRAWL_URL = "https://api.firecrawl.dev/v1/crawl"

# ---------------------------------------
# ENVIRONMENT LOADING
# ---------------------------------------

if Path(".env").exists():
    load_dotenv(".env")
else:
    load_dotenv(Path.home() / ".env")

FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY")


# ---------------------------------------
# CLASS DEFINITION
# ---------------------------------------

class FirecrawlSSRNSearch:
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir

    def _poll_job(self, job_url: str, headers: dict, max_wait: int = 120) -> dict:
        """Poll Firecrawl job until completion or timeout."""
        print(f"Polling Firecrawl job: {job_url}")
        start_time = time.time()

        while True:
            resp = requests.get(job_url, headers=headers, timeout=30)
            if resp.status_code != 200:
                print(f"Firecrawl poll error: {resp.status_code}")
                return None

            data = resp.json()
            status = data.get("status") or data.get("data", {}).get("status")
            if data.get("data"):  # job completed
                print("✅ Firecrawl job completed.")
                return data

            elapsed = int(time.time() - start_time)
            if elapsed > max_wait:
                print("⚠️ Firecrawl job timed out (no results within wait window).")
                return None

            print(f"⏳ Still processing... ({elapsed}s)")
            time.sleep(5)

    def fetch_results(self):
        if not FIRECRAWL_API_KEY:
            raise RuntimeError("Missing FIRECRAWL_API_KEY in environment.")

        headers = {
            "Authorization": f"Bearer {FIRECRAWL_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {"url": SEARCH_URL}

        print(f"Fetching SSRN results using Firecrawl for query: {SEARCH_QUERY}")
        resp = requests.post(FIRECRAWL_URL, headers=headers, json=payload, timeout=60)

        if resp.status_code != 200:
            print(f"Firecrawl error: {resp.status_code} {resp.text}")
            return []

        job_url = resp.json().get("url")
        if not job_url:
            print("⚠️ Firecrawl did not return a valid job URL.")
            return []

        # Poll until results are available
        data = self._poll_job(job_url, headers)
        if not data:
            print("⚠️ No data returned from Firecrawl.")
            return []

        pages = data.get("data") or data.get("results") or []
        if isinstance(pages, dict):
            pages = [pages]

        results = []
        for page in pages:
            title = page.get("title") or "N/A"
            url = page.get("url") or SEARCH_URL
            text = page.get("content") or page.get("markdown") or ""
            snippet = text.strip()[:800]

            results.append({
                "title": title,
                "authors": "N/A",
                "published": None,
                "link": url,
                "summary": snippet or "No text extracted."
            })

            print(f"Found: {title}")
            if len(results) >= MAX_RESULTS:
                break

        print(f"Total SSRN papers fetched: {len(results)}")
        return results
