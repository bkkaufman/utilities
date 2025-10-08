import requests
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv
import os

# ---------------------------------------
# CONFIGURATION CONSTANTS
# ---------------------------------------

MAX_RESULTS = 200
PAGE_SIZE = 50           # Scopus API supports up to 50 per request
SEARCH_DAYS = 180

'''
Scopus query for AI-related research papers.

This mirrors the arXiv search scope as closely as possible but uses Scopus syntax.

Scopus Query Fields:
- TITLE: Searches titles only
- ABS:   Searches abstracts
- KEY:   Searches keywords
Use TITLE-ABS-KEY for a comprehensive full-text field match.

The combination below targets modern AI and agentic system concepts
across domains including foundation models, RAG, medical AI, and
multi-agent systems.

That combination will:
- Capture AI and ML applied research across computer science and medicine.
- Include both academic and preprint entries, including SSRN content.
- Broaden beyond arXiv to cover Elsevier-indexed papers.

Scopus query documentation:
https://dev.elsevier.com/documentation/ScopusSearchAPI.wadl
'''

SCOPUS_QUERY = (
    'TITLE-ABS-KEY("foundation model" OR "agentic" OR "multi-agent" OR '
    '"autonomous system" OR "RAG" OR "retrieval" OR '
    '"pharmacovigilance" OR "medical AI")'
)


# ---------------------------------------
# CLASS DEFINITION
# ---------------------------------------

# Load global or local .env
if Path(".env").exists():
    load_dotenv(".env")
else:
    load_dotenv(Path.home() / ".env")


class ScopusSearch:
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.api_key = os.getenv("SCOPUS_API_KEY")
        if not self.api_key:
            raise RuntimeError("Missing SCOPUS_API_KEY in environment.")
        self.base_url = "https://api.elsevier.com/content/search/scopus"

    def fetch_results(self):
        results = []
        headers = {"Accept": "application/json", "X-ELS-APIKey": self.api_key}
        start = 0
        week_ago = datetime.now() - timedelta(days=SEARCH_DAYS)

        while len(results) < MAX_RESULTS:
            params = {"query": SCOPUS_QUERY, "count": PAGE_SIZE, "start": start}
            resp = requests.get(self.base_url, headers=headers, params=params, timeout=30)
            if resp.status_code != 200:
                print(f"Scopus API error: {resp.status_code} {resp.text}")
                break

            data = resp.json().get("search-results", {}).get("entry", [])
            if not data:
                break

            for entry in data:
                try:
                    date_str = entry.get("prism:coverDate")
                    published = datetime.strptime(date_str, "%Y-%m-%d").date() if date_str else None
                    if published and published < week_ago.date():
                        continue
                    results.append({
                        "title": entry.get("dc:title", "N/A"),
                        "authors": entry.get("dc:creator", "N/A"),
                        "published": published,
                        "journal": entry.get("prism:publicationName", "N/A"),
                        "doi": entry.get("prism:doi"),
                        "link": entry.get("prism:url") or entry.get("link", [{}])[0].get("@href"),
                        "summary": entry.get("dc:description", "No abstract available.")
                    })
                except Exception:
                    continue

            start += PAGE_SIZE
            if len(data) < PAGE_SIZE:
                break

        return results
